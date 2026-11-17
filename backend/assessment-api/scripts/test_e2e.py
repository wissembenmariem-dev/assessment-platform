import os
import sys
import time
import random
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

API   = "http://localhost:8000/api/v1"
PASS  = "✅"
FAIL  = "❌"
INFO  = "   "

parser = argparse.ArgumentParser()
parser.add_argument("--package",  default="leadership",
                    choices=["scan", "operational", "commercial", "leadership"])
parser.add_argument("--strategy", default="random",
                    choices=["random", "smart", "low"],
                    help="random=aléatoire | smart=bonnes réponses | low=mauvaises")
parser.add_argument("--wait",     type=int, default=20,
                    help="Secondes à attendre pour le rapport (défaut 20)")
args = parser.parse_args()

errors = []


def step(label: str):
    print(f"\n{'─'*60}\n  {label}")


def ok(msg: str):
    print(f"  {PASS}  {msg}")


def fail(msg: str):
    print(f"  {FAIL}  {msg}")
    errors.append(msg)


def info(msg: str):
    print(f"  {INFO}  {msg}")


def make_response(q: dict) -> dict:
    qtype = q["type"]
    opts  = [o["id"] for o in q.get("options", [])]

    if qtype == "mcq":
        if args.strategy == "smart":
            return {"selected": opts[0] if opts else "A"}
        elif args.strategy == "low":
            return {"selected": opts[-1] if opts else "D"}
        else:
            return {"selected": random.choice(opts) if opts else "A"}

    elif qtype == "likert":
        if args.strategy == "smart":
            dim = (q.get("meta") or {}).get("dim", "")
            return {"value": 5 if dim in ("C", "E", "A", "O") else 2}
        elif args.strategy == "low":
            return {"value": 1}
        else:
            return {"value": random.randint(1, 5)}

    elif qtype in ("sjt", "ranking"):
        shuffled = opts[:]
        if args.strategy != "random":
            pass
        else:
            random.shuffle(shuffled)
        return {"ranking": shuffled}

    return {}


step("ÉTAPE 1 — Login recruteur")

recruiter_email    = os.environ.get("RECRUITER_EMAIL", "")
recruiter_password = os.environ.get("RECRUITER_PASSWORD", "")

if not recruiter_email or not recruiter_password:
    fail("RECRUITER_EMAIL / RECRUITER_PASSWORD manquants dans .env")
    sys.exit(1)

try:
    r = requests.post(f"{API}/auth/login", json={
        "email":    recruiter_email,
        "password": recruiter_password,
    }, timeout=10)
    r.raise_for_status()
    data = r.json()
    token_jwt    = data["access_token"]
    recruiter_id = data["recruiter_id"]
    ok(f"Connecté — recruiter_id: {recruiter_id}")
    headers = {"Authorization": f"Bearer {token_jwt}"}
except Exception as e:
    fail(f"Login échoué : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")
    sys.exit(1)


step(f"ÉTAPE 2 — Création session (package={args.package}, stratégie={args.strategy})")

try:
    r = requests.post(f"{API}/sessions/",
        headers=headers,
        json={
            "candidate_name":  "Bot Test Acme Talent",
            "candidate_email": "candidate-test@example.com",
            "package":         args.package,
            "lang":            "fr",
        }, timeout=10)
    r.raise_for_status()
    session = r.json()
    candidate_token = session["token"]
    session_id      = str(session["id"])
    ok(f"Session créée — ID: {session_id}")
    info(f"Token candidat : {candidate_token}")
except Exception as e:
    fail(f"Création session échouée : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")
    sys.exit(1)


step("ÉTAPE 3 — Vérification token candidat")

try:
    r = requests.get(f"{API}/test/{candidate_token}", timeout=10)
    r.raise_for_status()
    sess_info = r.json()
    ok(f"Token valide — candidat : {sess_info['candidate_name']}, status : {sess_info['status']}")
except Exception as e:
    fail(f"Vérification token échouée : {e}")
    sys.exit(1)


step("ÉTAPE 4 — Consentement RGPD + démarrage")

try:
    r = requests.post(f"{API}/test/{candidate_token}/start",
        json={"consent_given": True, "consent_version": "v1.0"},
        timeout=10)
    r.raise_for_status()
    ok(f"Consentement enregistré — status : {r.json()['status']}")
except Exception as e:
    fail(f"Démarrage échoué : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")
    sys.exit(1)


step("ÉTAPE 5 — Récupération des questions")

try:
    r = requests.get(f"{API}/test/{candidate_token}/questions", timeout=15)
    r.raise_for_status()
    questions = r.json()
    if not questions:
        fail("Aucune question retournée — vérifiez que seed_demo.py a été exécuté")
        sys.exit(1)

    by_module = {}
    for q in questions:
        by_module.setdefault(q["module"], []).append(q)

    ok(f"{len(questions)} questions reçues")
    for mod, qs in sorted(by_module.items()):
        types = {}
        for q in qs:
            types[q["type"]] = types.get(q["type"], 0) + 1
        types_str = " | ".join(f"{t}×{n}" for t, n in types.items())
        info(f"Module {mod} : {len(qs)} questions ({types_str})")
