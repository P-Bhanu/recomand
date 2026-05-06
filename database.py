"""
Database Module
===============
MongoDB with:
  - Atlas Vector Search ($vectorSearch ANN) for neural path
  - Tag + category index pre-filter for symbolic / looks path
  - Deduplication + 24-h TTL on evaluations
  - Paginated batch embedding — never OOM at 777k products
 
Atlas Vector Search setup (one-time, in MongoDB Atlas UI):
  Collection : products
  Index name : embedding_index   (or set env VECTOR_INDEX_NAME)
  Field      : embedding
  Type       : knnVector
  Dimensions : 384
  Similarity : cosine
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
 
logger = logging.getLogger(__name__)
 
MONGO_URI          = os.getenv("MONGO_URI",          "mongodb://localhost:27017")
DB_NAME            = os.getenv("DB_NAME",            "style_evaluator")
VECTOR_INDEX_NAME  = os.getenv("VECTOR_INDEX_NAME",  "embedding_index")
 
 
class Database:
    def __init__(self):
        self.client      = AsyncIOMotorClient(MONGO_URI)
        self.db          = self.client[DB_NAME]
        self.rules       = self.db["rules"]
        self.evaluations = self.db["extracted_attributes"]
        self.products    = self.db["products"]
        self._idx        = False
 
    async def _ensure_indexes(self):
        if self._idx:
            return
        await self.rules.create_index("isActive")
        await self.rules.create_index("id", unique=True, sparse=True)
        await self.evaluations.create_index("userId", unique=True)
        await self.evaluations.create_index("expiresAt", expireAfterSeconds=0)
        await self.products.create_index([("tags",     1)])
        await self.products.create_index([("category", 1)])
        await self.products.create_index([("category", 1), ("tags", 1)])
        self._idx = True
 
    async def ping(self) -> bool:
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False
 
    # ── Rules ──────────────────────────────────────────────────────────
    async def create_rule(self, data: Dict) -> Dict:
        await self._ensure_indexes()
        data["createdAt"] = data["updatedAt"] = datetime.utcnow()
        r = await self.rules.insert_one(data)
        data["_id"] = str(r.inserted_id)
        return self._ser(data)
 
    async def get_rules(self, field=None, is_active=None) -> List[Dict]:
        await self._ensure_indexes()
        q = {}
        if is_active is not None: q["isActive"] = is_active
        if field:                 q["conditions.clauses.field"] = field
        return [self._ser(r) for r in
                await self.rules.find(q).sort("priority", -1).to_list(1000)]
 
    async def get_rule(self, rid: str):
        await self._ensure_indexes()
        r = await self.rules.find_one({"id": rid})
        if not r:
            try:   r = await self.rules.find_one({"_id": ObjectId(rid)})
            except Exception: pass
        return self._ser(r) if r else None
 
    async def update_rule(self, rid: str, data: Dict):
        await self._ensure_indexes()
        data["updatedAt"] = datetime.utcnow()
        r = await self.rules.find_one_and_update(
            {"id": rid}, {"$set": data}, return_document=True)
        return self._ser(r) if r else None
 
    async def delete_rule(self, rid: str) -> bool:
        await self._ensure_indexes()
        r = await self.rules.delete_one({"id": rid})
        return r.deleted_count > 0
 
    async def toggle_rule(self, rid: str):
        rule = await self.get_rule(rid)
        if not rule: return None
        return await self.update_rule(rid, {"isActive": not rule.get("isActive", True)})
 
    async def count_rules(self, is_active=None) -> int:
        q = {"isActive": is_active} if is_active is not None else {}
        return await self.rules.count_documents(q)
 
    # ── Evaluations ────────────────────────────────────────────────────
    async def save_evaluation(self, profile: Dict, result: Dict) -> Dict:
        await self._ensure_indexes()
        uid     = self._pid(profile)
        grouped = {}
        for item in result.get("recommend", []) + result.get("avoid", []):
            attr  = item.get("attr",  "")
            value = item.get("value", "")
            score = item.get("score", 0)
            if attr not in grouped:
                grouped[attr] = {}
            grouped[attr][value] = score
 
        doc = {
            "userId":             uid,
            "userProfile":        profile,
            "grouped_attributes": grouped,
            "attributes":         [{"key": i["key"], "score": i["score"]}
                                    for i in result.get("recommend", []) + result.get("avoid", [])],
            "recommend":          result.get("recommend", []),
            "avoid":              result.get("avoid",    []),
            "matchedRules":       result.get("matched_rules",      0),
            "matchedRuleNames":   result.get("matched_rule_names", []),
            "evaluatedAt":        datetime.utcnow(),
            "expiresAt":          datetime.utcnow() + timedelta(hours=24),
        }
        await self.evaluations.update_one({"userId": uid}, {"$set": doc}, upsert=True)
        return doc
 
    async def get_evaluation(self, profile: Dict):
        uid = self._pid(profile)
        doc = await self.evaluations.find_one({"userId": uid})
        return self._ser(doc) if doc else None
 
    async def count_evaluations(self) -> int:
        return await self.evaluations.count_documents({})
 
    # ── Products: tag search (used by /suggest) ────────────────────────
    async def search_products(self, include: List[str],
                              exclude: List[str] = None, limit=20) -> List[Dict]:
        await self._ensure_indexes()
        if not include: return []
        q = {"tags": {"$in": include}}
        if exclude: q["tags"]["$nin"] = exclude
        prods = await self.products.find(q).limit(limit).to_list(limit)
        inc, exc = set(include), set(exclude or [])
        for p in prods:
            t = set(p.get("tags", []))
            p["relevance"] = len(t & inc) - len(t & exc) * 2
        prods.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return [self._ser(p) for p in prods]
 
    # ── Products: candidate fetch for /looks (replaces get_all_products) ─
    async def get_candidate_products(
        self,
        positive_tags:  List[str],
        negative_tags:  List[str] = None,
        category:       str       = None,
        limit:          int       = 300,
    ) -> List[Dict]:
        """Tag+category index cuts 777k to <=300 candidates. Never full scan."""
        await self._ensure_indexes()
        if not positive_tags:
            return []
        q: Dict = {"tags": {"$in": positive_tags}}
        if negative_tags:
            q["tags"]["$nin"] = negative_tags
        if category:
            q["category"] = category
        cursor = self.products.find(
            q, {"name": 1, "category": 1, "tags": 1, "price": 1, "_id": 1}
        ).limit(limit)
        docs = []
        async for doc in cursor:
            d = dict(doc)
            if "_id" in d: d["_id"] = str(d["_id"])
            docs.append(d)
        return docs
 
    # ── Atlas Vector Search ────────────────────────────────────────────
    async def vector_search(
        self,
        query_vector:    List[float],
        num_candidates:  int = 1000,
        limit:           int = 50,
        category_filter: str = None,
    ) -> List[Dict]:
        """Atlas $vectorSearch ANN. Returns [] if Atlas not available."""
        pipeline = [
            {
                "$vectorSearch": {
                    "index":         VECTOR_INDEX_NAME,
                    "path":          "embedding",
                    "queryVector":   query_vector,
                    "numCandidates": num_candidates,
                    "limit":         limit,
                }
            },
            {"$addFields": {"vector_score": {"$meta": "vectorSearchScore"}}},
            *(
                [{"$match": {"category": category_filter}}]
                if category_filter else []
            ),
            {
                "$project": {
                    "name": 1, "category": 1, "tags": 1,
                    "price": 1, "vector_score": 1, "_id": 1,
                }
            },
        ]
        try:
            results = []
            async for doc in self.products.aggregate(pipeline):
                d = dict(doc)
                if "_id" in d: d["_id"] = str(d["_id"])
                results.append(d)
            logger.info("Atlas vector search returned %d results", len(results))
            return results
        except Exception as exc:
            logger.warning("Atlas Vector Search unavailable (%s). Using fallback.", exc)
            return []
 
    async def vector_search_with_tag_boost(
        self,
        query_vector:   List[float],
        positive_tags:  List[str],
        negative_tags:  List[str] = None,
        num_candidates: int = 1500,
        limit:          int = 100,
    ) -> List[Dict]:
        """ANN + tag-boost + sort — entirely inside MongoDB. Zero Python loops."""
        neg   = negative_tags or []
        n_pos = max(len(positive_tags), 1)
        n_neg = max(len(neg),           1)
        pipeline = [
            {
                "$vectorSearch": {
                    "index":         VECTOR_INDEX_NAME,
                    "path":          "embedding",
                    "queryVector":   query_vector,
                    "numCandidates": num_candidates,
                    "limit":         limit * 3,
                }
            },
            {"$addFields": {"vector_score": {"$meta": "vectorSearchScore"}}},
            {
                "$addFields": {
                    "tag_hits":   {"$size": {"$ifNull": [{"$setIntersection": ["$tags", positive_tags]}, []]}},
                    "tag_misses": {"$size": {"$ifNull": [{"$setIntersection": ["$tags", neg]},           []]}},
                }
            },
            {
                "$addFields": {
                    "boosted_score": {
                        "$subtract": [
                            {"$add": [
                                {"$multiply": ["$vector_score", 0.6]},
                                {"$multiply": [{"$divide": ["$tag_hits",  n_pos]}, 0.3]},
                            ]},
                            {"$multiply": [{"$divide": ["$tag_misses", n_neg]}, 0.1]},
                        ]
                    }
                }
            },
            {"$sort":  {"boosted_score": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "name": 1, "category": 1, "tags": 1, "price": 1,
                    "vector_score": 1, "boosted_score": 1, "tag_hits": 1, "_id": 1,
                }
            },
        ]
        try:
            results = []
            async for doc in self.products.aggregate(pipeline):
                d = dict(doc)
                if "_id" in d: d["_id"] = str(d["_id"])
                results.append(d)
            return results
        except Exception as exc:
            logger.warning("vector_search_with_tag_boost failed (%s). Using fallback.", exc)
            return []
 
    # ── Products: CRUD ─────────────────────────────────────────────────
    async def get_all_products(self) -> List[Dict]:
        """Only for seeding/admin. Never call in hot paths at 777k scale."""
        logger.warning("get_all_products() called — unsafe for large catalogs")
        products = []
        async for doc in self.products.find({}):
            d = dict(doc)
            if "_id" in d: d["_id"] = str(d["_id"])
            products.append(d)
        return products
 
    async def add_product(self, product: Dict) -> Dict:
        await self._ensure_indexes()
        product["createdAt"] = datetime.utcnow()
        result = await self.products.insert_one(product)
        product["_id"] = str(result.inserted_id)
        return self._ser(product)
 
    async def store_product_embedding(self, product_id: str,
                                      embedding: List[float], embed_text: str):
        await self.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"embedding": embedding, "embed_text": embed_text,
                      "embeddedAt": datetime.utcnow()}},
        )
 
    async def get_products_without_embeddings(
        self, batch_size: int = 100, skip: int = 0
    ) -> List[Dict]:
        """Paginated — call in a loop. Never OOM at 777k."""
        cursor = (
            self.products
            .find({"embedding": {"$exists": False}},
                  {"name": 1, "tags": 1, "category": 1, "_id": 1})
            .skip(skip)
            .limit(batch_size)
        )
        docs = []
        async for doc in cursor:
            d = dict(doc)
            if "_id" in d: d["_id"] = str(d["_id"])
            docs.append(d)
        return docs
 
    async def count_embedded_products(self) -> int:
        return await self.products.count_documents({"embedding": {"$exists": True}})
 
    async def count_unembedded_products(self) -> int:
        return await self.products.count_documents({"embedding": {"$exists": False}})
 
    async def get_products_with_embeddings(self) -> List[Dict]:
        """Kept for backward-compat only."""
        products = []
        async for doc in self.products.find({"embedding": {"$exists": True}}):
            d = dict(doc)
            if "_id" in d: d["_id"] = str(d["_id"])
            products.append(d)
        return products
 
    # ── Seed ───────────────────────────────────────────────────────────
    async def seed_rules(self, rules):
        await self._ensure_indexes()
        if await self.count_rules() > 0:
            return {"message": "Rules exist, skipped"}
        for r in rules:
            r["createdAt"] = r["updatedAt"] = datetime.utcnow()
        res = await self.rules.insert_many(rules)
        return {"inserted": len(res.inserted_ids)}
 
    async def seed_products(self, products):
        await self._ensure_indexes()
        if await self.products.count_documents({}) > 0:
            return {"message": "Products exist, skipped"}
        for p in products:
            p["createdAt"] = datetime.utcnow()
        res = await self.products.insert_many(products)
        return {"inserted": len(res.inserted_ids)}
 
    # ── Helpers ────────────────────────────────────────────────────────
    def _pid(self, p: Dict) -> str:
        return "|".join(f"{k}:{p[k]}" for k in sorted(p) if p[k])
 
    def _ser(self, d):
        if not d: return None
        d = dict(d)
        if "_id" in d: d["_id"] = str(d["_id"])
        for k, v in d.items():
            if isinstance(v, datetime): d[k] = v.isoformat()
        return d