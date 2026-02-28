import argparse
import sys
from pathlib import Path
from typing import List
import requests


def find_documents(
    directory: Path,
    recursive: bool = False,
    extensions: List[str] = None
) -> List[Path]:

    if not directory.exists():
        raise FileNotFoundError(f"El directorio no existe: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"La ruta no es un directorio: {directory}")
    
    allowed_extensions = extensions or ['pdf', 'txt', 'docx', 'csv', 'xlsx']
    pattern = "**/*" if recursive else "*"
    all_files = directory.glob(pattern)
    
    documents = []
    for file_path in all_files:
        if not file_path.is_file():
            continue
        
        ext = file_path.suffix.lower().lstrip('.')
        if ext in allowed_extensions:
            documents.append(file_path)
    
    return sorted(documents)


def upload_batch(
    files: List[Path],
    api_url: str,
    batch_number: int = None,
    total_batches: int = None
) -> dict:

    batch_info = f" (Lote {batch_number}/{total_batches})" if batch_number else ""
    print(f"\n📤 Enviando {len(files)} archivo(s){batch_info}...")
    
    files_data = []
    for file_path in files:
        try:
            files_data.append(
                ('files', (file_path.name, open(file_path, 'rb'), 'application/octet-stream'))
            )
        except Exception as e:
            print(f"⚠️  Error leyendo {file_path.name}: {e}")
    
    if not files_data:
        return {"error": "No se pudieron leer archivos"}
    
    try:
        response = requests.post(api_url, files=files_data, timeout=300)
        
        # Cerrar todos los archivos abiertos
        for _, (_, file_obj, _) in files_data:
            file_obj.close()
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Error HTTP {response.status_code}: {response.text}"
            }
    
    except requests.exceptions.Timeout:
        return {"error": "Timeout: El servidor tardó demasiado en responder"}
    except requests.exceptions.ConnectionError:
        return {"error": "Error de conexión: No se pudo conectar al servidor"}
    except Exception as e:
        return {"error": f"Error inesperado: {str(e)}"}


def batch_upload_via_api(
    directory: Path,
    api_base_url: str,
    recursive: bool = False,
    extensions: List[str] = None,
    batch_size: int = 5
):

    api_url = f"{api_base_url}/api/documents/upload/batch"
    documents = find_documents(directory, recursive, extensions)
    
    if not documents:
        return
    
    total_successful = 0
    total_failed = 0
    all_errors = []
    
    num_batches = (len(documents) + batch_size - 1) // batch_size
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        result = upload_batch(batch, api_url, batch_num, num_batches)
        
        if "error" in result:
            total_failed += len(batch)
            continue
        
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)
        results = result.get("results", [])
        
        total_successful += successful
        total_failed += failed
        
        if failed > 0:
            for res in results:
                if res.get("status") == "error":
                    error_info = f"{res['filename']}: {res.get('error', 'Unknown error')}"
                    all_errors.append(error_info)
    
    if all_errors:
        for error in all_errors[:10]:
            print(f"  • {error}")
        if len(all_errors) > 10:
            print(f"  ... y {len(all_errors) - 10} errores más")

def main():
    parser = argparse.ArgumentParser(
        description="Carga masiva de documentos vía API REST de ExcaliSearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python batch_upload_api.py ./mi_dataset
  python batch_upload_api.py ./documentos --recursive
  python batch_upload_api.py ./papers --batch-size 10
  python batch_upload_api.py ./data --url http://localhost:8000
  python batch_upload_api.py ./docs --extensions pdf,docx --batch-size 20
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Carpeta que contiene los documentos a cargar"
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="URL base del API de ExcaliSearch (default: http://localhost:8000)"
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
        "-b", "--batch-size",
        type=int,
        default=5,
        help="Número de archivos a enviar por request (default: 5)"
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
        batch_upload_via_api(
            directory=directory,
            api_base_url=args.url.rstrip('/'),
            recursive=args.recursive,
            extensions=extensions,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()
