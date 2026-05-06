

"""
Rule Evaluator Engine
=====================
Matches rules to user profiles, sums scores with deduplication.
Builds outfit blueprints and scores products with category-aware weighting.
"""
from typing import Dict, List, Any
 
 
# Which attributes matter for which product category
# Shoes don't have necklines. Tops don't have heel types.
CATEGORY_ATTRIBUTE_MAP = {
    "tops":        ["colorFamily", "fabric", "fit", "neckline", "sleeve", "pattern", "palette"],
    "bottoms":     ["colorFamily", "fabric", "fit", "length", "pattern", "palette", "waistline"],
    "dresses":     ["colorFamily", "fabric", "fit", "neckline", "length", "pattern", "palette", "sleeve", "waistline", "silhouette"],
    "outerwear":   ["colorFamily", "fabric", "fit", "length", "pattern", "palette", "layering"],
    "footwear":    ["colorFamily", "palette", "heelType", "shoeStyle"],
    "accessories": ["colorFamily", "palette", "accessory"],
    "bags":        ["colorFamily", "palette", "bagStyle"],
    "jewelry":     ["colorFamily", "palette", "jewelryStyle"],
    "ethnic":      ["colorFamily", "fabric", "fit", "neckline", "pattern", "palette", "embellishment", "ethnicDetail", "sleeve", "length"],
    "jumpsuits":   ["colorFamily", "fabric", "fit", "neckline", "length", "pattern", "palette", "sleeve", "waistline"],
    "swimwear":    ["colorFamily", "pattern", "palette"],
    "scarves_wraps": ["colorFamily", "fabric", "pattern", "palette"],
    "hats":        ["colorFamily", "palette"],
}
 
 
class RuleEvaluator:
 
    def evaluate(self, user_profile: Dict[str, Any], rules: List[Dict]) -> Dict:
        """
        1. Find rules matching user profile
        2. Sum all action scores (deduplicate by attr:value key)
        3. Return ranked recommend/avoid lists
        """
        matched = self._match(user_profile, rules)
        score_map, source_map = self._aggregate(matched)
 
        recommend, avoid = [], []
        for key, score in score_map.items():
            attr, value = key.split(":", 1)
            entry = {"attr": attr, "value": value, "score": round(score, 1), "key": key, "sources": source_map.get(key, [])}
            if score > 0:
                recommend.append(entry)
            elif score < 0:
                avoid.append(entry)
 
        recommend.sort(key=lambda x: x["score"], reverse=True)
        avoid.sort(key=lambda x: x["score"])
 
        return {
            "recommend": recommend,
            "avoid": avoid,
            "all_scores": {k: round(v, 1) for k, v in score_map.items()},
            "matched_rules": len(matched),
            "matched_rule_names": [r.get("name", "?") for r in matched],
        }
 
    # ─── BLUEPRINT: Pick strongest signal per category ───
 
    def build_blueprint(self, grouped_attributes: Dict) -> Dict:
        """
        From grouped_attributes, pick the highest scoring value per category.
        Returns blueprint (what to look for) + blacklist (what to avoid).
 
        Input:  {"fit": {"tailored": 3.5, "bodycon": -2}, "neckline": {"v_neck": 2.5}}
        Output: {
            "blueprint": {"fit": {"value": "tailored", "score": 3.5}, ...},
            "blacklist": [{"attr": "fit", "value": "bodycon", "score": -2}, ...]
        }
        """
        blueprint = {}
        blacklist = []
 
        for category, values in grouped_attributes.items():
            if not values:
                continue
            sorted_vals = sorted(values.items(), key=lambda x: x[1], reverse=True)
 
            # Highest positive = best pick
            best_name, best_score = sorted_vals[0]
            if best_score > 0:
                blueprint[category] = {"value": best_name, "score": best_score}
 
            # All negatives = blacklist
            for name, score in sorted_vals:
                if score < 0:
                    blacklist.append({"attr": category, "value": name, "score": score})
 
        return {"blueprint": blueprint, "blacklist": blacklist}
 
    # ─── SCORE PRODUCTS: Category-aware weighted scoring ───
 
    def score_product(self, product: Dict, grouped_attributes: Dict) -> Dict:
        """
        Score a single product against grouped_attributes.
        Only uses attributes relevant to the product's category.
 
        A shoe ignores neckline scores. A top ignores heel_type scores.
        """
        product_cat = product.get("category", "").lower()
        product_tags = set(product.get("tags", []))
 
        # Get which attributes matter for this category
        relevant_attrs = CATEGORY_ATTRIBUTE_MAP.get(product_cat, list(grouped_attributes.keys()))
 
        score = 0.0
        matches = []
        penalties = []
 
        for attr, values in grouped_attributes.items():
            # Skip attributes not relevant for this product category
            if attr not in relevant_attrs:
                continue
 
            for value, weight in values.items():
                if value in product_tags:
                    score += weight
                    if weight > 0:
                        matches.append(f"{attr}:{value} +{weight}")
                    else:
                        penalties.append(f"{attr}:{value} {weight}")
 
        return {
            "product": product.get("name", "Unknown"),
            "category": product_cat,
            "score": round(score, 1),
            "matches": matches,
            "penalties": penalties,
            "tags": list(product_tags),
        }
 
    def score_all_products(self, products: List[Dict], grouped_attributes: Dict) -> List[Dict]:
        """Score all products and return sorted by score (highest first)"""
        scored = [self.score_product(p, grouped_attributes) for p in products]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored
 
    # ─── GENERATE LOOKS: Combine top products into outfits ───
 
    def generate_looks(self, products: List[Dict], grouped_attributes: Dict, num_looks: int = 3) -> List[Dict]:
        """
        Generate complete outfit looks from scored products.
 
        1. Score all products (category-aware)
        2. Group by category (top, bottom, shoes, accessory)
        3. Pick top products from each slot
        4. Combine into complete looks
 
        Returns list of looks, each with slots and total score.
        """
        # Score all products
        scored = [
            {**self.score_product(p, grouped_attributes), **p}
            for p in products
        ]
 
        # Group by category slot
        SLOT_MAP = {
            "tops": "top", "bottoms": "bottom", "dresses": "top",
            "outerwear": "layer", "footwear": "shoes",
            "accessories": "accessory", "bags": "accessory",
            "jewelry": "accessory", "ethnic": "top",
            "jumpsuits": "top", "swimwear": "top",
            "scarves_wraps": "accessory", "hats": "accessory",
        }
 
        slots = {}
        for p in scored:
            slot = SLOT_MAP.get(p.get("category", ""), "other")
            if slot not in slots:
                slots[slot] = []
            slots[slot].append(p)
 
        # Sort each slot by score
        for slot in slots:
            slots[slot].sort(key=lambda x: x["score"], reverse=True)
 
        # Generate looks by picking from each slot
        looks = []
        for i in range(num_looks):
            look = {"items": [], "total_score": 0, "name": f"Look {i + 1}"}
 
            for slot_name in ["top", "bottom", "shoes", "accessory", "layer"]:
                if slot_name in slots and len(slots[slot_name]) > i:
                    item = slots[slot_name][i]
                    look["items"].append({
                        "slot": slot_name,
                        "name": item.get("name", "Unknown"),
                        "category": item.get("category", ""),
                        "score": item.get("score", 0),
                        "matches": item.get("matches", []),
                        "penalties": item.get("penalties", []),
                        "tags": item.get("tags", []),
                        "price": item.get("price", 0),
                    })
                    look["total_score"] += item.get("score", 0)
 
            look["total_score"] = round(look["total_score"], 1)
 
            # Only add looks that have at least 2 items
            if len(look["items"]) >= 2:
                looks.append(look)
 
        # Name the looks based on their character
        look_names = ["Best match", "Smart alternative", "Casual option"]
        for i, look in enumerate(looks):
            if i < len(look_names):
                look["name"] = look_names[i]
 
        return looks
 
    # ─── EXISTING: Rule matching ───
 
    def _match(self, profile: Dict, rules: List[Dict]) -> List[Dict]:
        """Find all active rules whose conditions match the profile"""
        matched = []
        for rule in rules:
            if not rule.get("isActive", True):
                continue
            cond = rule.get("conditions", {})
            clauses = cond.get("clauses", [])
            op = cond.get("operator", "AND")
            if not clauses:
                continue
 
            results = [self._clause_match(profile, c) for c in clauses]
 
            if op == "AND" and all(results):
                matched.append(rule)
            elif op == "OR" and any(results):
                matched.append(rule)
        return matched
 
    def _clause_match(self, profile: Dict, clause: Dict) -> bool:
        """Check if one clause matches the profile"""
        field = clause.get("field", "")
        op = clause.get("op", "IN")
        values = set(clause.get("values", []))
        user_val = profile.get(field)
        if user_val is None:
            return False
        user_set = {user_val} if isinstance(user_val, str) else set(user_val)
 
        if op == "IN":
            return bool(user_set & values)
        elif op == "NOT_IN":
            return not bool(user_set & values)
        elif op == "EQUALS":
            return user_set == values
        elif op == "NOT_EQUALS":
            return user_set != values
        return False
 
    def _aggregate(self, matched: List[Dict]) -> tuple:
        """
        DEDUPLICATION: Sum scores by attr:value key.
        Multiple rules scoring fit:a_line -> one entry, scores added.
        """
        scores: Dict[str, float] = {}
        sources: Dict[str, List[str]] = {}
 
        for rule in matched:
            name = rule.get("name", "?")
            for act in rule.get("actions", []):
                a, v, s = act.get("attr", ""), act.get("value", ""), act.get("score", 0)
                if not a or not v or s == 0:
                    continue
                key = f"{a}:{v}"
                scores[key] = scores.get(key, 0) + s
                sources.setdefault(key, []).append(f"{name} ({'+' if s > 0 else ''}{s})")
 
        return scores, sources
 