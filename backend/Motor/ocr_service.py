import re, io
from pathlib import Path
from typing import Dict
import numpy as np
import cv2

import fitz
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from pdf2image import convert_from_bytes

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.utils import extract_legal_metadata, extract_keywords_from_text, calculate_quality_score


def preprocess_image(img: Image.Image) -> Image.Image:
    """Basic preprocessing (existing method) - kept for compatibility."""
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = img.filter(ImageFilter.MedianFilter(3))
    return img


def preprocess_image_advanced(img: Image.Image) -> Image.Image:
    """
    Advanced image preprocessing for legal documents.
    Includes deskewing, adaptive thresholding, and automatic contrast adjustment.
    """
    # Convert to grayscale
    if img.mode != "L":
        img = img.convert("L")

    # Convert to OpenCV format for advanced processing
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    # Auto-deskew: detect document tilt
    cv_img = _deskew_image(cv_img)

    # Adaptive thresholding (Otsu's method) for better text extraction
    _, cv_img = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Auto-adjust contrast based on histogram
    cv_img = _auto_contrast(cv_img)

    # Denoise
    cv_img = cv2.medianBlur(cv_img, 3)

    # Convert back to PIL Image
    img = Image.fromarray(cv_img)
    return img


def _deskew_image(cv_img: np.ndarray, angle_threshold: float = 2.0) -> np.ndarray:
    """
    Detect document tilt and deskew if angle > threshold.
    Uses edge detection and Hough transform.
    """
    try:
        # Detect edges
        edges = cv2.Canny(cv_img, 50, 150)

        # Hough transform to detect lines
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

        if lines is None or len(lines) == 0:
            return cv_img

        # Extract angles from lines
        angles = [line[0][1] for line in lines]
        median_angle = np.median(angles)

        # Convert from radians to degrees
        angle_deg = np.degrees(median_angle)

        # Normalize angle to [-90, 90]
        if angle_deg > 90:
            angle_deg -= 180

        # Only deskew if angle is significant
        if abs(angle_deg) > angle_threshold:
            h, w = cv_img.shape
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
            deskewed = cv2.warpAffine(
                cv_img,
                rotation_matrix,
                (w, h),
                borderMode=cv2.BORDER_REFLECT_101,
            )
            return deskewed

        return cv_img
    except Exception:
        # If deskewing fails, return original image
        return cv_img


