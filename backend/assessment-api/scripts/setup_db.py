import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.environ.get("SUPABASE_URL", "")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RECRUITER_EMAIL = os.environ.get("RECRUITER_EMAIL", "")

if not URL or not KEY:
    print("❌  SUPABASE_URL et SUPABASE_SERVICE_KEY manquants dans .env")
    sys.exit(1)

db = create_client(URL, KEY)

print(f"\n{'═'*55}")
print("  Acme Talent Assessment — Vérification DB")
print(f"{'═'*55}")
print(f"  Supabase : {URL}")
print()


TABLES = ["recruiters", "sessions", "questions", "answers", "scores"]
missing = []

for table in TABLES:
    try:
        r = db.table(table).select("id").limit(1).execute()
        count = len(r.data) if r.data else 0
        print(f"  ✅  {table:<15} — accessible")
    except Exception as e:
        if "relation" in str(e).lower() or "does not exist" in str(e).lower() or "42P01" in str(e):
            print(f"  ❌  {table:<15} — TABLE ABSENTE")
            missing.append(table)
        else:
            print(f"  ⚠️   {table:<15} — erreur: {e}")

if missing:
    print(f"""
❌  Tables manquantes : {', '.join(missing)}

   → Appliquer schema.sql dans Supabase SQL Editor :
     https://supabase.com/dashboard/project/{URL.split('//')[1].split('.')[0]}/sql/new

   Ouvrir schema.sql, copier-coller le contenu et cliquer Run.
   Puis relancer ce script.
""")
    sys.exit(1)


print()
if not RECRUITER_EMAIL:
    print("  ⚠️   RECRUITER_EMAIL non défini dans .env — recruteur non créé")
else:
    existing = (
        db.table("recruiters")
        .select("id, email, name")
        .eq("email", RECRUITER_EMAIL.lower().strip())
        .maybe_single()
        .execute()
    )

    if existing and existing.data:
        r = existing.data
        print(f"  ✅  Recruteur existant : {r['name']} ({r['email']}) — id: {r['id']}")
    else:
        new_rec = db.table("recruiters").insert({
            "email": RECRUITER_EMAIL.lower().strip(),
            "name":  "Recruteur Acme Talent",
            "role":  "admin",
        }).execute()

        if new_rec.data:
            r = new_rec.data[0]
            print(f"  ✅  Recruteur créé : {r['name']} ({r['email']}) — id: {r['id']}")
        else:
            print(f"  ❌  Impossible de créer le recruteur")


print()
for table in TABLES:
    try:
        r = db.table(table).select("id", count="exact").execute()
        n = r.count if hasattr(r, 'count') and r.count is not None else len(r.data or [])
        print(f"  📊  {table:<15} : {n} enregistrement(s)")
    except Exception as e:
        print(f"  ⚠️   {table:<15} : {e}")

print(f"""
{'═'*55}
  ✅  DB prête — lancez le test :
     python scripts/test_e2e.py --package leadership
{'═'*55}
""")
