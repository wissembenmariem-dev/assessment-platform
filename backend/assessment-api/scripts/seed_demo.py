import os
import sys

LANGS = ("fr", "en", "nl")
LIKERT_AGREE = {
    "fr": ["Pas du tout d'accord", "Plutôt pas d'accord", "Neutre", "Plutôt d'accord", "Tout à fait d'accord"],
    "en": ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
    "nl": ["Helemaal oneens", "Oneens", "Neutraal", "Eens", "Helemaal eens"],
}


def opts(*texts):
    return [{"id": chr(65 + i), "text": t} for i, t in enumerate(texts)]


def likert(lang):
    return [{"id": str(i + 1), "text": t} for i, t in enumerate(LIKERT_AGREE[lang])]


M1 = [
    ("m1_demo_01", "numeric", {"fr": "3 · 6 · 12 · 24 · ?", "en": "3 · 6 · 12 · 24 · ?", "nl": "3 · 6 · 12 · 24 · ?"}, ["36", "48", "30", "42"], "B"),
    ("m1_demo_02", "verbal", {"fr": "Livre est à lire ce que fourchette est à…", "en": "Book is to read as fork is to…", "nl": "Boek staat tot lezen zoals vork staat tot…"},
     ["cuisine / kitchen / keuken", "manger / eat / eten", "métal / metal / metaal", "table / table / tafel"], "B"),
    ("m1_demo_03", "deductive", {"fr": "Tous les A sont B. Aucun B n'est C. Donc…", "en": "All A are B. No B is C. Therefore…", "nl": "Alle A zijn B. Geen B is C. Dus…"},
     ["Aucun A n'est C / No A is C / Geen A is C", "Certains A sont C / Some A are C / Sommige A zijn C", "Tous les C sont A / All C are A / Alle C zijn A", "On ne peut pas conclure / Cannot conclude / Geen conclusie"], "A"),
]

M2 = [
    ("m2_demo_O", "O", False, {"fr": "J'aime explorer des idées nouvelles.", "en": "I enjoy exploring new ideas.", "nl": "Ik verken graag nieuwe ideeën."}),
    ("m2_demo_C", "C", False, {"fr": "Je termine ce que je commence.", "en": "I finish what I start.", "nl": "Ik maak af waar ik aan begin."}),
    ("m2_demo_E", "E", True, {"fr": "Je préfère rester en retrait en groupe.", "en": "I prefer to stay in the background in groups.", "nl": "In groep blijf ik liever op de achtergrond."}),
    ("m2_demo_A", "A", False, {"fr": "Je prends le temps d'aider les autres.", "en": "I make time to help others.", "nl": "Ik maak tijd om anderen te helpen."}),
    ("m2_demo_N", "N", False, {"fr": "Je m'inquiète facilement.", "en": "I worry easily.", "nl": "Ik maak me snel zorgen."}),
]

M3 = [
    ("m3_demo_01", "people", "transformational",
     {"fr": "Un collaborateur expérimenté semble démotivé depuis plusieurs semaines.", "en": "An experienced team member has seemed disengaged for several weeks.", "nl": "Een ervaren teamlid lijkt al weken weinig betrokken."},
     ["Rappeler les objectifs par écrit / Restate goals in writing / Doelen schriftelijk herhalen",
      "Organiser un entretien individuel pour comprendre / Hold a one-to-one to understand / Een individueel gesprek houden",
      "Redistribuer une partie de ses tâches / Reassign some of their work / Een deel van zijn taken herverdelen",
      "Attendre que la situation s'améliore / Wait for things to improve / Afwachten"], ["B", "C", "A", "D"]),
    ("m3_demo_02", "pressure", "directive",
     {"fr": "Un client demande de livrer en deux semaines un projet qui en demande quatre.", "en": "A client asks for a four-week project to be delivered in two.", "nl": "Een klant vraagt een project van vier weken in twee weken te leveren."},
     ["Accepter et faire faire des heures supplémentaires / Accept and add overtime / Aanvaarden met overuren",
      "Proposer un périmètre réduit pour la date demandée / Offer a reduced scope for the date / Een kleinere scope voorstellen",
      "Expliquer le délai réaliste et ses raisons / Explain the realistic timeline / De realistische timing toelichten",
      "Refuser le projet / Decline the project / Het project weigeren"], ["B", "C", "A", "D"]),
]

M4_RANKING = [
    ("m4_demo_G1", {"fr": "Ce que vous valorisez le plus au travail", "en": "What you value most at work", "nl": "Wat u het meest waardeert in uw werk"},
     ["Des résultats mesurables / Measurable results / Meetbare resultaten",
      "De bonnes relations / Good relationships / Goede relaties",
      "Apprendre en continu / Continuous learning / Continu leren",
      "De l'autonomie / Autonomy / Autonomie"],
     {"A": "performance", "B": "social", "C": "development", "D": "autonomy"}),
]

M4_LIKERT = [
    ("m4_demo_D1", False, {"fr": "Je fais souvent plus que ce qui m'est demandé.", "en": "I often go beyond what is asked of me.", "nl": "Ik doe vaak meer dan wat van mij gevraagd wordt."}),
    ("m4_demo_D2", True, {"fr": "Quand un projet ne me motive pas, mes résultats baissent.", "en": "When a project does not motivate me, my results drop.", "nl": "Als een project mij niet motiveert, dalen mijn resultaten."}),
]


def pick(text, lang):
    parts = [p.strip() for p in text.split(" / ")]
    return parts[LANGS.index(lang)] if len(parts) == len(LANGS) else text


def build():
    rows = []
    for lang in LANGS:
        for pos, (slug, section, text, options, key) in enumerate(M1, 1):
            rows.append(dict(slug=slug, module=1, level="both", position=pos, type="mcq", lang=lang, category=section,
                             text=text[lang], instruction=None, options=opts(*(pick(o, lang) for o in options)),
                             correct={"selected": key}, scoring={"section": section}, meta={}))
        for pos, (slug, dim, inverted, text) in enumerate(M2, 1):
            rows.append(dict(slug=slug, module=2, level="both", position=pos, type="likert", lang=lang, category=f"ocean_{dim}",
                             text=text[lang], instruction=None, options=likert(lang), correct=None,
                             scoring={"dimension": dim, "inverted": inverted}, meta={"dimension": dim}))
        for pos, (slug, dim, style, text, options, key) in enumerate(M3, 1):
            rows.append(dict(slug=slug, module=3, level="both", position=pos, type="sjt", lang=lang, category="sjt",
                             text=text[lang], instruction=None, options=opts(*(pick(o, lang) for o in options)),
                             correct=key, scoring={"dimension": dim, "style": style}, meta={}))
        for pos, (slug, text, options, values) in enumerate(M4_RANKING, 1):
            rows.append(dict(slug=slug, module=4, level="both", position=pos, type="ranking", lang=lang, category="values",
                             text=text[lang], instruction=None, options=opts(*(pick(o, lang) for o in options)),
                             correct=None, scoring={"values": values}, meta={}))
        for pos, (slug, inverted, text) in enumerate(M4_LIKERT, len(M4_RANKING) + 1):
            rows.append(dict(slug=slug, module=4, level="both", position=pos, type="likert", lang=lang, category="engagement",
                             text=text[lang], instruction=None, options=likert(lang), correct=None,
                             scoring={"inverted": inverted}, meta={}))
    return rows


def main() -> int:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")
        return 1
    rows = build()
    create_client(url, key).table("questions").upsert(rows, on_conflict="slug,lang").execute()
    print(f"Seeded {len(rows)} demo items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