except Exception as e:
    fail(f"Récupération questions échouée : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")
    sys.exit(1)


step("ÉTAPE 6 — Génération des réponses (stratégie : {})".format(args.strategy))

answers = []
for q in questions:
    answers.append({
        "question_id": q["id"],
        "module":      q["module"],
        "response":    make_response(q),
    })

ok(f"{len(answers)} réponses générées")
for mod, qs in sorted(by_module.items()):
    mod_answers = [a for a in answers if a["module"] == mod]
    info(f"Module {mod} : {len(mod_answers)} réponses")


step("ÉTAPE 7 — Soumission")

try:
    r = requests.post(f"{API}/test/{candidate_token}/submit",
        json={"answers": answers},
        timeout=15)
    r.raise_for_status()
    ok(f"{r.json()['message']}")
except Exception as e:
    fail(f"Soumission échouée : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")
    sys.exit(1)


step(f"ÉTAPE 8 — Attente rapport (max {args.wait}s)")

info(f"Scoring en cours...")
report_data = None
start = time.time()
attempt = 0

while time.time() - start < args.wait:
    attempt += 1
    time.sleep(3)
    try:
        r = requests.get(f"{API}/scores/{session_id}",
            headers=headers, timeout=10)
        if r.status_code == 202:
            elapsed = int(time.time() - start)
            print(f"  ⏳  Tentative {attempt} ({elapsed}s) — rapport en cours...", end="\r")
            continue
        r.raise_for_status()
        report_data = r.json()
        print()
        ok(f"Rapport disponible après {int(time.time()-start)}s")
        break
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 202:
            continue
        fail(f"Erreur HTTP : {e}")
        break
    except Exception as e:
        fail(f"Erreur : {e}")
        break

if not report_data:
    print()
    fail(f"Rapport non disponible après {args.wait}s")
    info("Le scoring fonctionne mais le rapport LLM nécessite ANTHROPIC_API_KEY")
    info(f"Vérifier dans Supabase : SELECT * FROM scores WHERE session_id = '{session_id}';")


step("ÉTAPE 9 — Validation des résultats")

if report_data:
    try:
        ok(f"Score global : {report_data['global_score']}/100 ({report_data['global_label']})")
        info(f"Modèle utilisé : {report_data['model_used']}")

        m1 = report_data.get("m1", {})
        ok(f"M1 (Raisonnement) : {m1.get('raw')} pts — niveau {m1.get('level')}")

        m2 = report_data.get("m2", {})
        ocean = {k: m2.get(k) for k in ("O","C","E","A","N")}
        ok(f"M2 (Personnalité) : {ocean} — archétype {m2.get('archetype')}")

        m3 = report_data.get("m3")
        if m3:
            ok(f"M3 (Jugement) : {m3.get('raw')} pts — {m3.get('style')}")

        m4 = report_data.get("m4", {})
        ok(f"M4 (Motivations) : engagement {m4.get('engagement')}/100")

        signals = report_data.get("signals", [])
        if signals:
            ok(f"Signaux détectés : {len(signals)}")
            for s in signals:
                icon = "🟢" if s["type"] == "positive" else "🟡"
                info(f"  {icon} {s['label']}")

        report = report_data.get("report", {})
        if report:
            ok(f"Rapport narratif : {len(report.get('interview_questions', []))} questions d'entretien générées")
            if report.get("ai_disclaimer"):
                ok("Disclaimer AI Act présent ✓")
            else:
                fail("Disclaimer AI Act ABSENT dans le rapport")

    except Exception as e:
        fail(f"Erreur validation résultats : {e}")


step("ÉTAPE 10 — Droits RGPD (Art. 15 — accès aux données)")

try:
    r = requests.get(f"{API}/test/{candidate_token}/my-data", timeout=10)
    r.raise_for_status()
    my_data = r.json()
    ok(f"GET /my-data OK — {len(my_data)} champs retournés")
    info(f"Consentement : {my_data.get('consent_at')} (version {my_data.get('consent_version')})")
except Exception as e:
    fail(f"GET /my-data échoué : {e}")
    if hasattr(e, 'response') and e.response is not None:
        info(f"Détail : {e.response.text}")


print(f"\n{'═'*60}")
print(f"  RÉSUMÉ — Session {session_id}")
print(f"{'═'*60}")

if errors:
    print(f"\n  {FAIL}  {len(errors)} erreur(s) détectée(s) :")
    for e in errors:
        print(f"       • {e}")
else:
    print(f"\n  {PASS}  Tous les tests ont réussi")

print(f"\n  Swagger :  http://localhost:8000/docs")
print(f"  Rapport :  curl -H 'Authorization: Bearer <token>' \\")
print(f"             http://localhost:8000/api/v1/scores/{session_id}")
print()