def _auto_contrast(cv_img: np.ndarray) -> np.ndarray:
    """Auto-adjust contrast and brightness based on histogram."""
    try:
        # Calculate histogram
        hist = cv2.calcHist([cv_img], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()

        # Find dark and bright points
        dark_threshold = np.where(np.cumsum(hist) > 0.05)[0]
        bright_threshold = np.where(np.cumsum(hist) > 0.95)[0]

        if len(dark_threshold) == 0 or len(bright_threshold) == 0:
            return cv_img

        dark_val = dark_threshold[0]
        bright_val = bright_threshold[0]

        if bright_val <= dark_val:
            return cv_img

        # Stretch contrast
        cv_img = cv2.convertScaleAbs(cv_img, alpha=255 / (bright_val - dark_val),
                                      beta=-dark_val * 255 / (bright_val - dark_val))
        return cv_img
    except Exception:
        return cv_img


def _extract_words_from_ocr_data(data: Dict, confidence_threshold: int = 30) -> tuple:
    """Extract words and confidence scores from Tesseract output."""
    words, confs = [], []
    for word, conf in zip(data["text"], data["conf"]):
        if str(conf).isdigit():
            conf_int = int(conf)
            if conf_int > confidence_threshold and word.strip():
                words.append(word)
                confs.append(conf_int)
    return words, confs


def ocr_image(image_bytes: bytes, lang: str = "ara+fra", confidence_threshold: int = 50) -> Dict:
    """
    OCR image with confidence-based retry logic.
    Tries advanced preprocessing first, falls back to basic preprocessing if confidence is low.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Upscale small images
        if min(img.size) < 300:
            scale = 300 / min(img.size)
            img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), Image.LANCZOS)

        # First attempt: Advanced preprocessing
        preprocessed = preprocess_image_advanced(img)
        data = pytesseract.image_to_data(
            preprocessed,
            lang=lang,
            config="--psm 3 --oem 3",
            output_type=pytesseract.Output.DICT,
        )
        words, confs = _extract_words_from_ocr_data(data, confidence_threshold=30)
        avg_confidence = round(sum(confs) / len(confs), 1) if confs else 0

        # If confidence is too low, retry with basic preprocessing
        if avg_confidence < 40:
            preprocessed = preprocess_image(img)
            data = pytesseract.image_to_data(
                preprocessed,
                lang=lang,
                config="--psm 3 --oem 3",
                output_type=pytesseract.Output.DICT,
            )
            words_basic, confs_basic = _extract_words_from_ocr_data(data, confidence_threshold=30)
            avg_confidence_basic = round(sum(confs_basic) / len(confs_basic), 1) if confs_basic else 0

            # Use basic result if better
            if avg_confidence_basic > avg_confidence:
                words, confs = words_basic, confs_basic
                avg_confidence = avg_confidence_basic
                method = "tesseract_image_basic"
            else:
                method = "tesseract_image_advanced"
        else:
            method = "tesseract_image_advanced"

        text = " ".join(words)

        # Calculate quality score
        quality_score = calculate_quality_score(
            ocr_confidence=avg_confidence,
            text_length=len(text),
        )

        return {
            "text": text,
            "confidence": avg_confidence,
            "method": method,
            "quality_score": quality_score,
        }
    except Exception as e:
        return {"text": "", "confidence": 0, "method": "error", "error": str(e)}


def ocr_pdf(pdf_bytes: bytes, lang: str = "ara+fra", max_pages: int = None) -> Dict:
    """
    OCR PDF with smart two-tier extraction.
    First tries native text extraction, falls back to OCR on all pages if needed.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()

        # If native text is sufficient, return it
        if len(text.strip()) > 200:
            quality_score = calculate_quality_score(
                ocr_confidence=99,
                text_length=len(text),
            )
            return {
                "text": text.strip(),
                "confidence": 99,
                "method": "native_pdf",
                "quality_score": quality_score,
            }

        # Fallback to OCR - process all pages
        from concurrent.futures import ThreadPoolExecutor, as_completed

        images = convert_from_bytes(pdf_bytes, dpi=200)

        # Limit pages if specified
        if max_pages:
            images = images[:max_pages]

        all_text, all_confs = [], []

        def process_page(img):
            """Process single page with OCR."""
            try:
                preprocessed = preprocess_image_advanced(img)
                data = pytesseract.image_to_data(
                    preprocessed,
                    lang=lang,
                    config="--psm 3 --oem 3",
                    output_type=pytesseract.Output.DICT,
                )
                words, confs = _extract_words_from_ocr_data(data, confidence_threshold=30)
                return " ".join(words), confs
            except Exception:
                return "", []

        # Process pages in parallel for better performance
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_page, img): i for i, img in enumerate(images)}

            for future in as_completed(futures):
                page_text, page_confs = future.result()
                if page_text:
                    all_text.append(page_text)
                if page_confs:
                    all_confs.extend(page_confs)

        full = "\n".join(all_text)

        # Calculate quality score based on overall confidence
        avg_confidence = round(sum(all_confs) / len(all_confs), 1) if all_confs else 0
        quality_score = calculate_quality_score(
            ocr_confidence=avg_confidence,
            text_length=len(full),
        )

        return {
            "text": full.strip(),
            "confidence": avg_confidence,
            "method": "ocr_pdf",
            "quality_score": quality_score,
        }
    except Exception as e:
        return {"text": "", "confidence": 0, "method": "error", "error": str(e)}


