import re, json, glob, argparse
from pathlib import Path
from typing import List, Dict
import fitz
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import sys
import pickle

sys.path.insert(0, str(Path(__file__).parent))
from rag_engine import build_index
from utils import extract_legal_metadata, extract_keywords_from_text


def extract_pdf_text(filepath: str) -> str:
    """Extract text from PDF using native extraction or OCR fallback."""
    try:
        doc = fitz.open(filepath)
        text = "".join(page.get_text() for page in doc)
        doc.close()
    except Exception:
        text = ""

    if len(text.strip()) < 200:
        print(f"   OCR sur {Path(filepath).name}...")
        text = ""
        try:
            images = convert_from_path(filepath, dpi=200)
            for i, img in enumerate(images):
                text += pytesseract.image_to_string(img, lang="ara+fra",
                                                    config="--psm 3 --oem 3") + "\n"
        except Exception as e:
            print(f"   OCR échoué : {e}")

    return "\n".join(l.strip() for l in text.split("\n") if l.strip())


def chunk_text(text: str, source: str, size: int = 900, overlap: int = 100) -> List[Dict]:
    """
    Intelligent document chunking that respects article boundaries.
    Preserves hierarchical metadata (chapter, section, article).
    """
    # Smart separators: prioritize article/section boundaries
    article_pattern = r"(?=(?:Article|Art\.|المادة|الفصل)\s+\d+)"
    chapter_pattern = r"(?=(?:Chapitre|Chapter|الفصل|الباب)\s+\d+)"
    section_pattern = r"(?=(?:Section|القسم)\s+[A-Za-z0-9])"

    # First split by chapters/articles to preserve structure
    separators = r"|".join([article_pattern, chapter_pattern, section_pattern, r"\n\n"])
    parts = [p.strip() for p in re.split(separators, text) if len(p.strip()) > 60]

    chunks = []
    current_metadata = {
        "chapter": None,
        "section": None,
        "article": None,
    }

    for part in parts:
        # Update metadata based on part content
        legal_meta = extract_legal_metadata(part)
        if legal_meta.get("chapter"):
            current_metadata["chapter"] = legal_meta["chapter"]
        if legal_meta.get("section"):
            current_metadata["section"] = legal_meta["section"]
        if legal_meta.get("article"):
            current_metadata["article"] = legal_meta["article"]

        # If part is small enough, add as single chunk
        if len(part) <= size:
            chunk = {
                "text": part.strip(),
                "source": source,
                "article": current_metadata["article"],
                "section": current_metadata.get("section"),
                "chapter": current_metadata.get("chapter"),
                "subsection": None,
                "keywords": extract_keywords_from_text(part, top_n=5),
                "hierarchy_path": _build_hierarchy_path(current_metadata),
                "is_header": legal_meta.get("is_header", False),
                "quality_score": 100.0,  # Full text is always high quality
            }
            chunks.append(chunk)
        else:
            # Split large parts while preserving context and metadata
            sub_parts = re.split(r"\n\n+", part)
            current_chunk_text = ""

            for sub_part in sub_parts:
                if len(current_chunk_text) + len(sub_part) < size:
                    current_chunk_text += "\n\n" + sub_part
                else:
                    if current_chunk_text.strip():
                        chunk = {
                            "text": current_chunk_text.strip(),
                            "source": source,
                            "article": current_metadata["article"],
                            "section": current_metadata.get("section"),
                            "chapter": current_metadata.get("chapter"),
                            "subsection": None,
                            "keywords": extract_keywords_from_text(current_chunk_text, top_n=5),
                            "hierarchy_path": _build_hierarchy_path(current_metadata),
                            "is_header": False,
                            "quality_score": 100.0,
                        }
                        chunks.append(chunk)
                    # Start new chunk with overlap
                    current_chunk_text = current_chunk_text[-overlap:] + "\n\n" + sub_part

            if current_chunk_text.strip():
                chunk = {
                    "text": current_chunk_text.strip(),
                    "source": source,
                    "article": current_metadata["article"],
                    "section": current_metadata.get("section"),
                    "chapter": current_metadata.get("chapter"),
                    "subsection": None,
                    "keywords": extract_keywords_from_text(current_chunk_text, top_n=5),
                    "hierarchy_path": _build_hierarchy_path(current_metadata),
                    "is_header": False,
                    "quality_score": 100.0,
                }
                chunks.append(chunk)

    return chunks


def _build_hierarchy_path(metadata: Dict) -> str:
    """Build a human-readable hierarchy path from metadata."""
    path_parts = []
    if metadata.get("chapter"):
        path_parts.append(metadata["chapter"])
    if metadata.get("section"):
        path_parts.append(metadata["section"])
    if metadata.get("article"):
        path_parts.append(metadata["article"])
    return " > ".join(path_parts) if path_parts else "Document"


def chunks_from_json(json_path: str) -> List[Dict]:
    """Load Q&A dataset and convert to chunks with metadata."""
    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    chunks = []
    for item in dataset:
        text = f"Q: {item['instruction']}\nR: {item['output'][:600]}"
        if item.get("input", "").strip():
            text += f"\nContexte: {item['input'][:200]}"

        # Extract article if present
        article_num = item.get("article")
        article = f"Article {article_num}" if article_num else None

        chunk = {
            "text": text,
            "source": "Dataset Q&A JurisRoute",
            "article": article,
            "section": None,
            "chapter": None,
            "subsection": None,
            "keywords": extract_keywords_from_text(text, top_n=3),
            "hierarchy_path": f"Dataset > {article}" if article else "Dataset",
            "is_header": False,
            "quality_score": 95.0,
        }
        chunks.append(chunk)

    print(f"   {len(chunks)} Q&A depuis JSON")
    return chunks


def run_indexing(data_dir: str, json_path: str = None):
    """Run full indexing pipeline: extract → chunk → build indices."""
    all_chunks = []

    pdf_files = glob.glob(f"{data_dir}/*.pdf")
    print(f"\n{len(pdf_files)} PDF(s) trouvé(s)")
    for fpath in pdf_files:
        name = Path(fpath).stem
        print(f"\n→ {name}")
        text = extract_pdf_text(fpath)
        chunks = chunk_text(text, source=name)
        print(f"   {len(text):,} chars → {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if json_path and Path(json_path).exists():
        all_chunks.extend(chunks_from_json(json_path))
    else:
        print(f"⚠️  JSON non trouvé : {json_path}")

    # Deduplicate while preserving metadata
    seen, unique = set(), []
    for c in all_chunks:
        key = c["text"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    print(f"\nTotal chunks uniques : {len(unique)}")
    build_index(unique)
    print("\n🎉 Indexation terminée !")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--json", default=None)
    args = parser.parse_args()
    run_indexing(data_dir=args.data_dir, json_path=args.json)