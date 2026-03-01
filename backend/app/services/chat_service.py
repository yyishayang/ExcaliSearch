"""
Chat service with Ollama LLM integration.
Provides conversational AI capabilities with document context awareness.
"""
import os
from typing import Optional, List, Dict, Generator

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[chat] Warning: ollama not installed. Install with: pip install ollama")

from app.utils.database import get_document
from app.services.extraction_service import extract_text
from app.utils.file_utils import get_file_path

# Configuration
DEFAULT_MODEL = os.environ.get("EXCALISEARCH_LLM_MODEL", "llama3.2:3b")
CHAT_ENABLED = os.environ.get("EXCALISEARCH_CHAT_ENABLED", "1") == "1"
MAX_CONTEXT_LENGTH = 4000
MAX_HISTORY_MESSAGES = 10
RAG_TOP_K = 3  # Number of top documents to retrieve for RAG


def is_chat_available() -> bool:
    """Check if chat service is available."""
    if not OLLAMA_AVAILABLE or not CHAT_ENABLED:
        return False
    
    try:
        models = ollama.list()
        return len(models.get('models', [])) > 0
    except Exception:
        return False


def get_document_context(doc_ids: List[str]) -> str:
    """
    Get context from specified documents for RAG-enhanced chat.
    
    Args:
        doc_ids: List of document IDs to extract context from
        
    Returns:
        Formatted context string with document contents
    """
    if not doc_ids:
        return ""
    
    context_parts = []
    total_length = 0
    
    for doc_id in doc_ids[:3]:  # Limit to 3 documents max
        doc = get_document(doc_id)
        if not doc:
            continue
        
        file_path = get_file_path(doc.filename)
        if not file_path.exists():
            continue
        
        try:
            text, _ = extract_text(file_path, doc.file_type)
            # Truncate if too long
            if total_length + len(text) > MAX_CONTEXT_LENGTH:
                remaining = MAX_CONTEXT_LENGTH - total_length
                text = text[:remaining]
            
            context_parts.append(f"=== Documento: {doc.original_name} ===\n{text}\n")
            total_length += len(text)
            
            if total_length >= MAX_CONTEXT_LENGTH:
                break
        except Exception as e:
            print(f"[chat] Error extracting context from {doc_id}: {e}")
            continue
    
    if not context_parts:
        return ""
    
    return "\n".join(context_parts)


def search_relevant_documents(query: str, top_k: int = RAG_TOP_K) -> tuple[str, List[str]]:
    """
    Search for relevant documents using semantic search for RAG.
    
    Args:
        query: User's query to search for
        top_k: Number of top documents to retrieve
        
    Returns:
        Tuple of (context_string, list_of_doc_ids)
    """
    try:
        from app.services.semantic_service import semantic_search
        
        # Use semantic search to find relevant documents
        results = semantic_search(query, limit=top_k, use_reranking=True)
        
        if not results:
            return "", []
        
        context_parts = []
        doc_ids = []
        total_length = 0
        
        for result in results:
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            doc_ids.append(doc_id)
            doc = get_document(doc_id)
            if not doc:
                continue
            
            # Use snippet from search results (already relevant)
            snippet = result.get("snippet", "")
            
            # If snippet is too short, try to get more context
            if len(snippet) < 100:
                file_path = get_file_path(doc.filename)
                if file_path.exists():
                    try:
                        text, _ = extract_text(file_path, doc.file_type)
                        # Take first relevant chunk
                        snippet = text[:800] if len(text) > 800 else text
                    except Exception:
                        pass
            
            # Check if we have space for this document
            if total_length + len(snippet) > MAX_CONTEXT_LENGTH:
                remaining = MAX_CONTEXT_LENGTH - total_length
                if remaining > 100:  # Only add if we have meaningful space
                    snippet = snippet[:remaining]
                else:
                    break
            
            relevance_score = result.get("score", 0)
            context_parts.append(
                f"=== Documento: {doc.original_name} (Relevancia: {relevance_score:.2f}) ===\n{snippet}\n"
            )
            total_length += len(snippet)
            
            if total_length >= MAX_CONTEXT_LENGTH:
                break
        
        return "\n".join(context_parts), doc_ids
    
    except Exception as e:
        print(f"[chat] Error in semantic search for RAG: {e}")
        return "", []