PV_PATTERNS = {
    "montant_dh":     [r"(\d[\d\s]*)\s*(?:DH|dirhams?|درهم)", r"amende[^\d]*(\d[\d\s]+)"],
    "article":        [r"[Aa]rticle\s+(\d+)", r"المادة\s+(\d+)"],
    "date":           [r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})"],
    "points_retires": [r"(\d+)\s*points?\s*(?:retirés?|perdus?)", r"سحب\s*(\d+)\s*نقاط?"],
}


def extract_pv_info(text: str) -> Dict:
    info = {}
    for field, patterns in PV_PATTERNS.items():
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                info[field] = re.sub(r"\s+", "", m.group(1))
                break
    return info


def analyze_document(file_bytes: bytes, filename: str) -> Dict:
    """
    Comprehensive document analysis: OCR, metadata extraction, and RAG query generation.
    """
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp"):
        ocr_result = ocr_image(file_bytes)
    elif ext == ".pdf":
        ocr_result = ocr_pdf(file_bytes)
    else:
        return {"error": f"Format non supporté : {ext}"}

    text = ocr_result.get("text", "")
    if ocr_result.get("error"):
        return {"error": ocr_result["error"]}

    # Extract PV information (existing logic)
    pv_info = extract_pv_info(text)

    # Extract legal metadata for better RAG queries
    legal_metadata = extract_legal_metadata(text)
    keywords = extract_keywords_from_text(text, top_n=5)

    # Build RAG query with multiple strategies
    query = _build_rag_query_hierarchical(text, pv_info, legal_metadata, keywords)

    return {
        "filename": filename,
        "ocr": {
            "text": ocr_result.get("text", ""),
            "confidence": ocr_result.get("confidence", 0),
            "method": ocr_result.get("method", "unknown"),
            "quality_score": ocr_result.get("quality_score", 0),
        },
        "pv_info": pv_info,
        "legal_metadata": legal_metadata,
        "keywords": keywords,
        "rag_query": query,
    }


def _build_rag_query_hierarchical(
    text: str,
    pv_info: Dict,
    legal_metadata: Dict,
    keywords: list,
) -> str:
    """
    Build RAG query using hierarchical approach:
    Tier 1: Article + chapter + section if available
    Tier 2: Keywords + type of infraction
    Tier 3: Fallback general query
    """
    parts = []

    # Tier 1: Specific article and section information
    if pv_info.get("article"):
        parts.append(f"Article {pv_info['article']}")

    if legal_metadata.get("chapter"):
        parts.append(legal_metadata["chapter"])

    if legal_metadata.get("section"):
        parts.append(legal_metadata["section"])

    if pv_info.get("montant_dh"):
        parts.append(f"amende {pv_info['montant_dh']} DH")

    if pv_info.get("points_retires"):
        parts.append(f"{pv_info['points_retires']} points retirés")

    if parts:
        query = f"Sanctions et procédures : {', '.join(parts)} du Code de la Route marocain"
        return query

    # Tier 2: Keyword-based search
    if keywords:
        keyword_str = ", ".join(keywords[:3])
        query = f"Infraction {keyword_str} - Sanctions et procédures Code de la Route"
        return query

    # Tier 3: Extract important terms from text
    important_terms = []
    for term in [
        "feu rouge",
        "vitesse",
        "alcool",
        "permis",
        "ceinture",
        "téléphone",
        "stationnement",
        "priorité",
        "dépassement",
    ]:
        if term.lower() in text.lower():
            important_terms.append(term)

    if important_terms:
        query = f"Infraction {', '.join(important_terms[:2])} - Sanctions Code de la Route marocain"
        return query

    # Tier 4: Final fallback
    if len(text) > 300:
        query = f"Infraction routière : {text[:300]} - Code de la Route marocain"
    else:
        query = "Sanctions et procédures infractions Code de la Route marocain"

    return query