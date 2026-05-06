"""
Fashion Vectorizer — Production Version
========================================
Uses sentence-transformers (all-MiniLM-L6-v2) for real vector embeddings.
Falls back to the synonym-based bag-of-words approach if the model is unavailable.
 
Install dependencies:
    pip install sentence-transformers numpy
 
Methods used by main.py:
    vectorizer.embed_text(text)              → List[float]
    vectorizer._product_to_text(product)     → str
    vectorizer._attributes_to_text(grouped)  → str
    vectorizer.normalize_term(term)          → str
    vectorizer.smart_search(...)             → List[Dict]
    vectorizer.combined_search(...)          → List[Dict]
    vectorizer.cosine_similarity(a, b)       → float
"""
 
from __future__ import annotations
 
import math
import logging
from typing import Dict, List, Tuple, Optional
 
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# Try to import the neural backend; fall back gracefully
# ---------------------------------------------------------------------------
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
 
    _MODEL_NAME = "all-MiniLM-L6-v2"
    _model: Optional[SentenceTransformer] = None  # lazy-loaded
 
    def _get_model() -> SentenceTransformer:
        global _model
        if _model is None:
            logger.info("Loading sentence-transformers model '%s' …", _MODEL_NAME)
            _model = SentenceTransformer(_MODEL_NAME)
        return _model
 
    NEURAL_AVAILABLE = True
 
except ImportError:
    NEURAL_AVAILABLE = False
    logger.warning(
        "sentence-transformers / numpy not found. "
        "Falling back to symbolic (bag-of-words) mode. "
        "Run: pip install sentence-transformers numpy"
    )
 
# ---------------------------------------------------------------------------
# Fashion synonym groups
# ---------------------------------------------------------------------------
FASHION_SYNONYMS: Dict[str, List[str]] = {
    # Fit
    "tailored":  ["structured", "fitted", "slim_cut", "sharp", "clean_cut"],
    "relaxed":   ["loose", "easy", "casual", "comfortable", "laid_back"],
    "bodycon":   ["body_hugging", "tight", "figure_hugging", "skin_tight"],
    "oversized": ["boxy", "baggy", "roomy"],
    "a_line":    ["flared", "swing", "trapeze", "tent"],
    "wrap":      ["surplice", "crossover", "tie_front"],
    "slim":      ["narrow", "skinny", "fitted", "lean"],
    # Fabric
    "silk":    ["satin", "charmeuse", "crepe_de_chine", "habotai"],
    "chiffon": ["georgette", "organza", "sheer", "voile", "tulle"],
    "cotton":  ["poplin", "chambray", "muslin", "lawn", "broadcloth"],
    "linen":   ["flax", "ramie", "hemp_blend"],
    "denim":   ["chambray", "jean", "dungaree"],
    "wool":    ["tweed", "cashmere", "merino", "flannel", "felt"],
    "leather": ["faux_leather", "vegan_leather", "suede", "nubuck"],
    "velvet":  ["velour", "plush", "crushed_velvet"],
    "jersey":  ["knit", "stretch", "interlock", "ponte"],
    "lace":    ["guipure", "chantilly", "broderie", "eyelet", "crochet"],
    "satin":   ["silk", "duchess", "charmeuse", "crepe_back"],
    # Color
    "white":    ["ivory", "cream", "off_white", "pearl", "snow", "chalk"],
    "black":    ["jet", "onyx", "charcoal", "ebony", "midnight"],
    "navy":     ["midnight_blue", "dark_blue", "nautical", "indigo"],
    "red":      ["crimson", "scarlet", "burgundy", "wine", "cherry", "ruby"],
    "pink":     ["blush", "rose", "fuchsia", "magenta", "coral"],
    "beige":    ["nude", "sand", "khaki", "camel", "tan", "oatmeal"],
    "gold":     ["metallic_gold", "champagne", "gilded", "brass"],
    "emerald":  ["forest_green", "hunter", "jade", "bottle_green"],
    "lavender": ["lilac", "mauve", "periwinkle", "wisteria"],
    "coral":    ["salmon", "peach", "terracotta", "apricot"],
    # Neckline
    "v_neck":      ["deep_v", "plunge", "v_shape"],
    "scoop":       ["round", "u_neck", "ballet"],
    "boat":        ["bateau", "wide"],
    "turtle":      ["turtleneck", "mock_neck", "high_neck", "funnel"],
    "sweetheart":  ["heart_shaped", "curved", "bustier"],
    # Pattern
    "floral":    ["botanical", "flower", "ditsy", "tropical_print", "garden"],
    "solid":     ["plain", "block_color", "single_color", "monochrome_print"],
    "stripes":   ["striped", "pinstripe", "breton", "nautical_stripe"],
    "checks":    ["plaid", "gingham", "tartan", "buffalo_check", "houndstooth"],
    "animal":    ["leopard", "zebra", "snake", "tiger", "cheetah"],
    "geometric": ["abstract", "graphic", "mod", "angular"],
    "paisley":   ["bohemian_print", "bandana_print", "ethnic_print"],
    # Palette
    "neutral": ["earthy", "muted", "understated", "subtle", "tonal"],
    "bright":  ["vivid", "bold", "saturated", "vibrant", "electric"],
    "pastel":  ["soft", "light", "pale", "baby", "powder"],
    "dark":    ["deep", "rich", "moody", "noir", "dramatic"],
    "jewel":   ["emerald_tone", "ruby_tone", "sapphire", "amethyst", "rich_tone"],
    "earth":   ["terracotta_tone", "olive", "rust_tone", "ochre", "sienna"],
    # Length
    "maxi":  ["floor_length", "full_length", "ankle_length", "long"],
    "midi":  ["calf_length", "tea_length", "below_knee"],
    "mini":  ["short", "above_knee", "micro"],
    "knee":  ["knee_length", "just_above_knee", "at_knee"],
    # Style
    "minimalist": ["clean", "simple", "understated", "pared_back"],
    "boho":       ["bohemian", "hippie", "free_spirited", "gypsy"],
    "classic":    ["timeless", "traditional", "preppy", "conservative"],
    "edgy":       ["punk", "grunge", "rock", "alternative", "rebellious"],
    "romantic":   ["feminine", "soft", "dreamy", "delicate", "ethereal"],
}
 
 
# ---------------------------------------------------------------------------
# Module-level text helpers (also used internally by the class)
# ---------------------------------------------------------------------------
 
