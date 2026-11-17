import os
import sys
import argparse
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

API_BASE    = "http://localhost:8000/api/v1"
RECRUITER_ID = os.environ["RECRUITER_ID"]
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

parser = argparse.ArgumentParser()
parser.add_argument("--package", default="leadership", choices=["scan","operational","commercial","leadership"])
parser.add_argument("--token", default=None, help="Utiliser un token existant au lieu d'en créer un")
args = parser.parse_args()

db = create_client(SUPABASE_URL, SUPABASE_KEY)


if args.token:
    token = args.token
    print(f"🔗  Token existant : {token}")
else:
    r = requests.post(
        f"{API_BASE}/sessions/",
        params={"recruiter_id": RECRUITER_ID},
        json={
            "candidate_name": "Auto Test",
            "candidate_email": "notifications@example.com",
            "package": args.package,
            "lang": "fr",
        }
    )
    r.raise_for_status()
    session = r.json()
    token = session["token"]
    print(f"✅  Session créée — token: {token}")


requests.post(f"{API_BASE}/test/{token}/start")
print("▶️   Session démarrée")


r = requests.get(f"{API_BASE}/test/{token}/questions")
r.raise_for_status()
questions = r.json()
print(f"📋  {len(questions)} questions récupérées")


answers = []
for q in questions:
    qid   = q["id"]
    mod   = q["module"]
    qtype = q["type"]
    opts  = q.get("options", [])

    if qtype == "mcq":
        response = {"selected": "A"}

    elif qtype == "likert":
        response = {"value": 4}

    elif qtype == "sjt":
        ids = [o["id"] for o in opts]
        response = {"ranking": ids}

    elif qtype == "ranking":
        ids = [o["id"] for o in opts]
        response = {"ranking": ids}

    else:
        response = {}

    answers.append({"question_id": qid, "module": mod, "response": response})


r = requests.post(
    f"{API_BASE}/test/{token}/submit",
    json={"answers": answers}
)
r.raise_for_status()
print(f"✅  Soumission OK — {r.json()['message']}")
print(f"\n⏳  Gemini génère le rapport en arrière-plan (~10s)...")
print(f"    Session ID à utiliser pour voir le rapport :")

res = db.table("sessions").select("id").eq("token", token).single().execute()
sid = res.data["id"]
print(f"    {sid}")
print(f"\n    curl http://localhost:8000/api/v1/scores/{sid}")
