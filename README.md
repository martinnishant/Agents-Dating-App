# Morrow — Agent Matching Studio

A small full-stack prototype using a **fictional 25-person cohort**. It includes a responsive website and a Python API for profile persistence, match ranking, and simulated agent dates.

## Run locally

Requires Python 3.10+; no third-party packages are needed.

```bash
python server.py
```

Open http://localhost:4173. The Python process serves the website and API from one origin.

## Backend API

Implemented in `server.py` using Python's standard library:

- `GET /api/health` — health check.
- `GET /api/people` — read the seeded cohort.
- `PUT /api/people` — save profile changes to `data/people.json` (local mode only).
- `POST /api/analyze` — compute ranked matches and simulated agent-date dialogue.

The app calls the Python API when available. If opened on a static host such as GitHub Pages, it uses browser localStorage and its JavaScript fallback instead.

## Matching algorithm

A transparent weighted heuristic, implemented server-side in Python:

- Shared interests: **40%** (Jaccard overlap of entered interest tags)
- Similar explicitly stated relationship intention: **30%**
- Shared stated values: **20%** (Jaccard overlap)
- Same city: **10%**

The API returns scores, per-person ranked shortlists, human-readable reasons, and a template-generated conversation for each unique top pairing. The dialogue is fictional template output—not an LLM, not an actual conversation, and not a prediction of real-world chemistry.

## Deploy the full-stack demo

A Render Blueprint is included in `render.yaml`:

1. Push the project files to a public GitHub repository.
2. In Render, create a new **Blueprint** and connect that repository.
3. Deploy the `morrow-showcase` service described by `render.yaml`.

The public service is configured read-only (`MORROW_READ_ONLY=1`): profile edits stay in each visitor's browser, while the backend serves the synthetic seed data and calculates analysis. This avoids an unauthenticated public write endpoint. The in-app local preview can save to the JSON file.

## Data & limitations

- All 25 demo profiles and source excerpts are synthetic; no real people or social profiles are represented.
- No LinkedIn/Instagram scraping, Apify calls, external LLM, or outbound messages are included.
- `data/people.json` is fictional sample data, committed so the hosted backend starts with a cohort.
- This is a demo design, not a production dating service. Before using real participants, obtain appropriate consent and add authentication, a database, access controls, data-retention handling, and a compliant data-collection process.

## Files

- `index.html` — frontend.
- `server.py` — Python backend and match engine.
- `data/people.json` — fictional seed data.
- `render.yaml` — full-stack deployment configuration.
- `requirements.txt` — no external Python packages required.
- `morrow-template.csv` — profile CSV template.
