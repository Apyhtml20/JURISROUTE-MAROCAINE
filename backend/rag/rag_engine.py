import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os

import faiss
from sentence_transformers import SentenceTransformer

# Import BM25 for keyword search
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("⚠️  rank-bm25 not installed. Hybrid search will use semantic only.")

# ── Config ────────────────────────────────────────────────────
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INDEX_PATH = Path(__file__).parent / "faiss_index.bin"
CHUNKS_PATH = Path(__file__).parent / "chunks.pkl"
BM25_PATH = Path(__file__).parent / "bm25_index.pkl"
TOP_K = 7
SCORE_THRESH = 0.20

# Hybrid search configuration
HYBRID_SEMANTIC_WEIGHT = float(os.getenv("HYBRID_SEMANTIC_WEIGHT", "0.6"))
HYBRID_KEYWORD_WEIGHT = float(os.getenv("HYBRID_KEYWORD_WEIGHT", "0.4"))
RESPONSE_FORMAT = os.getenv("RESPONSE_FORMAT", "concise")  # "concise" or "detailed"

# ── Initialisation ────────────────────────────────────────────
print("⏳ Chargement modèle d'embedding...")
embedder = SentenceTransformer(EMBED_MODEL)
print("✅ Embedder prêt")

index: Optional[faiss.IndexFlatIP] = None
chunks_store: List[Dict] = []
bm25_index: Optional[BM25Okapi] = None


# ─────────────────────────────────────────────────────────────
# 1. Construction de l'index
# ─────────────────────────────────────────────────────────────

def build_bm25_index(chunks: List[Dict]) -> BM25Okapi:
    """Build BM25 index for keyword search."""
    if not BM25_AVAILABLE:
        return None

    # Tokenize chunks: split text into words
    tokenized_chunks = []
    for chunk in chunks:
        # Simple tokenization: split by whitespace and convert to lowercase
        tokens = chunk["text"].lower().split()
        tokenized_chunks.append(tokens)

    # Build BM25 index
    bm25 = BM25Okapi(tokenized_chunks)
    return bm25


