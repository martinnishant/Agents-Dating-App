from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "people.json"


def load_people():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_people(people):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(people, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_FILE)


def tokens(value):
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").split(",")
    return {re.sub(r"\s+", " ", str(x).strip().lower()) for x in raw if str(x).strip()}


def intention_class(value):
    v = str(value or "").lower()
    if any(w in v for w in ("long-term", "long term", "committed", "life partner", "intentional", "serious")):
        return "serious"
    if any(w in v for w in ("casual", "short-term", "short term", "explore")):
        return "casual"
    return "unspecified"


def compare(a, b):
    ai, bi = tokens(a.get("interests")), tokens(b.get("interests"))
    av, bv = tokens(a.get("values")), tokens(b.get("values"))
    shared_i, shared_v = sorted(ai & bi), sorted(av & bv)
    union_i, union_v = ai | bi, av | bv
    interest_overlap = len(shared_i) / len(union_i) if union_i else 0.30
    value_overlap = len(shared_v) / len(union_v) if union_v else 0.30
    ca, cb = intention_class(a.get("wants")), intention_class(b.get("wants"))
    intent_fit = 0.86 if ca != "unspecified" and ca == cb else (0.53 if ca == "unspecified" or cb == "unspecified" else 0.35)
    city_fit = 1.0 if a.get("city") and b.get("city") and str(a["city"]).strip().lower() == str(b["city"]).strip().lower() else 0.48
    score = round(40 * (0.25 + 0.75 * interest_overlap) + 30 * intent_fit + 20 * (0.30 + 0.70 * value_overlap) + 10 * city_fit)
    reasons = []
    if shared_i:
        reasons.append("shared interests: " + ", ".join(shared_i[:3]))
    if intent_fit > 0.70:
        reasons.append("similar stated relationship intentions")
    if shared_v:
        reasons.append("overlapping stated values: " + ", ".join(shared_v[:2]))
    if city_fit == 1.0:
        reasons.append("same city")
    if not reasons:
        reasons.append("a useful contrast in interests and perspective")
    return {"score": score, "reasons": reasons, "shared_interests": shared_i, "shared_values": shared_v}


def analyze(people):
    by_id = {str(p.get("id")): p for p in people}
    rankings = {}
    for person in people:
        pid = str(person.get("id"))
        ranked = []
        for other in people:
            if str(other.get("id")) == pid:
                continue
            result = compare(person, other)
            ranked.append({"id": str(other.get("id")), "name": other.get("name", "Participant"), **result})
        rankings[pid] = sorted(ranked, key=lambda x: (-x["score"], x["name"]))

    seen = set()
    dates = []
    for person in people:
        pid = str(person.get("id"))
        picks = rankings.get(pid, [])
        if not picks:
            continue
        top = picks[0]
        other_id = top["id"]
        pair_key = tuple(sorted((pid, other_id)))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        other = by_id[other_id]
        interest = (top["shared_interests"] or ["trying something new"])[0]
        role = person.get("role") or "your work"
        response_interest = (top["shared_interests"] or tokens(other.get("interests")) or ["curiosity"])
        response_interest = sorted(response_interest)[0] if isinstance(response_interest, set) else response_interest[0]
        values = sorted(tokens(person.get("values")))
        value = values[0] if values else "openness"
        dates.append({
            "person_id": pid, "person_name": person.get("name", "Participant"),
            "match_id": other_id, "match_name": other.get("name", "Participant"),
            "score": top["score"], "reasons": top["reasons"],
            "opening": f"I noticed {interest} on both of your profiles. What do you enjoy most about it?",
            "reply": f"I like that it gives us an easy way to connect. I’d also be curious to hear more about {person.get('name', 'them')}'s {role} and what inspires it.",
            "comparison": f"The strongest evidence is {('; '.join(top['reasons']))}. {person.get('name', 'This person')} has publicly stated an interest in {value}; a good next question is what each person wants from a relationship."
        })
    dates.sort(key=lambda x: (-x["score"], x["person_name"], x["match_name"]))
    return {"rankings": rankings, "dates": dates, "algorithm": {
        "weights": {"interests": 40, "stated_intentions": 30, "stated_values": 20, "same_city": 10},
        "note": "Transparent heuristic for a fictional demo; not a prediction of real compatibility."
    }, "generated_at": datetime.now(timezone.utc).isoformat()}


class Handler(SimpleHTTPRequestHandler):
    server_version = "MorrowDemo/1.0"

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 2_000_000:
                raise ValueError("Payload too large (2 MB limit)")
            return json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Expected a valid JSON request body") from exc

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.send_json(200, {"ok": True, "service": "Morrow Python API", "storage": "data/people.json"})
        if path == "/api/people":
            return self.send_json(200, {"people": load_people()})
        return super().do_GET()

    def do_PUT(self):
        if urlparse(self.path).path != "/api/people":
            return self.send_json(404, {"error": "Not found"})
        if os.environ.get("MORROW_READ_ONLY", "0").lower() in ("1", "true", "yes"):
            return self.send_json(403, {"error": "Public demo is read-only; edits stay in this browser."})
        try:
            payload = self.read_body()
            people = payload.get("people") if isinstance(payload, dict) else payload
            if not isinstance(people, list) or len(people) > 100:
                return self.send_json(400, {"error": "Send a list of 1–100 profile objects"})
            cleaned = []
            for person in people:
                if not isinstance(person, dict) or not str(person.get("name", "")).strip():
                    continue
                cleaned.append({k: person.get(k, "") for k in ("id", "name", "role", "city", "linkedin", "instagram", "interests", "wants", "values", "notes", "demo")})
            save_people(cleaned)
            return self.send_json(200, {"ok": True, "count": len(cleaned), "people": cleaned})
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_body()
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        if path == "/api/analyze":
            people = payload.get("people") if isinstance(payload, dict) else None
            if not isinstance(people, list):
                people = load_people()
            if len(people) < 2:
                return self.send_json(400, {"error": "Add at least two people first"})
            return self.send_json(200, analyze(people))
        if path == "/api/demo/reset":
            return self.send_json(409, {"error": "Use the app's Reload showcase data button to seed the fictional cohort."})
        return self.send_json(404, {"error": "Not found"})


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run the Morrow demo website and Python API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "4173")))
    args = parser.parse_args()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Morrow web + API running at http://{args.host}:{args.port}")
    print("API health: /api/health | Profiles: /api/people | Match engine: POST /api/analyze")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
