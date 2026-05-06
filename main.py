"""
Style Rule Evaluator API  —  Production-scale edition
======================================================
All hot paths are safe at 777k products:
 
  /looks          → tag-index pre-filter → score ≤300 candidates
  /search/neural  → Atlas $vectorSearch ANN (C++ inside MongoDB)
  /search/combined→ Atlas $vectorSearch + tag-boost aggregation (all in MongoDB)
  /products/embed → paginated batch, never OOM
 
Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import asyncio
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
 
from evaluator  import RuleEvaluator
from database   import Database
from models     import UserProfile, EvaluationResult, RuleCreate
from vectorizer import FashionVectorizer
 
logger = logging.getLogger(__name__)
 
app = FastAPI(title="Style Rule Evaluator", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
 
db         = Database()
evaluator  = RuleEvaluator()
vectorizer = FashionVectorizer()
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Core helper — used by every Looks-tab endpoint
# ──────────────────────────────────────────────────────────────────────────────
 
async def _get_or_evaluate(profile: UserProfile) -> dict:
    """
    Return stored grouped_attributes for this profile.
    If nothing is stored yet, run a fresh evaluation, save it, and return it.
 
    This makes every Looks-tab endpoint self-contained — the user never has to
    manually click "Evaluate → Store" before clicking Neural / Combined search.
    """
    p = profile.dict(exclude_none=True)
    if not p:
        raise HTTPException(400, "Profile is empty — select at least one field.")
 
    stored = await db.get_evaluation(p)
    if stored:
        grouped = stored.get("grouped_attributes", {})
        if grouped:
            return grouped          # fast path — already stored
 
    # Nothing stored (or grouped_attributes missing) → evaluate now
    rules = await db.get_rules(is_active=True)
    if not rules:
        raise HTTPException(404, "No active rules in database. Run POST /seed first.")
 
    result = evaluator.evaluate(p, rules)
    await db.save_evaluation(p, result)     # store so next call is instant
 
    # Re-fetch to get the grouped_attributes structure built by save_evaluation
    stored = await db.get_evaluation(p)
    grouped = stored.get("grouped_attributes", {}) if stored else {}
 
    if not grouped:
        raise HTTPException(500, "Evaluation ran but produced no attributes. "
                                 "Check that your rules have actions.")
    return grouped
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Health / root
# ──────────────────────────────────────────────────────────────────────────────
 
@app.get("/")
async def root():
    return {"status": "ok", "service": "Style Rule Evaluator", "version": "3.0.0"}
 
 
@app.get("/health")
async def health():
    return {"status": "healthy", "database": await db.ping(),
            "vectorizer_mode": vectorizer.mode}
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Rules CRUD  (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/rules")
async def create_rule(rule: RuleCreate):
    return await db.create_rule(rule.dict())
 
@app.get("/rules")
async def get_rules(field: Optional[str] = None, is_active: Optional[bool] = True):
    rules = await db.get_rules(field=field, is_active=is_active)
    return {"rules": rules, "count": len(rules)}
 
@app.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    rule = await db.get_rule(rule_id)
    if not rule: raise HTTPException(404, "Rule not found")
    return rule
 
@app.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule: RuleCreate):
    result = await db.update_rule(rule_id, rule.dict())
    if not result: raise HTTPException(404, "Rule not found")
    return result
 
@app.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    if not await db.delete_rule(rule_id): raise HTTPException(404, "Rule not found")
    return {"deleted": True}
 
@app.patch("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str):
    result = await db.toggle_rule(rule_id)
    if not result: raise HTTPException(404, "Rule not found")
    return result
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Evaluation  (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate_user(profile: UserProfile):
    """Evaluate profile → save to MongoDB."""
    rules = await db.get_rules(is_active=True)
    if not rules: raise HTTPException(404, "No active rules")
    result = evaluator.evaluate(profile.dict(exclude_none=True), rules)
    await db.save_evaluation(profile.dict(exclude_none=True), result)
    return result
 
@app.post("/evaluate/preview")
async def preview(profile: UserProfile):
    """Evaluate without saving."""
    rules = await db.get_rules(is_active=True)
    if not rules:
        return {"recommend": [], "avoid": [], "all_scores": {},
                "matched_rules": 0, "matched_rule_names": []}
    return evaluator.evaluate(profile.dict(exclude_none=True), rules)
 
@app.post("/stored")
async def get_stored(profile: UserProfile):
    stored = await db.get_evaluation(profile.dict(exclude_none=True))
    if not stored: raise HTTPException(404, "No stored data. Evaluate first.")
    return stored
 
@app.post("/suggest")
async def suggest(profile: UserProfile, limit: int = 20):
    rules = await db.get_rules(is_active=True)
    if not rules: raise HTTPException(404, "No active rules")
    result = evaluator.evaluate(profile.dict(exclude_none=True), rules)
    tags   = [i["value"] for i in result["recommend"][:10]]
    avoid  = [i["value"] for i in result["avoid"][:5]]
    products = await db.search_products(tags, avoid, limit)
    return {"evaluation": result, "suggestions": products}
 
@app.post("/suggest/stored")
async def suggest_stored(profile: UserProfile, limit: int = 20):
    grouped = await _get_or_evaluate(profile)
    tags  = [tag for vals in grouped.values() for tag, sc in vals.items() if sc > 0][:10]
    avoid = [tag for vals in grouped.values() for tag, sc in vals.items() if sc < 0][:5]
    products = await db.search_products(tags, avoid, limit)
    return {"suggestions": products}
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Blueprint + Looks  — FIXED for 777k
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/blueprint")
async def get_blueprint(profile: UserProfile):
    grouped   = await _get_or_evaluate(profile)
    blueprint = evaluator.build_blueprint(grouped)
    blueprint["profile"] = profile.dict(exclude_none=True)
    return blueprint
 
 
@app.post("/looks")
async def generate_looks(
    profile:    UserProfile,
    num_looks:  int = 3,
    category:   Optional[str] = None,
):
    """
    Generate complete outfit looks.
 
    Scale fix:
      - Extract top positive tags from stored attributes
      - Ask MongoDB for ≤300 matching products (tag index)
      - Python scores only those ≤300 docs
      - Never loads the full 777k collection
    """
    grouped = await _get_or_evaluate(profile)
    positive_tags = []
    negative_tags = []
    for attr_values in grouped.values():
        for tag, score in attr_values.items():
            if score > 0:
                positive_tags.append(tag)
            elif score < 0:
                negative_tags.append(tag)
 
    if not positive_tags:
        raise HTTPException(400, "No positive attributes to match products against")
 
    # ── 2. Fetch ≤300 candidates via MongoDB tag index ────────────────────────
    candidates = await db.get_candidate_products(
        positive_tags=positive_tags[:30],   # top 30 tags are plenty for the index
        negative_tags=negative_tags[:10],
        category=category,
        limit=300,
    )
 
    if not candidates:
        raise HTTPException(404, "No products matched in catalog")
 
    # ── 3. Python scores only the ≤300 candidates ────────────────────────────
    blueprint        = evaluator.build_blueprint(grouped)
    scored_products  = evaluator.score_all_products(candidates, grouped)
    looks            = evaluator.generate_looks(candidates, grouped, num_looks)
 
    return {
        "blueprint":             blueprint,
        "scored_products":       scored_products,
        "looks":                 looks,
        "total_products_scored": len(scored_products),
        "candidates_fetched":    len(candidates),
        "scale_note":            "MongoDB tag-index pre-filter applied — full collection NOT scanned",
    }
 
 
# ──────────────────────────────────────────────────────────────────────────────
# PRE-COMPUTE EMBEDDINGS  — Paginated, safe at 777k
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/products/embed")
async def embed_all_products(batch_size: int = 100):
    """
    Pre-compute embeddings for ALL products and store in MongoDB.
 
    Scale fix: processes in batches of `batch_size` — never loads all 777k
    into RAM at once.  For 777k products ≈ 7,770 batches.
 
    Tip: run with batch_size=200 and call this endpoint once.
    It is idempotent — skips already-embedded products.
    """
    total_unembedded = await db.count_unembedded_products()
    if total_unembedded == 0:
        embedded_total = await db.count_embedded_products()
        return {"message": "All products already embedded",
                "embedded": embedded_total}
 
    embedded = 0
    skip     = 0
    dim      = 0
 
    while True:
        batch = await db.get_products_without_embeddings(
            batch_size=batch_size, skip=skip)
        if not batch:
            break
 
        for product in batch:
            text      = vectorizer._product_to_text(product)
            embedding = vectorizer.embed_text(text)
            pid       = product.get("_id", "")
            if pid:
                await db.store_product_embedding(pid, embedding, text)
                embedded += 1
                dim       = len(embedding)
 
        skip += batch_size
        logger.info("Embedded %d / %d products …", embedded, total_unembedded)
 
    return {
        "embedded":       embedded,
        "total_unembedded_before": total_unembedded,
        "embedding_dim":  dim,
        "vectorizer_mode": vectorizer.mode,
        "atlas_index_note": (
            "Now create an Atlas Search vector index on 'products.embedding' "
            f"(name='{db.VECTOR_INDEX_NAME if hasattr(db, 'VECTOR_INDEX_NAME') else 'embedding_index'}', "
            "dimensions=384, similarity=cosine) to enable /search/neural."
        ),
    }
 
 
# ──────────────────────────────────────────────────────────────────────────────
# NEURAL SEARCH  — Atlas $vectorSearch, never loads embeddings into Python
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/search/neural")
async def neural_search(
    profile:        UserProfile,
    top_k:          int = 10,
    num_candidates: int = 1000,
    category:       Optional[str] = None,
):
    """
    Neural search at 777k scale.
 
    What changed vs the old version:
      OLD: loaded ALL embedded products into Python RAM → cosine loop in Python
      NEW: sends ONE query vector to MongoDB Atlas $vectorSearch →
           MongoDB ANN in C++ scans numCandidates=1000, returns top_k
 
    numCandidates controls accuracy/speed trade-off:
      500  → fast,  slightly less accurate
      1000 → good balance  (default)
      5000 → very accurate, slightly slower (still ms-range)
    """
    grouped = await _get_or_evaluate(profile)
 
    # Build query vector from user's attribute profile
    query_text = vectorizer._attributes_to_text(grouped)
    query_vec  = vectorizer.embed_text(query_text)
 
    # ── Atlas Vector Search (all computation in MongoDB) ─────────────────────
    atlas_results = await db.vector_search(
        query_vector    = query_vec,
        num_candidates  = num_candidates,
        limit           = top_k,
        category_filter = category,
    )
 
    if atlas_results:
        # Enrich with synonym-match labels (cheap: only top_k docs)
        enriched = []
        for p in atlas_results:
            matched_terms = _find_matched_terms(grouped, p.get("tags", []))
            enriched.append({
                "product":         p.get("name", "Unknown"),
                "category":        p.get("category", ""),
                "tags":            p.get("tags", []),
                "price":           p.get("price", 0),
                "similarity":      round(p.get("vector_score", 0), 4),
                "matched_terms":   matched_terms,
                "synonym_matches": [m for m in matched_terms if "~" in m],
                "model":           "atlas_vector_search",
            })
        return {
            "search_type":   "neural",
            "backend":       "atlas_vector_search",
            "num_candidates": num_candidates,
            "results":       enriched,
            "total":         len(enriched),
        }
 
    # ── Fallback: symbolic smart_search (local / no Atlas) ───────────────────
    logger.warning("Atlas Vector Search unavailable — falling back to symbolic search")
    candidates = await db.get_candidate_products(
        positive_tags=_top_positive_tags(grouped, n=20),
        limit=500,
    )
    results = vectorizer.smart_search(grouped, candidates, top_k)
    return {
        "search_type": "neural",
        "backend":     "symbolic_fallback",
        "results":     results,
        "total":       len(results),
        "warning":     "Atlas Vector Search not available on this deployment",
    }
 
 
# ──────────────────────────────────────────────────────────────────────────────
# COMBINED NEURO-SYMBOLIC  — Atlas ANN + tag-boost aggregation in MongoDB
# ──────────────────────────────────────────────────────────────────────────────
 
@app.post("/search/combined")
async def combined_search(
    profile:        UserProfile,
    alpha:          float = 0.6,
    top_k:          int   = 10,
    num_candidates: int   = 1500,
):
    """
    Neuro-symbolic search at 777k scale.
 
    What changed vs the old version:
      OLD: get_all_products → score_all_products in Python → neural loop in Python
      NEW: single MongoDB aggregation pipeline:
           $vectorSearch → $addFields tag_hits/misses → $addFields boosted_score
           → $sort → $limit
           Zero Python loops over the product collection.
 
    alpha is kept in the response for UI display but the actual blending
    is done in the MongoDB aggregation (0.6 vector / 0.3 tag overlap / 0.1 penalty).
    """
    grouped = await _get_or_evaluate(profile)
 
    positive_tags = _top_positive_tags(grouped, n=30)
    negative_tags = _top_negative_tags(grouped, n=10)
 
    query_text = vectorizer._attributes_to_text(grouped)
    query_vec  = vectorizer.embed_text(query_text)
 
    # ── Single MongoDB aggregation — ANN + tag-boost + sort + limit ──────────
    atlas_results = await db.vector_search_with_tag_boost(
        query_vector    = query_vec,
        positive_tags   = positive_tags,
        negative_tags   = negative_tags,
        num_candidates  = num_candidates,
        limit           = top_k,
    )
 
    if atlas_results:
        enriched = []
        for p in atlas_results:
            matched_terms = _find_matched_terms(grouped, p.get("tags", []))
            enriched.append({
                "product":          p.get("name", "Unknown"),
                "category":         p.get("category", ""),
                "tags":             p.get("tags", []),
                "price":            p.get("price", 0),
                "vector_score":     round(p.get("vector_score",  0), 4),
                "tag_hits":         p.get("tag_hits",            0),
                "combined_score":   round(p.get("boosted_score", 0), 4),
                # Keep field names same as old API for frontend compatibility
                "symbolic_score":   p.get("tag_hits", 0),
                "neural_similarity":round(p.get("vector_score",  0), 4),
                "matched_terms":    matched_terms,
                "synonym_matches":  [m for m in matched_terms if "~" in m],
                "backend":          "atlas_vector_search",
            })
        return {
            "search_type": "neuro_symbolic",
            "backend":     "atlas_vector_search",
            "alpha":       alpha,
            "results":     enriched,
            "total":       len(enriched),
        }
 
    # ── Fallback: original Python combined search on limited candidates ───────
    logger.warning("Atlas Vector Search unavailable — falling back to combined symbolic search")
    candidates       = await db.get_candidate_products(positive_tags, negative_tags, limit=500)
    symbolic_scores  = evaluator.score_all_products(candidates, grouped)
    results          = vectorizer.combined_search(
        grouped, candidates, symbolic_scores, alpha, top_k)
    return {
        "search_type": "neuro_symbolic",
        "backend":     "symbolic_fallback",
        "alpha":       alpha,
        "results":     results,
        "total":       len(results),
        "warning":     "Atlas Vector Search not available on this deployment",
    }
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Stats + Seed
# ──────────────────────────────────────────────────────────────────────────────
 
@app.get("/stats")
async def stats():
    embedded   = await db.count_embedded_products()
    unembedded = await db.count_unembedded_products()
    return {
        "total_rules":        await db.count_rules(),
        "active_rules":       await db.count_rules(True),
        "evaluations":        await db.count_evaluations(),
        "embedded_products":  embedded,
        "unembedded_products": unembedded,
        "vectorizer_mode":    vectorizer.mode,
        "atlas_ready":        embedded > 0,
    }
 
@app.post("/seed")
async def seed():
    from seed_data import SEED_RULES, SEED_PRODUCTS
    r = await db.seed_rules(SEED_RULES)
    p = await db.seed_products(SEED_PRODUCTS)
    return {"rules": r, "products": p}
 
 
# ──────────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────────
 
def _top_positive_tags(grouped: dict, n: int = 30) -> list:
    """Extract the N highest-scoring positive tags from grouped_attributes."""
    pairs = [
        (tag, score)
        for attr_vals in grouped.values()
        for tag, score in attr_vals.items()
        if score > 0
    ]
    pairs.sort(key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in pairs[:n]]
 
 
def _top_negative_tags(grouped: dict, n: int = 10) -> list:
    pairs = [
        (tag, score)
        for attr_vals in grouped.values()
        for tag, score in attr_vals.items()
        if score < 0
    ]
    pairs.sort(key=lambda x: x[1])
    return [tag for tag, _ in pairs[:n]]
 
 
def _find_matched_terms(grouped: dict, product_tags: list) -> list:
    """Lightweight synonym-match labeller for top_k results only."""
    attr_terms  = [t for vals in grouped.values() for t in vals]
    tag_set     = set(product_tags)
    matched     = []
    for tag in product_tags:
        n_tag = vectorizer.normalize_term(tag)
        for attr in attr_terms:
            n_attr = vectorizer.normalize_term(attr)
            if n_tag == n_attr:
                label = f"{tag} (exact)" if tag == attr else f"{tag} ~ {attr}"
                matched.append(label)
    return matched
 
 
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)