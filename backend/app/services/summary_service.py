import os
from pathlib import Path
from typing import Optional, Literal

# Configure NLTK data path to avoid Windows user profile issues
_NLTK_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "nltk_data"
_NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)

import nltk
nltk.data.path.insert(0, str(_NLTK_DATA_DIR))

# Download required NLTK data on first import
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("[summary] Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', download_dir=str(_NLTK_DATA_DIR), quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("[summary] Downloading NLTK stopwords...")
    nltk.download('stopwords', download_dir=str(_NLTK_DATA_DIR), quiet=True)


def generate_preview(text: str, max_len: int = 300) -> str:
    """
    Generate a short preview from the extracted text.
    Returns the first max_len characters, trimmed to the last complete word.
    """
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]
    # Try to break at the last space
    last_space = truncated.rfind(" ")
    if last_space > max_len * 0.5:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "…"


def generate_summary(
    text: str,
    sentence_count: int = 5,
    algorithm: str = "lsa",
    language: str = "spanish"
) -> Optional[str]:
    """
    Generate an automatic extractive summary of the text.
    
    Args:
        text: The full text to summarize
        sentence_count: Number of sentences in the summary (default: 5)
        algorithm: Summarization algorithm - "lsa", "lexrank", or "textrank" (default: "lsa")
        language: Language for stopwords - "spanish" or "english" (default: "spanish")
    
    Returns:
        The generated summary as a string, or None if summarization fails
    """
    if not text or len(text.strip()) < 100:
        # Text too short to summarize
        return None
    
    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.summarizers.lex_rank import LexRankSummarizer
        from sumy.summarizers.text_rank import TextRankSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words
        
        # Parse the text
        parser = PlaintextParser.from_string(text, Tokenizer(language))
        
        # Choose summarizer based on algorithm
        stemmer = Stemmer(language)
        if algorithm == "lexrank":
            summarizer = LexRankSummarizer(stemmer)
        elif algorithm == "textrank":
            summarizer = TextRankSummarizer(stemmer)
        else:  # default to LSA
            summarizer = LsaSummarizer(stemmer)
        
        summarizer.stop_words = get_stop_words(language)
        
        # Generate summary
        summary_sentences = summarizer(parser.document, sentence_count)
        
        # Combine sentences into a single string
        summary = " ".join(str(sentence) for sentence in summary_sentences)
        
        return summary if summary else None
        
    except Exception as e:
        print(f"[summary] Failed to generate summary: {e}")
        return None


def generate_smart_summary(
    text: str,
    max_sentences: int = 5,
    method: Literal["auto", "extractive", "llm"] = "auto"
) -> str:
    """
    Generate a summary with automatic language detection and fallback.
    
    Args:
        text: The text to summarize
        max_sentences: Number of sentences in the summary
        method: Summarization method:
            - "auto": Use LLM if available and enabled, otherwise extractive
            - "extractive": Always use sumy (fast, works offline)
            - "llm": Always use LLM (better quality, requires Ollama)
    
    Returns:
        Generated summary string, or preview as fallback
    """
    if not text or len(text.strip()) < 100:
        # Too short, just return preview
        return generate_preview(text, max_len=300)
    
    # Simple language detection based on common words
    spanish_indicators = ["el", "la", "de", "que", "y", "en", "los", "las", "del", "para"]
    english_indicators = ["the", "and", "of", "to", "in", "a", "is", "that", "for", "it"]
    
    text_lower = text.lower()
    spanish_count = sum(1 for word in spanish_indicators if f" {word} " in text_lower)
    english_count = sum(1 for word in english_indicators if f" {word} " in text_lower)
    
    language = "spanish" if spanish_count > english_count else "english"
    
    # Try LLM method if requested or auto-enabled
    if method in ("auto", "llm"):
        try:
            from app.services.llm_summary_service import (
                generate_llm_summary,
                is_ollama_available,
                LLM_ENABLED
            )
            
            # Use LLM if explicitly requested or if auto and enabled
            should_use_llm = (
                method == "llm" or
                (method == "auto" and LLM_ENABLED and is_ollama_available())
            )
            
            if should_use_llm:
                llm_summary = generate_llm_summary(
                    text=text,
                    language=language,
                    max_sentences=max_sentences
                )
                
                if llm_summary:
                    print(f"[summary] Using LLM-generated summary")
                    return llm_summary
                elif method == "llm":
                    # LLM was explicitly requested but failed
                    print("[summary] LLM summary failed, falling back to extractive")
        
        except ImportError:
            if method == "llm":
                print("[summary] LLM service not available, falling back to extractive")
    
    # Use extractive method (default or fallback)
    summary = generate_summary(
        text,
        sentence_count=max_sentences,
        algorithm="lsa",
        language=language
    )
    
    # Fallback to preview if summary generation failed
    if not summary:
        return generate_preview(text, max_len=500)
    
    return summary