def chat_completion(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    document_ids: Optional[List[str]] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    stream: bool = False,
    use_rag: bool = True
) -> str | Generator[str, None, None]:
    """
    Generate a chat completion using Ollama.
    
    Args:
        message: User's message
        history: Conversation history [{"role": "user"|"assistant", "content": "..."}]
        document_ids: Optional list of document IDs for context (RAG)
        model: Model name to use (default: llama3.2:3b)
        system_prompt: Custom system prompt
        stream: Whether to stream the response
        use_rag: Whether to use automatic RAG (search relevant documents)
        
    Returns:
        The assistant's response (string or generator if streaming)
    """
    if not OLLAMA_AVAILABLE:
        raise RuntimeError("Ollama is not available. Install with: pip install ollama")
    
    if not CHAT_ENABLED:
        raise RuntimeError("Chat is disabled. Set EXCALISEARCH_CHAT_ENABLED=1 to enable")
    
    model_name = model or DEFAULT_MODEL
    history = history or []
    
    # Build system prompt
    if system_prompt is None:
        system_prompt = """Eres un asistente de IA útil y profesional integrado en ExcaliSearch, un sistema de búsqueda y gestión de documentos. 

Tu función es ayudar a los usuarios a:
- Responder preguntas sobre los documentos que han subido
- Proporcionar resúmenes y análisis de información
- Ayudar con búsquedas y navegación
- Responder preguntas generales de forma clara y concisa

Siempre responde en el mismo idioma que el usuario utiliza (español o inglés).
Si tienes acceso a documentos del contexto, úsalos para dar respuestas más precisas y cita el documento cuando sea relevante.
Si no encuentras información relevante en los documentos proporcionados, indícalo claramente."""
    
    # Add document context (RAG)
    doc_context = ""
    used_doc_ids = []
    
    if document_ids:
        # Use explicitly provided document IDs
        doc_context = get_document_context(document_ids)
        used_doc_ids = document_ids
    elif use_rag:
        # Use automatic RAG: search for relevant documents
        doc_context, used_doc_ids = search_relevant_documents(message)
    
    if doc_context:
        system_prompt += f"\n\n📚 CONTEXTO DE DOCUMENTOS RELEVANTES:\n{doc_context}\n"
        system_prompt += "\nBasa tu respuesta en la información de estos documentos. Cita el nombre del documento cuando uses información específica de él."
    
    # Build messages for Ollama
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (limit to recent messages)
    recent_history = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
    messages.extend(recent_history)
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    try:
        if stream:
            # Return generator for streaming
            return _stream_chat(model_name, messages)
        else:
            # Standard completion
            response = ollama.chat(
                model=model_name,
                messages=messages,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 1000,
                }
            )
            return response['message']['content']
    
    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            raise RuntimeError(f"Model '{model_name}' not found. Pull it with: ollama pull {model_name}")
        raise RuntimeError(f"Chat error: {error_msg}")


def _stream_chat(model_name: str, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """Internal generator for streaming chat responses."""
    stream = ollama.chat(
        model=model_name,
        messages=messages,
        stream=True,
        options={
            'temperature': 0.7,
            'top_p': 0.9,
            'num_predict': 1000,
        }
    )
    
    for chunk in stream:
        if 'message' in chunk and 'content' in chunk['message']:
            yield chunk['message']['content']


def get_available_models() -> List[str]:
    """Get list of available Ollama models."""
    if not OLLAMA_AVAILABLE:
        return []
    
    try:
        models_response = ollama.list()
        return [m['name'] for m in models_response.get('models', [])]
    except Exception:
        return []
