# LocationReasoner Demos

Two interactive site selection demos built on H3 hexagonal zones. Each lets you type a natural language query, generates a JSON constraint spec, evaluates it against ground truth, and shows zone rankings when no perfect match exists.

- **Boston** — 255 zones, 48 features (SafeGraph data), port 5003
- **Abu Dhabi** — 471 zones, 27 features (OpenStreetMap data), port 5002

## Setup

```bash
pip install -r requirements.txt
```

You need at least one API key:

```bash
export OPENAI_API_KEY="sk-..."
export DEEPSEEK_API_KEY="sk-..."   # recommended — used for LLM ranking
```

## Running

**Boston:**
```bash
cd boston
PYTHONPATH=. python app.py
# Open http://localhost:5003
```

**Abu Dhabi:**
```bash
cd abu_dhabi
PYTHONPATH=. python app.py
# Open http://localhost:5002
```

## How it works

1. Type a natural language query (e.g. "Find zones with 2+ pharmacies within 800m of a mall")
2. The system generates a JSON constraint spec via LLM
3. Ground truth evaluation checks which zones satisfy all constraints exactly
4. If no zones match, a partial-satisfaction ranking scores every zone 0–100%
5. Toggle between **Rank by Formula** (deterministic scoring) and **Rank by LLM** (DeepSeek reranking with trade-off reasoning)
