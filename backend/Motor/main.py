import os, sys, time, logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.rag_engine    import build_context, build_rag_prompt, index_stats, load_index
from Motor.ocr_service import analyze_document

MODEL_BACKEND  = os.getenv("MODEL_BACKEND",  "groq")
OLLAMA_URL     = os.getenv("OLLAMA_URL",     "http://localhost:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL",   "qwen2.5:3b")
QWEN2_MODEL_ID = os.getenv("QWEN2_MODEL_ID", "abdoulba/jurisroute-qwen2-lora")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY",   "")
GROQ_MODEL     = os.getenv("GROQ_MODEL",     "llama-3.1-8b-instant")

MAX_TOKENS_ASK   = int(os.getenv("MAX_TOKENS_ASK",   "600"))
MAX_TOKENS_IMAGE = int(os.getenv("MAX_TOKENS_IMAGE",  "600"))
MAX_TOKENS_PDF   = int(os.getenv("MAX_TOKENS_PDF",    "800"))

USE_HYBRID_SEARCH      = os.getenv("USE_HYBRID_SEARCH", "true").lower() == "true"
HYBRID_SEMANTIC_WEIGHT = float(os.getenv("HYBRID_SEMANTIC_WEIGHT", "0.6"))
HYBRID_KEYWORD_WEIGHT  = float(os.getenv("HYBRID_KEYWORD_WEIGHT",  "0.4"))
RESPONSE_FORMAT        = os.getenv("RESPONSE_FORMAT", "concise")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("jurisroute")

model = None; tokenizer = None; model_ready = False


# ── Qwen2 loader (optional backend) ──────────────────────────

def load_qwen2():
    global model, tokenizer, model_ready
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(QWEN2_MODEL_ID, trust_remote_code=True)
        tokenizer.pad_token    = tokenizer.eos_token
        tokenizer.padding_side = "right"
        model = AutoModelForCausalLM.from_pretrained(
            QWEN2_MODEL_ID,
            quantization_config=bnb,
            device_map="auto",
            trust_remote_code=True,
        )
        model.config.use_cache = True
        model_ready = True
        log.info("✅ Qwen2 chargé !")
    except Exception as e:
        log.error(f"❌ Qwen2 : {e}")


# ── Lifespan (remplace @on_event deprecated) ─────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"🚀 JurisRoute API — backend : {MODEL_BACKEND.upper()}")
    load_index()

    if MODEL_BACKEND == "qwen2":
        load_qwen2()

    elif MODEL_BACKEND == "groq":
        if not GROQ_API_KEY:
            log.warning("⚠️  GROQ_API_KEY manquante dans .env !")
        else:
            log.info(f"✅ Groq configuré — modèle : {GROQ_MODEL}")

    else:  # ollama
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{OLLAMA_URL}/api/tags")
                models = [m["name"] for m in r.json().get("models", [])]
                if any(OLLAMA_MODEL in m for m in models):
                    log.info(f"✅ Ollama OK — {OLLAMA_MODEL} disponible")
                else:
                    log.warning(f"⚠️  Lance : ollama pull {OLLAMA_MODEL}")
            log.info("⏳ Warm-up du modèle Ollama...")
            async with httpx.AsyncClient(timeout=60) as c:
                await c.post(f"{OLLAMA_URL}/api/chat", json={
                    "model":      OLLAMA_MODEL,
                    "messages":   [{"role": "user", "content": "Bonjour"}],
                    "stream":     False,
                    "keep_alive": -1,
                    "options":    {"num_predict": 5},
                })
            log.info("✅ Modèle Ollama chargé en mémoire (keep_alive=-1)")
        except Exception as e:
            log.warning(f"⚠️  Ollama non joignable : {e} — lance : ollama serve")

    yield  # app runs


# ── App ───────────────────────────────────────────────────────

