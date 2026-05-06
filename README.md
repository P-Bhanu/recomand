# Style Rule Evaluator API

[![Live API](https://img.shields.io/badge/Live%20API-online-brightgreen?style=flat-square)](https://style-rule-evaluator.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

Evaluates user profiles against style rules and generates fashion recommendations.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MongoDB (if local)
mongod

# 3. Run the server
python main.py
# OR
uvicorn main:app --reload --port 8000

# 4. Open docs
# http://localhost:8000/docs

# 5. Load seed data (rules + sample products)
curl -X POST http://localhost:8000/seed
```

## Project Structure

```
evaluator/
├── main.py          ← FastAPI server, all endpoints
├── evaluator.py     ← Core logic: rule matching + score deduplication
├── database.py      ← MongoDB connection, CRUD, indexes
├── models.py        ← Pydantic request/response schemas
├── seed_data.py     ← 18 pre-filled rules + 15 sample products
├── requirements.txt ← Python dependencies
├── .env             ← MongoDB connection string
└── README.md        ← This file
```

## API Endpoints

### Rules (used by Rule Builder UI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rules` | Create a rule |
| GET | `/rules` | List all rules |
| GET | `/rules/{id}` | Get one rule |
| PUT | `/rules/{id}` | Update a rule |
| DELETE | `/rules/{id}` | Delete a rule |
| PATCH | `/rules/{id}/toggle` | Toggle active/inactive |

### Evaluation (core)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluate` | Evaluate user → ranked attributes (saves to DB) |
| POST | `/evaluate/preview` | Same but doesn't save |
| POST | `/suggest` | Full pipeline: evaluate → find matching products |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | Rule/evaluation counts |
| POST | `/seed` | Load seed rules + products |

## Example: Evaluate a User

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "bodyType": "oval",
    "skinTone": "dark",
    "occasion": "wedding",
    "stylePref": "romantic"
  }'
```

Response:
```json
{
  "recommend": [
    {"attr": "palette", "value": "jewel", "score": 3.5, "sources": ["Dark skin (+2)", "Wedding (+1.5)"]},
    {"attr": "fabric", "value": "lace", "score": 2.0, "sources": ["Romantic (+2)"]},
    {"attr": "fit", "value": "a_line", "score": 2.0, "sources": ["Oval (+2)"]},
    {"attr": "neckline", "value": "v_neck", "score": 2.0, "sources": ["Oval (+2)"]}
  ],
  "avoid": [
    {"attr": "colorFamily", "value": "white", "score": -0.5, "sources": ["Dark skin (+2.5)", "Wedding (-3)"]},
    {"attr": "fit", "value": "bodycon", "score": -3.0, "sources": ["Oval (-3)"]},
    {"attr": "fabric", "value": "leather", "score": -2.0, "sources": ["Romantic (-2)"]}
  ],
  "matched_rules": 4,
  "matched_rule_names": ["Oval", "Dark skin", "Wedding", "Romantic"]
}
```

## How Deduplication Works

**3 layers of protection:**

1. **Evaluator HashMap** — Same `attr:value` from multiple rules → scores SUMMED, not duplicated
2. **MongoDB upsert** — Same user profile → old evaluation REPLACED, not duplicated
3. **TTL index** — Old evaluations auto-delete after 24 hours

## MongoDB Atlas Setup

1. Go to https://cloud.mongodb.com (free tier)
2. Create a cluster
3. Get connection string
4. Update `.env`:
```
MONGO_URI=mongodb+srv://youruser:yourpass@cluster0.xxxxx.mongodb.net
```

## Connect Rule Builder Frontend

Update the Rule Builder to save/load rules via API instead of localStorage:

```javascript
// Instead of window.storage.set(...)
const response = await fetch('http://localhost:8000/rules', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(rule)
});
```
