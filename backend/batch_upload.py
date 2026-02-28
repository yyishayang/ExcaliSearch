import asyncio
import sys
from pathlib import Path
from typing import List
import argparse

from app.services.document_service import process_upload
from app.utils.file_utils import is_allowed_file
from app.utils.database import init_db
from app.services.indexing_service import init_index
from app.services.semantic_service import init_semantic_index


class FakeUploadFile:
    """Simula un UploadFile de FastAPI para usar process_upload directamente."""
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.filename = filepath.name
        self._content = None
    
    async def read(self) -> bytes:
        """Lee el contenido del archivo de forma asíncrona."""
        if self._content is None:
            # Leer de forma síncrona pero en contexto async
            self._content = await asyncio.get_event_loop().run_in_executor(
                None, self.filepath.read_bytes
            )
        return self._content
    
    async def seek(self, position: int):
        """Método seek no implementado pero requerido por la interfaz."""
        await asyncio.sleep(0)  # Mantener async


def find_documents(
    directory: Path,
    recursive: bool = False,
    extensions: List[str] = None
) -> List[Path]:
    """
    Encuentra todos los documentos en un directorio.
    
    Args:
        directory: Carpeta a escanear
        recursive: Si True, busca en subcarpetas
        extensions: Lista de extensiones permitidas (ej: ['pdf', 'txt'])
    
    Returns:
        Lista de rutas de archivos encontrados
    """
    if not directory.exists():
        raise FileNotFoundError(f"El directorio no existe: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"La ruta no es un directorio: {directory}")
    
    pattern = "**/*" if recursive else "*"
    all_files = directory.glob(pattern)
    
    documents = []
    for file_path in all_files:
        if not file_path.is_file():
            continue
        
        # Filtrar por extensión si se especificó
        if extensions:
            if file_path.suffix.lower().lstrip('.') not in extensions:
                continue
        else:
            # Usar el validador del sistema
            if not is_allowed_file(file_path.name):
                continue
        
        documents.append(file_path)
    
    return sorted(documents)


async def upload_single_document(file_path: Path, index: int, total: int) -> dict:
    """
    Procesa y sube un único documento.
    
    Returns:
        Dict con resultado del procesamiento
    """
    print(f"[{index}/{total}] Procesando: {file_path.name}")
    
    try:
        fake_file = FakeUploadFile(file_path)
        doc = await process_upload(fake_file)
        
        return {
            "status": "success",
            "file": file_path.name,
            "doc_id": doc.id,
            "word_count": doc.word_count,
        }
    except Exception as e:
        return {
            "status": "error",
            "file": file_path.name,
            "error": str(e),
        }


async def batch_upload(
    directory: Path,
    recursive: bool = False,
    extensions: List[str] = None,
    max_concurrent: int = 3
):
    """
    Procesa una carpeta completa de documentos.
    
    Args:
        directory: Carpeta con los documentos
        recursive: Procesar subcarpetas
        extensions: Extensiones permitidas
        max_concurrent: Número máximo de documentos a procesar simultáneamente
    """
    # Inicializar sistemas
    print("🔧 Inicializando índices...")
    init_db()
    init_index()
    try:
        init_semantic_index()
        print("✅ Índice semántico inicializado")
    except Exception as e:
        print(f"⚠️  Advertencia semántica: {e}")
    
    # Encontrar documentos
    print(f"\n📂 Escaneando directorio: {directory}")
    documents = find_documents(directory, recursive, extensions)
    
    if not documents:
        print("❌ No se encontraron documentos que procesar")
        return
    
    print(f"📄 Encontrados {len(documents)} documentos\n")
    
    # Procesar documentos
    results = []
    total = len(documents)
    
    # Procesar en lotes para no sobrecargar el sistema
    for i in range(0, total, max_concurrent):
        batch = documents[i:i + max_concurrent]
        tasks = [
            upload_single_document(doc, idx + i + 1, total)
            for idx, doc in enumerate(batch)
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE CARGA MASIVA")
    print("="*60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    print(f"\n✅ Exitosos: {len(successful)}/{total}")
    print(f"❌ Fallidos: {len(failed)}/{total}")
    
    if successful:
        total_words = sum(r["word_count"] for r in successful)
        print(f"📝 Total de palabras indexadas: {total_words:,}")
    
    if failed:
        print("\n⚠️  ERRORES:")
        for result in failed:
            print(f"  - {result['file']}: {result['error']}")
    
    print("\n✅ Proceso completado")


def main():
    parser = argparse.ArgumentParser(
        description="Carga masiva de documentos para ExcaliSearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python batch_upload.py ./mi_dataset
  python batch_upload.py ./documentos --recursive
  python batch_upload.py ./papers --extensions pdf,docx
  python batch_upload.py ./data --recursive --extensions txt,pdf --concurrent 5
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Carpeta que contiene los documentos a cargar"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Buscar documentos en subcarpetas recursivamente"
    )
    
    parser.add_argument(
        "-e", "--extensions",
        type=str,
        help="Extensiones permitidas separadas por coma (ej: pdf,txt,docx)"
    )
    
    parser.add_argument(
        "-c", "--concurrent",
        type=int,
        default=3,
        help="Número máximo de documentos a procesar simultáneamente (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Parsear extensiones
    extensions = None
    if args.extensions:
        extensions = [ext.strip().lower() for ext in args.extensions.split(",")]
    
    # Convertir a Path
    directory = Path(args.directory)
    
    # Ejecutar carga
    try:
        asyncio.run(batch_upload(
            directory=directory,
            recursive=args.recursive,
            extensions=extensions,
            max_concurrent=args.concurrent
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