app = FastAPI(title="JurisRoute MA API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Schémas ──────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    use_rag:  bool = True

class JurisResponse(BaseModel):
    question:              str
    answer:                str
    sources:               list  = []
    pv_info:               dict  = {}
    legal_metadata:        dict  = {}
    ocr_metadata:          dict  = {}
    model_used:            str   = ""
    processing_time_s:     float = 0.0
    search_method:         str   = "hybrid"


# ── Génération ───────────────────────────────────────────────

async def generate_groq(messages: List[dict], max_tokens: int = 150) -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       GROQ_MODEL,
                    "messages":    messages,
                    "max_tokens":  max_tokens,
                    "temperature": 0.3,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except httpx.TimeoutException:
        return "❌ Timeout Groq — réessayez."
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "❌ Limite Groq atteinte (30 req/min). Réessayez dans 1 minute."
        return f"❌ Erreur Groq HTTP {e.response.status_code} : {e.response.text}"
    except Exception as e:
        return f"❌ Erreur Groq : {e}"


async def generate_ollama(messages: List[dict], max_tokens: int = 150) -> str:
    try:
        async with httpx.AsyncClient(timeout=180) as c:
            r = await c.post(f"{OLLAMA_URL}/api/chat", json={
                "model":      OLLAMA_MODEL,
                "messages":   messages,
                "stream":     False,
                "keep_alive": -1,
                "options": {
                    "temperature":    0.3,
                    "num_predict":    max_tokens,
                    "repeat_penalty": 1.1,
                    "top_k":          20,
                    "top_p":          0.8,
                },
            })
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
    except httpx.ConnectError:
        return "❌ Ollama non joignable. Lance : ollama serve"
    except httpx.TimeoutException:
        return "❌ Timeout — réduisez MAX_TOKENS_ASK dans .env"
    except Exception as e:
        return f"❌ Erreur Ollama : {e}"


def generate_qwen2(messages: List[dict], max_tokens: int = 150) -> str:
    if not model_ready:
        return "⚠️ Qwen2 non chargé."
    import torch
    text   = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text], return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.3,
            do_sample=True,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        out[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    ).strip()


async def generate(messages: List[dict], max_tokens: int = 150) -> str:
    if MODEL_BACKEND == "groq":
        return await generate_groq(messages, max_tokens)
    if MODEL_BACKEND == "ollama":
        return await generate_ollama(messages, max_tokens)
    return generate_qwen2(messages, max_tokens)


# ── Endpoints ────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"service": "JurisRoute MA API", "status": "actif", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    model_id = (
        GROQ_MODEL     if MODEL_BACKEND == "groq"   else
        OLLAMA_MODEL   if MODEL_BACKEND == "ollama" else
        QWEN2_MODEL_ID
    )
    return {
        "api":     "ok",
        "backend": MODEL_BACKEND,
        "model":   model_id,
        "rag":     index_stats(),
    }


@app.post("/ask", response_model=JurisResponse, tags=["Juridique"])
async def ask(req: QuestionRequest):
    t0 = time.time()
    log.info(f"📩 /ask : {req.question[:80]}")

    context, sources = build_context(req.question, top_k=3, use_hybrid=USE_HYBRID_SEARCH) if req.use_rag else ("", [])
    messages = build_rag_prompt(req.question, context, format_style=RESPONSE_FORMAT)
    answer   = await generate(messages, max_tokens=MAX_TOKENS_ASK)

    log.info(f"✅ /ask répondu en {round(time.time()-t0, 1)}s")

    # Format sources with enhanced metadata
    formatted_sources = []
    for s in sources:
        source_info = {
            "text": s["text"][:200],
            "source": s.get("source"),
            "score": s.get("combined_score") or s.get("semantic_score") or s.get("score"),
            "semantic_score": s.get("semantic_score"),
            "keyword_score": s.get("keyword_score"),
            "article": s.get("article"),
            "hierarchy": s.get("hierarchy_path"),
        }
        formatted_sources.append(source_info)

    model_id = (
        GROQ_MODEL if MODEL_BACKEND == "groq" else
        OLLAMA_MODEL if MODEL_BACKEND == "ollama" else
        QWEN2_MODEL_ID
    )

    return JurisResponse(
        question=req.question,
        answer=answer,
        sources=formatted_sources,
        model_used=f"{MODEL_BACKEND}:{model_id}",
        processing_time_s=round(time.time() - t0, 2),
        search_method="hybrid" if (USE_HYBRID_SEARCH and req.use_rag) else ("semantic" if req.use_rag else "none"),
    )


