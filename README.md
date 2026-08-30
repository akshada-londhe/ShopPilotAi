# 🛒 ShopPilot AI

> ## Stop scrolling.
> You just spent 40 minutes across 11 tabs comparing products, and you still aren't sure you picked the right one. ShopPilot AI turns that into one sentence and about 20 seconds. Tell it what you want and your budget. It searches the live web, verifies the results against your requirements, and hands you one clear pick with the real price and the reason it won, backed by a source link you can open.
>
> One query. Real products. A verified answer. No 11 tabs, no ads, no doomscrolling the reviews.

---

## ✨ What Does It Do?

You type:

> *"Find me a laptop under ₹80,000 for programming"*

ShopPilot AI:

1. 🧠 **Understands** your query — intent, budget, hard requirements, preferences.
2. ⚡ **Checks its memory first** — if you (or anyone) asked the same thing recently and the answer is still fresh, it replies instantly from its vector store, with no web search at all.
3. 🌐 **Searches the live web** (via Tavily) when memory has nothing fresh.
4. 📦 **Extracts real product data** — name, price, specs — from actual listing pages.
5. 🎯 **Filters strictly** — over-budget items are dropped, and phone *cases* never get returned when you asked for a *phone*.
6. 🧑‍⚖️ **Reviews itself** — an AI critic scores the results and retries with better searches if they aren't good enough.
7. 💬 **Explains the winner** — a plain-English recommendation that says why this product beat the alternatives, with source links.

Vague query? It asks one clarifying question first. Signed in? Every search is saved to your history and you can heart products to your saved list.

---

## 🏗️ How It Works

```
You type a query
       │
       ▼
  🧹 Normalizer          → Extracts intent, budget, constraints, preferences
       │
       ▼
  ⚡ Semantic Memory     → Same/near-identical query asked before AND still fresh?
       │                    ├─ HIT  → serve the stored answer instantly (no web search)
       │                    └─ MISS → run the full pipeline below
       ▼
  🔍 Query Generator     → Turns your intent into targeted web search queries
       │
       ▼
  🌐 Tavily Search       → Searches the live web for product pages
       │
       ▼
  🧼 Sanitizer           → Strips prompt-injection text from scraped content
       │
       ▼
  📦 Product Extractor   → Pulls structured data (name, price, specs) + keeps the raw title
       │
       ▼
  🎯 Constraint Matcher  → Drops over-budget items and accessories (case/cover/cable);
       │                    prefers products that carry a real price
       ▼
  🧑‍⚖️ Critic (LangGraph)  → Scores quality; loops back to search again if weak (max 3 tries)
       │
       ▼
  ✍️ Synthesizer         → Writes why the top pick wins vs the alternatives, with sources
       │
       ▼
  📡 SSE Stream          → Progress and results appear live as they happen
       │
       ▼
  💾 Recorded to memory  → The verified answer is embedded and stored for next time
```

The critic retry loop is orchestrated with **LangGraph**; every other stage is a **LangChain LCEL** chain.

### ⚡ Semantic Memory (the RAG story)

The first time a query runs, the finished, verified response (products + synthesis + verdict) is embedded by the raw query text and stored in a dedicated ChromaDB collection (`query_memory`). Ask the same thing again and, if the stored answer is still within its data's TTL (price data expires in 6 hours), it is served straight from the vector store — no Tavily, no pipeline, and the UI tells you: *"⚡ Answered from memory — no live web search used."* The similarity threshold is configurable (`MEMORY_SIMILARITY_THRESHOLD`, default `0.95` for near-exact recall).

---

## 🤖 AI Providers

Each pipeline stage picks its provider from `backend/app/config.py`. Out of the box every stage uses **OpenRouter**, with **Groq** available as a drop-in for the fast stages if you set a Groq key and switch the stage in config.

| Pipeline Stage        | Default Provider |
|-----------------------|------------------|
| Normalizer            | OpenRouter       |
| Query Generator       | OpenRouter       |
| Product Extractor     | OpenRouter       |
| Preference Scorer     | OpenRouter       |
| Critic / Reviewer     | OpenRouter       |
| Synthesizer           | OpenRouter       |
| Synthesizer Fallback  | OpenRouter       |

Local embeddings use ChromaDB's built-in `DefaultEmbeddingFunction` — no paid embedding API.

---

## 🚀 Quick Start

### What You Need

