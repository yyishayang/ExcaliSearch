"""
Chat API endpoints for conversational AI with Ollama.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.chat_service import (
    is_chat_available,
    chat_completion,
    get_available_models
)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    message: str = Field(..., min_length=1, description="User's message")
    history: List[ChatMessage] = Field(
        default=[],
        description="Conversation history"
    )
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional document IDs for RAG context"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (default: llama3.2:3b)"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )
    use_rag: bool = Field(
        default=True,
        description="Use automatic RAG (search relevant documents)"
    )


class ChatResponse(BaseModel):
    """Response from chat completion."""
    response: str = Field(..., description="Assistant's response")
    model: str = Field(..., description="Model used")


class ChatStatusResponse(BaseModel):
    """Chat service status."""
    available: bool = Field(..., description="Whether chat is available")
    models: List[str] = Field(..., description="Available models")


@router.get("/status", response_model=ChatStatusResponse)
async def get_chat_status():
    """
    Check if chat service is available and list models.
    """
    available = is_chat_available()
    models = get_available_models() if available else []
    
    return ChatStatusResponse(
        available=available,
        models=models
    )


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message and get a response.
    
    Supports:
    - Conversation history
    - RAG with document context (automatic or manual)
    - Multiple models
    - Streaming (if stream=True)
    """
    if not is_chat_available():
        raise HTTPException(
            status_code=503,
            detail="Chat service is not available. Make sure Ollama is running and a model is installed."
        )
    
    # Convert Pydantic models to dicts for service layer
    history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    try:
        if request.stream:
            # Return streaming response
            async def generate():
                try:
                    generator = chat_completion(
                        message=request.message,
                        history=history_dicts,
                        document_ids=request.document_ids,
                        model=request.model,
                        stream=True,
                        use_rag=request.use_rag
                    )
                    for chunk in generator:
                        yield chunk
                except Exception as e:
                    yield f"\n\n[Error: {str(e)}]"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain"
            )
        else:
            # Standard completion
            response_text = chat_completion(
                message=request.message,
                history=history_dicts,
                document_ids=request.document_ids,
                model=request.model,
                stream=False,
                use_rag=request.use_rag
            )
            
            return ChatResponse(
                response=response_text,
                model=request.model or "llama3.2:3b"
            )
    
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )
