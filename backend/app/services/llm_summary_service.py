# SPDX-FileCopyrightText: 2026 @albabsuarez
# SPDX-FileCopyrightText: 2026 @aslangallery
# SPDX-FileCopyrightText: 2026 @david598Uni
# SPDX-FileCopyrightText: 2026 @yyishayang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from typing import Optional

# Check if ollama is available
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[llm_summary] Warning: ollama not installed. Install with: pip install ollama")


# Configuration
DEFAULT_MODEL = os.environ.get("EXCALISEARCH_LLM_MODEL", "llama3.2:3b")
MAX_INPUT_LENGTH = 4000  # Tokens limit for context
LLM_ENABLED = os.environ.get("EXCALISEARCH_LLM_SUMMARY", "0") == "1"


def is_ollama_available() -> bool:
    """Check if Ollama is installed and a model is available."""
    if not OLLAMA_AVAILABLE:
        return False
    
    try:
        # Try to list models to verify Ollama is running
        models = ollama.list()
        return len(models.get('models', [])) > 0
    except Exception:
        return False


def generate_llm_summary(
    text: str,
    language: str = "spanish",
    max_sentences: int = 5,
    model: Optional[str] = None
) -> Optional[str]:
    """
    Generate an abstractive summary using a local LLM via Ollama.
    
    Args:
        text: The full text to summarize
        language: Language of the text ("spanish" or "english")
        max_sentences: Desired number of sentences in the summary
        model: Model name to use (default: llama3.2:3b)
    
    Returns:
        The generated summary, or None if generation fails
    """
    if not OLLAMA_AVAILABLE:
        print("[llm_summary] Ollama not available, skipping LLM summary")
        return None
    
    if not LLM_ENABLED:
        print("[llm_summary] LLM summary disabled. Set EXCALISEARCH_LLM_SUMMARY=1 to enable")
        return None
    
    if not text or len(text.strip()) < 100:
        return None
    
    # Use specified model or default
    model_name = model or DEFAULT_MODEL
    
    # Truncate text to fit context window
    text_truncated = text[:MAX_INPUT_LENGTH]
    
    # Build prompt based on language
    if language == "english":
        prompt = f"""You are a professional summarizer. Summarize the following document in {max_sentences} clear and concise sentences. Go straight to the summary without any preamble or phrases like "Here is a summary". Just provide the summary directly.

Document:
{text_truncated}

Summary:"""
    else:  # Spanish by default
        prompt = f"""Eres un asistente profesional de resúmenes. Resume el siguiente documento en {max_sentences} oraciones claras y concisas. Ve directo al resumen sin preámbulos ni frases como "Aquí está el resumen" o "A continuación". Solo proporciona el resumen directamente.

Documento:
{text_truncated}

Resumen:"""
    
    try:
        print(f"[llm_summary] Generating summary with {model_name}...")
        
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            options={
                'temperature': 0.3,  # More deterministic
                'top_p': 0.9,
                'num_predict': 250,  # Max tokens in response
                'stop': ['\n\n', 'Documento:', 'Document:'],  # Stop sequences
            }
        )
        
        summary = response['response'].strip()
        
        # Clean up common artifacts and preambles
        cleanup_phrases = [
            'Resumen:', 'Summary:', 'Aquí está el resumen:',
            'Here is a summary:', 'A continuación el resumen:',
            'Aquí te presento un resumen', 'Here is the summary',
            'El resumen es:', 'The summary is:'
        ]
        
        for phrase in cleanup_phrases:
            if summary.lower().startswith(phrase.lower()):
                summary = summary[len(phrase):].strip()
                # Remove any leading colons, dashes, or quotes
                summary = summary.lstrip(':-\'"').strip()
        
        # Remove incomplete sentences at the start (artifacts)
        lines = summary.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:  # Skip very short lines that might be artifacts
                clean_lines.append(line)
        
        summary = ' '.join(clean_lines)
        
        print(f"[llm_summary] Summary generated successfully ({len(summary)} chars)")
        return summary if len(summary) > 50 else None  # Ensure minimum quality
        
    except Exception as e:
        print(f"[llm_summary] Failed to generate summary: {e}")
        return None


def generate_smart_llm_summary(text: str, max_sentences: int = 5) -> Optional[str]:
    """
    Generate summary with automatic language detection.
    
    Tries to detect if the text is primarily Spanish or English,
    then generates a summary in the appropriate language.
    """
    if not text or len(text.strip()) < 100:
        return None
    
    # Simple language detection
    spanish_indicators = ["el", "la", "de", "que", "y", "en", "los", "las", "del", "para"]
    english_indicators = ["the", "and", "of", "to", "in", "a", "is", "that", "for", "it"]
    
    text_lower = text.lower()
    spanish_count = sum(1 for word in spanish_indicators if f" {word} " in text_lower)
    english_count = sum(1 for word in english_indicators if f" {word} " in text_lower)
    
    language = "spanish" if spanish_count > english_count else "english"
    
    return generate_llm_summary(text, language=language, max_sentences=max_sentences)


def get_available_models() -> list[str]:
    """Get list of available Ollama models."""
    if not OLLAMA_AVAILABLE:
        return []
    
    try:
        models_response = ollama.list()
        models = models_response.get('models', [])
        # Handle both 'name' and 'model' keys
        return [model.get('model', model.get('name', '')) for model in models if model]
    except Exception as e:
        print(f"[llm_summary] Failed to list models: {e}")
        return []


def pull_model(model_name: str) -> bool:
    """
    Download a model from Ollama registry.
    
    This is a convenience function to download models programmatically.
    """
    if not OLLAMA_AVAILABLE:
        return False
    
    try:
        print(f"[llm_summary] Downloading model {model_name}...")
        ollama.pull(model_name)
        print(f"[llm_summary] Model {model_name} downloaded successfully")
        return True
    except Exception as e:
        print(f"[llm_summary] Failed to download model: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Test the service
    test_text = """
    La inteligencia artificial está transformando la manera en que trabajamos y vivimos.
    Los modelos de lenguaje pueden generar texto, traducir idiomas y responder preguntas.
    Sin embargo, también presentan desafíos éticos y de seguridad que deben ser abordados.
    Es importante desarrollar estas tecnologías de manera responsable.
    El futuro de la IA depende de cómo la usemos hoy.
    """
    
    print("Available models:", get_available_models())
    
    if is_ollama_available():
        summary = generate_smart_llm_summary(test_text, max_sentences=3)
        print("\nTest summary:")
        print(summary)
    else:
        print("\nOllama not available. Please install and start Ollama.")