def build_index(chunks: List[Dict]) -> None:
    """Build both FAISS semantic and BM25 keyword indices."""
    global index, chunks_store, bm25_index

    if not chunks:
        raise ValueError("Aucun chunk fourni pour construire l'index.")

    print(f"⏳ Vectorisation de {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embeddings = np.array(embeddings, dtype="float32")

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Build BM25 index
    if BM25_AVAILABLE:
        print("⏳ Construction de l'index BM25...")
        bm25_index = build_bm25_index(chunks)
        print("✅ Index BM25 construit")

    chunks_store = chunks

    # Save indices
    INDEX_PATH.parent.mkdir(exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks_store, f)

    if bm25_index:
        with open(BM25_PATH, "wb") as f:
            pickle.dump(bm25_index, f)
        print(f"✅ Indices FAISS et BM25 construits : {index.ntotal} vecteurs → {INDEX_PATH}")
    else:
        print(f"✅ Index FAISS construit : {index.ntotal} vecteurs → {INDEX_PATH}")


def load_index() -> bool:
    """Load both FAISS semantic and BM25 keyword indices."""
    global index, chunks_store, bm25_index

    if INDEX_PATH.exists() and CHUNKS_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        with open(CHUNKS_PATH, "rb") as f:
            chunks_store = pickle.load(f)
        print(f"✅ Index FAISS chargé : {index.ntotal} vecteurs")

        # Load BM25 index if available
        if BM25_PATH.exists():
            try:
                with open(BM25_PATH, "rb") as f:
                    bm25_index = pickle.load(f)
                print("✅ Index BM25 chargé")
            except Exception as e:
                print(f"⚠️  Impossible de charger BM25 : {e}")
                bm25_index = None
        else:
            bm25_index = None

        return True

    print("⚠️  Aucun index trouvé — lance indexer.py d'abord.")
    return False


# ─────────────────────────────────────────────────────────────
# 2. Recherche
# ─────────────────────────────────────────────────────────────

def search(query: str, top_k: int = TOP_K, use_hybrid: bool = True) -> List[Dict]:
    """
    Search with hybrid approach (semantic + keyword) if available.
    Falls back to semantic-only if BM25 unavailable.
    """
    global index, chunks_store, bm25_index

    if index is None:
        if not load_index():
            return []

    if use_hybrid and BM25_AVAILABLE and bm25_index:
        return hybrid_search(query, top_k)
    else:
        return semantic_search(query, top_k)


def semantic_search(query: str, top_k: int = TOP_K) -> List[Dict]:
    """Pure semantic search using FAISS embeddings."""
    global index, chunks_store

    q_vec = embedder.encode([query], normalize_embeddings=True)
    q_vec = np.array(q_vec, dtype="float32")

    scores, indices = index.search(q_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or score < SCORE_THRESH:
            continue
        chunk = chunks_store[idx].copy()
        chunk["semantic_score"] = float(score)
        chunk["keyword_score"] = None
        chunk["combined_score"] = float(score)
        results.append(chunk)

    return results


def hybrid_search(query: str, top_k: int = TOP_K) -> List[Dict]:
    """
    Hybrid search combining semantic and keyword (BM25) approaches.
    Combines scores with configurable weights.
    """
    global index, chunks_store, bm25_index

    # Semantic search
    semantic_results = semantic_search(query, top_k=top_k * 2)

    # BM25 keyword search
    query_tokens = query.lower().split()
    bm25_scores = bm25_index.get_scores(query_tokens)

    # Normalize BM25 scores to [0, 1]
    max_bm25_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
    bm25_scores_norm = [s / max_bm25_score for s in bm25_scores]

    # Combine results
    combined_results = {}

    for result in semantic_results:
        idx = chunks_store.index(result)
        semantic_score = result["semantic_score"]
        keyword_score = bm25_scores_norm[idx]
        combined_score = (
            HYBRID_SEMANTIC_WEIGHT * semantic_score +
            HYBRID_KEYWORD_WEIGHT * keyword_score
        )

        combined_results[idx] = {
            **result,
            "keyword_score": keyword_score,
            "combined_score": combined_score,
        }

    # Add high-scoring BM25 results not in semantic results
    for idx, bm25_score in enumerate(bm25_scores_norm):
        if bm25_score > 0.3 and idx not in combined_results:
            chunk = chunks_store[idx].copy()
            # Get semantic score for completeness
            q_vec = embedder.encode([query], normalize_embeddings=True)
            q_vec = np.array(q_vec, dtype="float32")
            chunk_vec = embedder.encode([chunk["text"]], normalize_embeddings=True)
            chunk_vec = np.array(chunk_vec, dtype="float32")
            semantic_score = float(np.dot(q_vec, chunk_vec.T)[0, 0])

            combined_score = (
                HYBRID_SEMANTIC_WEIGHT * semantic_score +
                HYBRID_KEYWORD_WEIGHT * bm25_score
            )

            combined_results[idx] = {
                **chunk,
                "semantic_score": semantic_score,
                "keyword_score": bm25_score,
                "combined_score": combined_score,
            }

    # Sort by combined score and return top K
    sorted_results = sorted(
        combined_results.values(),
        key=lambda x: x["combined_score"],
        reverse=True,
    )[:top_k]

    return sorted_results


def metadata_filter(
    chunks: List[Dict],
    article: Optional[str] = None,
    chapter: Optional[str] = None,
    keywords: Optional[List[str]] = None,
) -> List[Dict]:
    """Filter chunks by metadata criteria."""
    filtered = chunks

    if article:
        filtered = [c for c in filtered if c.get("article") == article]

    if chapter:
        filtered = [c for c in filtered if c.get("chapter") == chapter]

    if keywords:
        filtered = [
            c for c in filtered
            if any(kw in c.get("keywords", []) for kw in keywords)
        ]

    return filtered


def build_context(query: str, top_k: int = TOP_K, use_hybrid: bool = True) -> Tuple[str, List[Dict]]:
    """Build context from search results with enhanced attribution."""
    results = search(query, top_k, use_hybrid=use_hybrid)

    if not results:
        return "", []

    parts = []
    for i, r in enumerate(results, 1):
        src = r.get("source", "Code de la Route")
        hierarchy = r.get("hierarchy_path", "")

        # Build attribution header with hierarchy and scores
        if r.get("combined_score") is not None:
            score_info = f"| relevance: {r['combined_score']:.2f}"
        elif r.get("semantic_score") is not None:
            score_info = f"| semantic: {r['semantic_score']:.2f}"
        else:
            score_info = f"| score: {r.get('score', 0):.2f}"

        header = f"[Source {i} — {src}"
        if hierarchy and hierarchy != "Document":
            header += f" > {hierarchy}"
        header += f" {score_info}]"

        parts.append(f"{header}\n{r['text']}")

    context = "\n\n---\n\n".join(parts)
    return context, results


# ─────────────────────────────────────────────────────────────
# 3. Prompt builder
# ─────────────────────────────────────────────────────────────

def build_rag_prompt(question: str, context: str, format_style: str = None) -> list:
    """
    Build RAG prompt with configurable response format.

    Args:
        question: User question
        context: RAG context from search
        format_style: "concise" (tables/schemas) or "detailed" (full explanations)
    """
    if format_style is None:
        format_style = RESPONSE_FORMAT

    if format_style == "concise":
        return _build_concise_prompt(question, context)
    else:
        return _build_detailed_prompt(question, context)


def _build_concise_prompt(question: str, context: str) -> list:
    """Build prompt for concise, table-based responses."""
    system = """Tu es JurisRoute, assistant juridique expert du Code de la Route marocain (Loi 52-05).

STYLE DE RÉPONSE — CONCIS ET STRUCTURÉ :
- Réponds UNIQUEMENT avec les informations ESSENTIELLES
- Format TABLEAU ou SCHÉMA, JAMAIS de texte long
- Maximum 2-3 phrases d'explication si nécessaire
- Pas de répétition, pas de bavardage

STRUCTURE DE RÉPONSE :

1. TABLEAU (si plusieurs éléments) :
   | Élément | Valeur |
   |---------|--------|
   | Article | Art. XX |
   | Infraction | ... |
   | Amende | XXX DH |
   | Points | X points |

2. SCHÉMA (pour procédures) :
   Étape 1 → Étape 2 → Étape 3

3. LISTE (si simple) :
   • Point 1
   • Point 2

INFORMATIONS À INCLURE (si applicable) :
- Article du Code de la Route (exact)
- Nom de l'infraction
- Montant de l'amende (DH)
- Points retirés
- Circonstances aggravantes (si pertinent)

RÈGLES :
- Priorise le contexte fourni
- Cite toujours l'article exact
- Réponds dans la langue de la question
- Sois BREF et DIRECT, maximum 5-10 lignes"""

    user = f"""CONTEXTE — CODE DE LA ROUTE MAROCAIN :
{context if context else "Aucun article trouvé."}

QUESTION : {question}

Réponds UNIQUEMENT avec tableau/schéma. Pas d'explication longue."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _build_detailed_prompt(question: str, context: str) -> list:
    """Build prompt for detailed, comprehensive responses."""
    system = """Tu es JurisRoute, assistant juridique expert du Code de la Route marocain (Loi 52-05).

RÈGLES :
- Priorise toujours le contexte fourni s'il contient la réponse
- Si le contexte est incomplet, complète avec tes connaissances générales
- Cite les articles précisément
- Réponds de façon utile et complète
- Mentionne les amendes en DH et points retirés
- Réponds dans la même langue que la question

FORMAT DE RÉPONSE :
- Commence par résumer l'infraction
- Cite l'article concerné
- Détaille les sanctions (amende + points)
- Ajoute des explications pertinentes
- Termine par conseils ou exceptions si applicable"""

    user = f"""CONTEXTE — CODE DE LA ROUTE MAROCAIN :
{context if context else "Aucun article trouvé, utilise tes connaissances générales."}

QUESTION : {question}

Réponds de façon complète et utile au citoyen marocain."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ─────────────────────────────────────────────────────────────
# 4. Utilitaires
# ─────────────────────────────────────────────────────────────

def index_stats() -> Dict:
    """Get statistics about the RAG index."""
    global index, chunks_store, bm25_index

    if index is None:
        load_index()

    if index is None:
        return {"status": "non initialisé"}

    sources = {}
    for c in chunks_store:
        src = c.get("source", "inconnu")
        sources[src] = sources.get(src, 0) + 1

    stats = {
        "status": "actif",
        "total_chunks": index.ntotal,
        "embed_model": EMBED_MODEL,
        "sources": sources,
        "top_k": TOP_K,
        "threshold": SCORE_THRESH,
        "hybrid_search": BM25_AVAILABLE and bm25_index is not None,
        "semantic_weight": HYBRID_SEMANTIC_WEIGHT,
        "keyword_weight": HYBRID_KEYWORD_WEIGHT,
    }

    return stats