def _tags_to_sentence(tags: List[str]) -> str:
    """["navy", "tailored", "cotton"] → 'navy tailored cotton fashion item'"""
    clean = [t.replace("_", " ").strip() for t in tags if t]
    return " ".join(clean) + " fashion item"
 
 
def _attributes_to_sentence(grouped_attributes: Dict) -> str:
    """
    {"fit": {"tailored": 3.5}, "color": {"navy": 2.0}}
    → weighted natural-language description.
    High-score terms are repeated so the embedding is biased toward them.
    """
    tokens: List[str] = []
    for _cat, values in grouped_attributes.items():
        for term, score in values.items():
            clean   = term.replace("_", " ").strip()
            repeats = max(1, round(abs(float(score))))
            if float(score) > 0:
                tokens.extend([clean] * repeats)
            else:
                tokens.append(f"not {clean}")
    return " ".join(tokens) + " fashion style"
 
 
# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
 
class FashionVectorizer:
    """
    Converts fashion descriptions to dense vectors and computes similarity.
 
    Two backends:
    - "neural"   — sentence-transformers all-MiniLM-L6-v2 (384-dim float32)
    - "symbolic" — bag-of-words + synonym expansion (pure Python, no deps)
 
    The backend is chosen automatically based on availability.
    """
 
    def __init__(self, mode: str = "auto"):
        if mode == "neural" and not NEURAL_AVAILABLE:
            raise ImportError(
                "sentence-transformers and numpy are required for neural mode. "
                "Run: pip install sentence-transformers numpy"
            )
 
        self.mode: str = (
            "neural" if (NEURAL_AVAILABLE and mode in ("auto", "neural")) else "symbolic"
        )
 
        # Synonym map for term normalisation
        self.synonym_map: Dict[str, str] = {}
        for main_word, synonyms in FASHION_SYNONYMS.items():
            for syn in synonyms:
                self.synonym_map[syn] = main_word
            self.synonym_map[main_word] = main_word
 
        self.vocab: List[str] = sorted(set(
            list(FASHION_SYNONYMS.keys()) +
            [s for syns in FASHION_SYNONYMS.values() for s in syns]
        ))
        self.word_to_idx: Dict[str, int] = {w: i for i, w in enumerate(self.vocab)}
 
        logger.info("FashionVectorizer initialised in '%s' mode.", self.mode)
 
    # ------------------------------------------------------------------
    # PUBLIC: Text conversion helpers  ← called by main.py
    # ------------------------------------------------------------------
 
    def _product_to_text(self, product: Dict) -> str:
        """
        Convert a product dict to a plain text string for embedding.
        Called by main.py /products/embed endpoint.
 
        {"name": "Navy Silk Blazer", "tags": ["navy", "silk", "tailored"],
         "category": "outerwear"}
        → "navy silk tailored outerwear Navy Silk Blazer fashion item"
        """
        tags      = product.get("tags", [])
        name      = product.get("name", "")
        category  = product.get("category", "")
        all_terms = [t.replace("_", " ") for t in tags] + [category, name]
        clean     = [t.strip() for t in all_terms if t.strip()]
        return " ".join(clean) + " fashion item"
 
    def _attributes_to_text(self, grouped_attributes: Dict) -> str:
        """
        Convert grouped_attributes from MongoDB into a query text string.
        Called by main.py /search/neural and /search/combined endpoints.
 
        {"fit": {"tailored": 3.5, "bodycon": -2}, "neckline": {"v_neck": 2.5}}
        → "tailored tailored tailored v neck v neck not bodycon fashion style"
        """
        return _attributes_to_sentence(grouped_attributes)
 
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a plain text string and return a list of floats.
        Called by main.py for both query and product embedding.
 
        Neural  → 384-dim float32 numpy array (returned as list for JSON/MongoDB)
        Symbolic → bag-of-words list[float]
        """
        vec = self.embed(text)
        if NEURAL_AVAILABLE and isinstance(vec, np.ndarray):
            return vec.tolist()   # convert numpy → plain Python list for MongoDB storage
        return vec
 
    # ------------------------------------------------------------------
    # PUBLIC: Vector creation
    # ------------------------------------------------------------------
 
    def embed(self, text: str):
        """
        Return a unit-normalised vector for text.
        Neural  → numpy ndarray shape (384,)
        Symbolic → list[float] length = len(vocab)
        """
        if self.mode == "neural":
            model = _get_model()
            return model.encode(text, normalize_embeddings=True)
        else:
            return self._symbolic_embed(text)
 
    def attributes_to_vector(self, grouped_attributes: Dict) -> Tuple:
        """
        Convert grouped_attributes → (vector, list_of_terms).
        Used internally by smart_search / combined_search.
        """
        terms = [v for vals in grouped_attributes.values() for v in vals]
        if self.mode == "neural":
            sentence = _attributes_to_sentence(grouped_attributes)
            vec      = self.embed(sentence)
        else:
            weights = {
                v: score
                for vals in grouped_attributes.values()
                for v, score in vals.items()
            }
            vec = self._symbolic_text_to_vector(terms, weights)
        return vec, terms
 
    def product_to_vector(self, product: Dict) -> Tuple:
        """
        Convert a product dict → (vector, list_of_terms).
        Used internally by smart_search.
        """
        tags       = product.get("tags", [])
        name_words = product.get("name", "").lower().replace("-", "_").split()
        all_terms  = list(set(tags + name_words))
 
        if self.mode == "neural":
            sentence = _tags_to_sentence(all_terms)
            vec      = self.embed(sentence)
        else:
            vec = self._symbolic_text_to_vector(all_terms)
        return vec, all_terms
 
    # ------------------------------------------------------------------
    # PUBLIC: Similarity
    # ------------------------------------------------------------------
 
    def cosine_similarity(self, vec_a, vec_b) -> float:
        """
        Cosine similarity. Accepts numpy arrays (neural) or plain lists (symbolic).
        Both neural vectors are already L2-normalised → dot product = cosine sim.
        """
        if NEURAL_AVAILABLE and isinstance(vec_a, np.ndarray):
            # If vec_b came from MongoDB it may be a plain list → convert
            b = np.array(vec_b, dtype=np.float32) if not isinstance(vec_b, np.ndarray) else vec_b
            return float(round(float(np.dot(vec_a, b)), 4))
        else:
            dot   = sum(a * b for a, b in zip(vec_a, vec_b))
            mag_a = math.sqrt(sum(a * a for a in vec_a))
            mag_b = math.sqrt(sum(b * b for b in vec_b))
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return round(dot / (mag_a * mag_b), 4)
 
    # ------------------------------------------------------------------
    # PUBLIC: Search  (fallback when Atlas Vector Search unavailable)
    # ------------------------------------------------------------------
 
    def smart_search(
        self,
        grouped_attributes: Dict,
        products: List[Dict],
        top_k: int = 10,
    ) -> List[Dict]:
        """Rank products by cosine similarity to user attributes."""
        attr_vec, attr_terms = self.attributes_to_vector(grouped_attributes)
 
        results = []
        for product in products:
            prod_vec, _ = self.product_to_vector(product)
            similarity  = self.cosine_similarity(attr_vec, prod_vec)
            matched     = self._find_matches(product.get("tags", []), attr_terms)
            results.append({
                "product":        product.get("name", "Unknown"),
                "category":       product.get("category", ""),
                "tags":           product.get("tags", []),
                "price":          product.get("price", 0),
                "similarity":     similarity,
                "matched_terms":  matched,
                "synonym_matches":[m for m in matched if "~" in m],
                "backend":        self.mode,
            })
 
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
 
    def combined_search(
        self,
        grouped_attributes: Dict,
        products: List[Dict],
        symbolic_scores: List[Dict],
        alpha: float = 0.6,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Neuro-symbolic blend.
        final = alpha * normalised_symbolic + (1-alpha) * neural_similarity
        """
        neural_results = self.smart_search(grouped_attributes, products, top_k=len(products))
        neural_map     = {r["product"]: r for r in neural_results}
 
        symbolic_map: Dict[str, float] = {}
        for s in symbolic_scores:
            key = s.get("product") or s.get("name", "")
            symbolic_map[key] = float(s.get("score", 0))
 
        max_sym   = max(symbolic_map.values(), default=1.0)
        min_sym   = min(symbolic_map.values(), default=0.0)
        range_sym = (max_sym - min_sym) or 1.0
 
        combined = []
        for product in products:
            name           = product.get("name", "Unknown")
            neural_score   = neural_map.get(name, {}).get("similarity", 0.0)
            symbolic_score = symbolic_map.get(name, 0.0)
            sym_norm       = (symbolic_score - min_sym) / range_sym
            final          = round(alpha * sym_norm + (1 - alpha) * neural_score, 4)
 
            combined.append({
                "product":          name,
                "category":         product.get("category", ""),
                "tags":             product.get("tags", []),
                "price":            product.get("price", 0),
                "symbolic_score":   round(symbolic_score, 1),
                "neural_similarity":neural_score,
                "combined_score":   final,
                "matched_terms":    neural_map.get(name, {}).get("matched_terms", []),
                "synonym_matches":  neural_map.get(name, {}).get("synonym_matches", []),
                "backend":          self.mode,
            })
 
        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined[:top_k]
 
    # ------------------------------------------------------------------
    # PUBLIC: Term normalisation  (used by main.py _find_matched_terms)
    # ------------------------------------------------------------------
 
    def normalize_term(self, term: str) -> str:
        t = term.lower().strip().replace(" ", "_").replace("-", "_")
        return self.synonym_map.get(t, t)
 
    # ------------------------------------------------------------------
    # Private: symbolic helpers
    # ------------------------------------------------------------------
 
    def _symbolic_embed(self, text: str) -> List[float]:
        tokens = text.lower().replace("-", "_").split()
        return self._symbolic_text_to_vector(tokens)
 
    def _symbolic_text_to_vector(
        self,
        terms: List[str],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[float]:
        vec = [0.0] * len(self.vocab)
        for term in terms:
            normalised = self.normalize_term(term)
            weight = 1.0
            if weights:
                weight = weights.get(term, weights.get(normalised, 1.0))
            if normalised in self.word_to_idx:
                vec[self.word_to_idx[normalised]] = weight
            if normalised in FASHION_SYNONYMS:
                for syn in FASHION_SYNONYMS[normalised]:
                    if syn in self.word_to_idx:
                        idx = self.word_to_idx[syn]
                        vec[idx] = max(vec[idx], weight * 0.7)
        return vec
 
    def _find_matches(self, product_tags: List[str], attr_terms: List[str]) -> List[str]:
        matched = []
        for tag in product_tags:
            n_tag = self.normalize_term(tag)
            for attr in attr_terms:
                n_attr = self.normalize_term(attr)
                if n_tag == n_attr:
                    label = f"{tag} (exact)" if tag == attr else f"{tag} ~ {attr}"
                    matched.append(label)
        return matched
 
 
# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fv = FashionVectorizer()
    print(f"Backend: {fv.mode}")
 
    grouped = {
        "fit":    {"tailored": 3.5, "bodycon": -2.0},
        "color":  {"navy": 2.5},
        "fabric": {"silk": 2.0},
    }
    text = fv._attributes_to_text(grouped)
    vec  = fv.embed_text(text)
    print(f"Query text : {text[:80]}...")
    print(f"Vector dim : {len(vec)}")
 
    products = [
        {"name": "Navy Silk Blazer",     "tags": ["navy", "silk", "tailored"],  "price": 4999, "category": "outerwear"},
        {"name": "Ivory Chiffon Blouse", "tags": ["ivory", "chiffon", "relaxed"],"price": 1299, "category": "tops"},
        {"name": "Emerald Bodycon Dress","tags": ["emerald", "bodycon", "jersey"],"price": 2499, "category": "dresses"},
    ]
    print("\n=== Smart Search ===")
    for r in fv.smart_search(grouped, products, top_k=3):
        print(f"  {r['similarity']:.4f}  {r['product']}")