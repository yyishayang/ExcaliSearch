<!--
SPDX-FileCopyrightText: 2026 @albabsuarez
SPDX-FileCopyrightText: 2026 @aslangallery
SPDX-FileCopyrightText: 2026 @david598Uni
SPDX-FileCopyrightText: 2026 @yyishayang

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# ExcaliSearch

## Propósito
ExcaliSearch es una plataforma de búsqueda y gestión de documentos basada en IA. Permite a los usuarios subir, analizar, indexar y buscar dentro de diversos formatos de documentos (PDF, TXT, DOCX, XLSX, CSV). Utilizando tecnologías de vanguardia como **Whoosh** para búsquedas léxicas, **ChromaDB** para búsquedas semánticas y **Ollama (LLMs)** para resumen automático y chat interactivo (RAG), la aplicación resuelve el problema de la fragmentación de la información, permitiendo extraer conocimiento de los documentos de forma eficiente y sumamente precisa.

## Características
- **Soporte Multiformato**: Carga y extracción de texto de documentos PDF, TXT, DOCX, XLSX y CSV.
- **Búsqueda Híbrida**: Búsqueda directa por palabras clave (Whoosh) complementada con búsqueda semántica vectorial (ChromaDB + SentenceTransformers).
- **OCR Integrado**: Extracción de texto a partir de imágenes de documentos PDF utilizando Tesseract OCR.
- **Resúmenes Inteligentes**: Generación automática de resúmenes utilizando modelos locales de lenguaje (Ollama) o métodos de procesamiento de lenguaje natural deductivo (Sumy/NLTK).
- **Chat Contextual (RAG)**: Chat conversacional directo con el contenido de los documentos utilizando la tecnología de Generación Aumentada por Recuperación (RAG).
- **Interfaz Moderna**: Interfaz gráfica ágil, limpia y reactiva construida con React y Vite.
- **Gestión Avanzada**: Filtrado por tipo de archivo, visualización instantánea de fragmentos relevantes (snippets) y limpieza automática de archivos huérfanos del sistema.

## Prerrequisitos y Compatibilidad
La aplicación es compatible con Windows, macOS y entornos basados en Linux. Las instrucciones de OCR en el código están nativamente preparadas para resolver el *path* en Windows.

- **Python**: Versión 3.10 o superior (Requerido para iniciar el API del backend).
- **Node.js**: Versión v18 o superior (Requerido para ejecutar o empaquetar el frontend).
- **Tesseract OCR (Opcional, para análisis de imágenes en PDF)**: 
  - **Windows**: Descargar el instalador desde [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Idealmente, debe instalarse en la ruta `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- **Ollama (Opcional, para resúmenes generativos y chat RAG)**:
  - Descargar e instalar desde el sitio oficial [Ollama.com](https://ollama.com/).
  - Una vez instalado, abrir una consola y descargar el modelo por defecto sugerido: `ollama pull llama3.2:3b`.

## Configuración y Variables de Entorno
El backend provee varias variables de entorno para activar características de evaluación pesada o especificar qué modelos de IA utilizar.

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `EXCALISEARCH_OCR` | `0` | Establecer con valor `1` para habilitar Tesseract OCR en la extracción integral de PDFs con imágenes. |
| `EXCALISEARCH_LLM_SUMMARY` | `0` | Establecer con valor `1` para habilitar los resúmenes de documentos utilizando el modelo LLM de Ollama. |
| `EXCALISEARCH_CHAT_ENABLED` | `1` | Establecer a `1` para habilitar el panel de chat interactivo (RAG). |
| `EXCALISEARCH_LLM_MODEL` | `llama3.2:3b`| Nombre del modelo de Ollama que el sistema instanciará para consultas y resúmenes. |

## Instalación

1. **Clonar el Repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd ExcaliSearch
   ```

2. **Preparar el Backend (Lógica y Base de Datos)**
   Abrir un terminal/consola y posicionarse en la carpeta `backend`:
   ```bash
   cd backend
   python -m venv venv
   
   # Activar el entorno virtual:
   # En Windows: 
   venv\Scripts\activate
   # En macOS/Linux: 
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Preparar el Frontend (Interfaz Visual)**
   Abrir una **segunda** terminal/consola y dirigirse a la carpeta `frontend`:
   ```bash
   cd frontend
   npm install
   ```

## Ejemplos de Uso y Ejecución

Para ejecutar el entorno completo, se deben lanzar en terminales diferentes el backend, el frontend y Ollama:

**Terminal 1: Iniciar el servidor Backend**
Desde la carpeta `backend`, asegurándose que el entorno virtual esté activo. De forma opcional, definimos las variables de entorno:
```bash
# Ejemplo en Windows (PowerShell):
$env:EXCALISEARCH_OCR="1"
$env:EXCALISEARCH_LLM_SUMMARY="1"

uvicorn app.main:app --reload
```
El servidor backend quedará escuchando de forma local en `http://localhost:8000`.

**Terminal 2: Iniciar la interfaz Frontend**
Desde la carpeta `frontend`:
```bash
npm run dev
```
La aplicación web será visible navegando a `http://localhost:5173`. A través de ella, podrás cargar cualquier documento de prueba y buscar frases o hacer preguntas al Chat.

**Terminal 3: Iniciar Ollama**
Desde cualquier carpeta:
```bash
ollama run llama3.2:3b
```