@app.post("/analyze-image", response_model=JurisResponse, tags=["Documents"])
async def analyze_image(file: UploadFile = File(...)):
    t0      = time.time()
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    if Path(file.filename).suffix.lower() not in allowed:
        raise HTTPException(400, f"Format non supporté. Acceptés : {allowed}")

    fb  = await file.read()
    log.info(f"📸 /analyze-image : {file.filename} ({len(fb)//1024} KB)")

    doc = analyze_document(fb, file.filename)
    if doc.get("error"):
        raise HTTPException(422, doc["error"])
    if not doc["ocr"].get("text"):
        raise HTTPException(422, "Impossible d'extraire du texte de l'image.")

    context, sources = build_context(doc["rag_query"], top_k=3, use_hybrid=USE_HYBRID_SEARCH)
    answer = await generate(build_rag_prompt(doc["rag_query"], context, format_style=RESPONSE_FORMAT), max_tokens=MAX_TOKENS_IMAGE)

    # Format sources with enhanced metadata
    formatted_sources = []
    for s in sources:
        source_info = {
            "text": s["text"][:200],
            "source": s.get("source"),
            "score": s.get("combined_score") or s.get("semantic_score") or s.get("score"),
            "semantic_score": s.get("semantic_score"),
            "keyword_score": s.get("keyword_score"),
            "article": s.get("article"),
            "hierarchy": s.get("hierarchy_path"),
        }
        formatted_sources.append(source_info)

    return JurisResponse(
        question=doc["rag_query"],
        answer=answer,
        sources=formatted_sources,
        pv_info=doc.get("pv_info", {}),
        legal_metadata=doc.get("legal_metadata", {}),
        ocr_metadata={
            "confidence": doc["ocr"].get("confidence", 0),
            "quality_score": doc["ocr"].get("quality_score", 0),
            "method": doc["ocr"].get("method", "unknown"),
        },
        model_used=f"{MODEL_BACKEND}:{GROQ_MODEL if MODEL_BACKEND == 'groq' else OLLAMA_MODEL}",
        processing_time_s=round(time.time() - t0, 2),
        search_method="hybrid" if USE_HYBRID_SEARCH else "semantic",
    )


@app.post("/analyze-pdf", response_model=JurisResponse, tags=["Documents"])
async def analyze_pdf(file: UploadFile = File(...)):
    t0 = time.time()
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Seuls les fichiers PDF sont acceptés.")

    fb  = await file.read()
    log.info(f"📄 /analyze-pdf : {file.filename} ({len(fb)//1024} KB)")

    doc = analyze_document(fb, file.filename)
    if doc.get("error"):
        raise HTTPException(422, doc["error"])
    if not doc["ocr"].get("text"):
        raise HTTPException(422, "Impossible d'extraire du texte du PDF.")

    context, sources = build_context(doc["rag_query"], top_k=4, use_hybrid=USE_HYBRID_SEARCH)
    answer = await generate(build_rag_prompt(doc["rag_query"], context, format_style=RESPONSE_FORMAT), max_tokens=MAX_TOKENS_PDF)

    # Format sources with enhanced metadata
    formatted_sources = []
    for s in sources:
        source_info = {
            "text": s["text"][:200],
            "source": s.get("source"),
            "score": s.get("combined_score") or s.get("semantic_score") or s.get("score"),
            "semantic_score": s.get("semantic_score"),
            "keyword_score": s.get("keyword_score"),
            "article": s.get("article"),
            "hierarchy": s.get("hierarchy_path"),
        }
        formatted_sources.append(source_info)

    return JurisResponse(
        question=doc["rag_query"],
        answer=answer,
        sources=formatted_sources,
        pv_info=doc.get("pv_info", {}),
        legal_metadata=doc.get("legal_metadata", {}),
        ocr_metadata={
            "confidence": doc["ocr"].get("confidence", 0),
            "quality_score": doc["ocr"].get("quality_score", 0),
            "method": doc["ocr"].get("method", "unknown"),
        },
        model_used=f"{MODEL_BACKEND}:{GROQ_MODEL if MODEL_BACKEND == 'groq' else OLLAMA_MODEL}",
        processing_time_s=round(time.time() - t0, 2),
        search_method="hybrid" if USE_HYBRID_SEARCH else "semantic",
    )


@app.get("/stats", tags=["Admin"])
async def stats():
    model_id = (
        GROQ_MODEL     if MODEL_BACKEND == "groq"   else
        OLLAMA_MODEL   if MODEL_BACKEND == "ollama" else
        QWEN2_MODEL_ID
    )
    return {
        "rag": index_stats(),
        "model": {
            "backend": MODEL_BACKEND,
            "id": model_id,
            "ready": model_ready if MODEL_BACKEND == "qwen2" else True,
        },
        "search": {
            "enabled": USE_HYBRID_SEARCH,
            "semantic_weight": HYBRID_SEMANTIC_WEIGHT,
            "keyword_weight": HYBRID_KEYWORD_WEIGHT,
        },
    }