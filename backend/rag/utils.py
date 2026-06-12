"""
Utility functions for RAG and OCR integration.
Supports legal document processing with hierarchical metadata extraction.
"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path


# ────────────────────────────────────────────────────────────────
# Legal Document Metadata Extraction
# ────────────────────────────────────────────────────────────────

LEGAL_KEYWORDS = {
    "obligations": ["obligation", "doit", "must", "يجب", "ملزم"],
    "sanctions": ["amende", "fine", "sanction", "pénalité", "عقوبة", "غرامة"],
    "procedures": ["procédure", "procedure", "processus", "étapes", "إجراء"],
    "exceptions": ["sauf", "except", "excepté", "إلا", "ما لم يكن"],
    "infractions": ["infraction", "violation", "breach", "مخالفة", "جريمة"],
    "points": ["point", "points", "retrait", "suspension", "نقاط"],
}

ARTICLE_PATTERN = r"(?:Article|Art\.|المادة|الفصل)\s+(\d+)"
CHAPTER_PATTERN = r"(?:Chapitre|Chapter|الفصل|الباب)\s+(\d+)"
SECTION_PATTERN = r"(?:Section|القسم)\s+([A-Za-z]|\d+)"


def extract_legal_metadata(text: str) -> Dict:
    """
    Extract legal document structure and metadata from text.

    Returns:
        Dict with keys: article, chapter, section, subsection, keywords, hierarchy_path
    """
    metadata = {
        "article": None,
        "chapter": None,
        "section": None,
        "subsection": None,
        "keywords": [],
        "hierarchy_path": "",
        "is_header": False,
    }

    # Extract article number
    article_match = re.search(ARTICLE_PATTERN, text, re.IGNORECASE)
    if article_match:
        metadata["article"] = f"Article {article_match.group(1)}"

    # Extract chapter number
    chapter_match = re.search(CHAPTER_PATTERN, text, re.IGNORECASE)
    if chapter_match:
        metadata["chapter"] = f"Chapter {chapter_match.group(1)}"

    # Extract section
    section_match = re.search(SECTION_PATTERN, text, re.IGNORECASE)
    if section_match:
        metadata["section"] = f"Section {section_match.group(1)}"

    # Extract keywords
    text_lower = text.lower()
    found_keywords = set()
    for category, keywords in LEGAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.add(keyword)
    metadata["keywords"] = list(found_keywords)

    # Build hierarchy path
    path_parts = []
    if metadata["chapter"]:
        path_parts.append(metadata["chapter"])
    if metadata["section"]:
        path_parts.append(metadata["section"])
    if metadata["article"]:
        path_parts.append(metadata["article"])
    if path_parts:
        metadata["hierarchy_path"] = " > ".join(path_parts)

    # Detect if this is a header (short text with article/chapter markers)
    if len(text.strip()) < 150 and (article_match or chapter_match or section_match):
        metadata["is_header"] = True

    return metadata


def normalize_score(score: float, score_type: str = "semantic") -> float:
    """
    Normalize different types of scores to [0, 1] range.

    Args:
        score: Raw score value
        score_type: "semantic" (faiss), "bm25", "confidence", or "quality"

    Returns:
        Normalized score in [0, 1]
    """
    if score_type == "semantic":
        # FAISS IP scores on normalized vectors range roughly [0, 1.1] for cosine
        return min(1.0, max(0.0, score))

    elif score_type == "bm25":
        # BM25 scores can be large, apply log scaling
        if score <= 0:
            return 0.0
        # Map to roughly [0, 1] using log scale
        return min(1.0, 0.2 * (1 + __import__('math').log(score + 1)))

    elif score_type == "confidence":
        # Confidence scores are typically [0, 100]
        return max(0.0, min(1.0, score / 100.0))

    elif score_type == "quality":
        # Quality scores [0, 100]
        return max(0.0, min(1.0, score / 100.0))

    return max(0.0, min(1.0, score))


def calculate_quality_score(
    ocr_confidence: float,
    text_length: int,
    language_score: float = 1.0,
    metadata_completeness: float = 1.0,
) -> float:
    """
    Calculate overall quality score for OCR'd text.

    Args:
        ocr_confidence: OCR engine confidence [0, 100]
        text_length: Length of extracted text
        language_score: Detected language confidence [0, 1]
        metadata_completeness: Completeness of metadata [0, 1]

    Returns:
        Quality score [0, 100]
    """
    # Base score from OCR confidence
    score = ocr_confidence * 0.5

    # Bonus for sufficient text extraction
    if text_length > 500:
        score += 20
    elif text_length > 200:
        score += 10

    # Apply language and metadata factors
    score *= language_score
    score *= (0.8 + metadata_completeness * 0.2)  # Small bonus for metadata

    return min(100.0, max(0.0, score))


def extract_keywords_from_text(text: str, top_n: int = 10) -> List[str]:
    """
    Extract legal keywords from text.
    Simple keyword extraction based on domain terms.

    Returns:
        List of extracted keywords, sorted by frequency
    """
    text_lower = text.lower()
    keyword_freq = {}

    # Extract from LEGAL_KEYWORDS categories
    for category, keywords in LEGAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

    # Also extract article/chapter numbers
    article_nums = re.findall(r"(?:Article|المادة)\s+(\d+)", text, re.IGNORECASE)
    for num in article_nums[:5]:  # Limit to top 5
        keyword_freq[f"Article {num}"] = keyword_freq.get(f"Article {num}", 0) + 2

    # Sort by frequency and return top N
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, freq in sorted_keywords[:top_n]]


# ────────────────────────────────────────────────────────────────
# Document Quality Assessment
# ────────────────────────────────────────────────────────────────

def estimate_layout_quality(text: str) -> float:
    """
    Estimate if document layout is preserved (0-1).
    Based on presence of structured elements like newlines, indentation.
    """
    lines = text.split("\n")
    if len(lines) < 5:
        return 0.3  # Likely poor layout

    # Check for consistent structure
    non_empty_lines = [l for l in lines if l.strip()]
    structure_score = min(1.0, len(non_empty_lines) / len(lines))

    return structure_score


def is_bilingual_text(text: str) -> Tuple[bool, str, float]:
    """
    Detect if text contains both Arabic and French/Latin.

    Returns:
        (is_bilingual, primary_language, arabic_ratio)
    """
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))

    total_chars = arabic_chars + latin_chars
    if total_chars == 0:
        return False, "unknown", 0.0

    arabic_ratio = arabic_chars / total_chars
    is_bilingual = 0.2 < arabic_ratio < 0.8

    primary = "Arabic" if arabic_ratio > 0.5 else "French"

    return is_bilingual, primary, arabic_ratio


# ────────────────────────────────────────────────────────────────
# Text Cleaning & Normalization
# ────────────────────────────────────────────────────────────────

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace: collapse multiple spaces, fix line breaks."""
    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)
    # Replace multiple newlines with double newline
    text = re.sub(r"\n\n+", "\n\n", text)
    # Strip leading/trailing whitespace
    return text.strip()


def clean_ocr_artifacts(text: str) -> str:
    """Remove common OCR artifacts and cleaning."""
    # Remove isolated special characters
    text = re.sub(r"[^\w\s\-.,!?()«»،؛:\n]", "", text)
    # Fix common OCR mistakes (example: 'O' instead of '0')
    # This is context-dependent, so keep minimal
    return normalize_whitespace(text)