- **Python 3.11+** (backend)
- **Node.js + npm** (frontend)
- API keys:
  - [OpenRouter](https://openrouter.ai) — many free models
  - [Tavily](https://tavily.com) — free tier for web search
  - [Groq](https://console.groq.com) — optional, for the fast stages
  - [Langfuse](https://cloud.langfuse.com) — optional, for tracing

### Step 1 — Backend env

```bash
cd backend
cp .env.example .env
```

Fill in `backend/.env`:

```env
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
TAVILY_API_KEY=your-tavily-key
BACKEND_API_KEY=any-random-secret-you-make-up
CHROMA_PERSIST_DIR=chroma_groq

# Optional
GROQ_API_KEY=your-groq-key
JWT_SECRET=set-a-long-random-value-for-user-auth
MEMORY_SIMILARITY_THRESHOLD=0.95
```

### Step 2 — Frontend env

The browser never sees the backend key. The Next.js API routes proxy to the backend using **server-only** vars. Create `frontend/.env.local`:

```env
SHOPPILOT_BACKEND_URL=http://localhost:8000
SHOPPILOT_API_KEY=same-value-as-BACKEND_API_KEY-above
```

> ⚠️ Never commit your `.env` files. They hold secrets.

### Step 3 — Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Step 4 — Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### Step 5 — Open the app

Go to **[http://localhost:3000](http://localhost:3000)** and search. 🎉

---

## 🩺 Health Check

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

---

## 🔌 API Endpoints

| Method | Endpoint            | Purpose                                             |
|--------|---------------------|-----------------------------------------------------|
| POST   | `/api/v1/search`    | Run a search; streams progress + result over SSE    |
| GET    | `/api/v1/history`   | Signed-in user's search history (newest first)      |
| GET    | `/api/v1/saved`     | Signed-in user's saved products                     |
| POST   | `/api/v1/saved`     | Save a product                                      |
| DELETE | `/api/v1/saved`     | Remove a saved product                              |
| POST   | `/auth/signup`      | Create an account, returns a JWT                    |
| POST   | `/auth/signin`      | Sign in, returns a JWT                              |
| GET    | `/auth/me`          | Current user from the JWT                           |
| GET    | `/health`           | Liveness check                                      |

Search and saved/history endpoints require the `X-API-Key` header (added by the frontend proxy). Per-user endpoints also read a `Bearer` JWT.

---

## 📁 Project Structure

```
ShopPilot-AI/
├── backend/
│   ├── app/
│   │   ├── chains/          ← LCEL stages: normalizer, generator, extractor,
│   │   │                       matcher, critic, synthesizer
│   │   ├── graph/           ← LangGraph critic retry loop
│   │   ├── models/          ← Pydantic models (query, product, critic)
│   │   ├── retrieval/       ← Tavily client, sanitizer, product cache,
│   │   │                       memory.py (semantic memory)
│   │   ├── routers/         ← Auth routes
│   │   ├── auth_users.py    ← User store (ChromaDB)
│   │   ├── user_data.py     ← Saved items + search history
│   │   ├── config.py        ← Per-stage provider/model settings
│   │   ├── llm_factory.py   ← Builds LLM clients per stage
│   │   └── main.py          ← FastAPI app, search endpoint, memory wiring
│   └── tests/
│
└── frontend/
    ├── app/
    │   ├── api/             ← Server-only proxy routes (hold the API key)
    │   ├── dashboard/       ← Activity hub (searches, saved, counts)
    │   ├── history/         ← Search history
    │   ├── saved/           ← Saved items
    │   └── search/          ← Search + results
    ├── components/          ← UI (results page, cards, clarification)
    └── lib/                 ← Types, SSE client, auth client
```

---

## ⚡ Running Tests

Backend:

```bash
cd backend
.venv/bin/python -m pytest -q
```

Frontend typecheck:

```bash
cd frontend
npm run typecheck
```

---

## 🔧 Troubleshooting

**Search returns "closest available" or few results**
- Check your **Tavily** key. Try a more specific query (category + budget).
- Watch the backend terminal for provider errors.

**Provider / rate-limit errors**
- Verify your **OpenRouter** (and optional **Groq**) keys.
- Free tiers rate-limit; wait a moment and retry.

**A product link opens a different product**
- Fixed: Amazon sponsored-ad redirect URLs are now unwrapped to the real product ASIN before display.

**Backend "running" but not responding**
- Give it a few seconds to bind the port, then re-check `/health`. If the port is stuck, stop the old process and restart on `:8000`.

**Starting fresh**
- Delete the ChromaDB directory (`backend/chroma_groq`) to wipe users, saved items, history, product cache, and semantic memory. Restart the backend and it recreates an empty store.

---

## ⚠️ Known Limitations

- Result quality depends on what Tavily surfaces; niche products may not appear.
- Prices are shown only when present on the scraped page — never fabricated. If nothing priced is found, the best match may show "Price unavailable."
- ChromaDB is local; not a production datastore as-is. On Railway, data persists only with a mounted volume.
- Free-tier API quotas can slow things down under load.

---

## 🛠️ Tech Stack

| Layer      | Technology                                            |
|------------|-------------------------------------------------------|
| Frontend   | Next.js 15, TypeScript, Tailwind CSS                  |
| Backend    | Python, FastAPI, LangChain (LCEL), LangGraph          |
| AI Models  | OpenRouter (default), Groq (optional fast stages)     |
| Search     | Tavily Web Search API                                 |
| Vector DB  | ChromaDB — product cache, semantic memory, user data  |
| Auth       | JWT (per-user history + saved items)                  |
| Streaming  | Server-Sent Events (SSE)                              |
| Tracing    | Langfuse (optional)                                   |

---

<div align="center">
  <sub>Built with LangGraph + FastAPI + Next.js</sub>
</div>
