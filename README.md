# Morrow — Agent Matching Studio

**Live demo:** [https://morrow-showcase.onrender.com](https://morrow-showcase.onrender.com)  
**API health:** [https://morrow-showcase.onrender.com/api/health](https://morrow-showcase.onrender.com/api/health)

Morrow is a full-stack prototype for a fictional, consent-first agent-matching demo. It has a responsive browser UI and a Python API that calculates explainable match rankings and template-generated agent dates for a 25-person synthetic cohort.

## Try the live demo

1. Open the live demo above.
2. Open a sample profile to inspect its fictional interests, stated intention, values, and evidence notes.
3. Select **Agent dates** and run the simulated conversations.
4. Select **Rankings** to compare each person’s best matches and the reasons for each score.
5. If the cohort count is not 25, choose **Reload showcase data**.

The live backend is configured read-only. Any edits made in the public demo are saved only in that visitor’s browser.

## Run locally

Requires Python 3.10+; no third-party packages are required.

```bash
python3 server.py
```

Open http://localhost:4173. The Python server serves both the website and API from one origin. Check the API at http://localhost:4173/api/health.

## Backend API

Implemented in `server.py` using Python’s standard library:

- `GET /api/health` — service health check.
- `GET /api/people` — load the synthetic cohort.
- `PUT /api/people` — save profile changes in local mode; disabled on the public Render deployment.
- `POST /api/analyze` — calculate rankings, match reasons, and simulated agent-date dialogue.

## Matching algorithm

A transparent weighted heuristic, calculated server-side in Python:

- Shared interests: **40%** (Jaccard overlap of entered interest tags)
- Similar explicitly stated relationship intention: **30%**
- Shared stated values: **20%** (Jaccard overlap)
- Same city: **10%**

The API returns scores, a ranked shortlist for every profile, human-readable reasons, and a template-generated conversation for each unique top pairing. Dialogue is fictional template output—not an LLM, an actual conversation, or a prediction of real-world chemistry.

## Deployment

The repository includes a Render Blueprint in `render.yaml`. The live demo is deployed from the public GitHub repository `martinnishant/Agents-Dating-App`. Render runs the Python service with `MORROW_READ_ONLY=1` so public visitors cannot overwrite the shared seed data.

## Data and limitations

- All 25 demo personas and source excerpts are synthetic. They are not real people and do not represent scraped social profiles.
- The app does not scrape LinkedIn or Instagram, call Apify or an external LLM, bypass access controls, or send messages.
- The project is a demonstration, not a production dating service. Using real participants would require appropriate consent, secure authentication, access controls, and a compliant data-retention process.

## Project files

- `index.html` — browser UI.
- `server.py` — Python API and match engine.
- `data/people.json` — fictional seed data.
- `render.yaml` — Render deployment configuration.
- `requirements.txt` — no external Python packages required.
- `morrow-template.csv` — profile CSV template.
