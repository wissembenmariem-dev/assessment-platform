import importlib.util
from pathlib import Path

from app.services.scoring import compute_global_score, compute_signals, score_m1, score_m2, score_m3, score_m4

spec = importlib.util.spec_from_file_location("seed_demo", Path(__file__).parents[1] / "scripts" / "seed_demo.py")
seed_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_demo)

ITEMS = [r for r in seed_demo.build() if r["lang"] == "en"]


def answers(module, response_for):
    return [{**item, "response": response_for(item)} for item in ITEMS if item["module"] == module]


def test_seed_is_consistent_across_languages():
    rows = seed_demo.build()
    assert len(rows) == 3 * len(ITEMS)
    assert len({(r["slug"], r["lang"]) for r in rows}) == len(rows)


def test_m1_scores_against_item_keys():
    perfect = score_m1(answers(1, lambda i: {"selected": i["correct"]["selected"]}))
    wrong = score_m1(answers(1, lambda i: {"selected": "Z"}))
    assert perfect["raw"] == perfect["max_possible"] == 3
    assert perfect["level"] == "exceptionnel"
    assert wrong["raw"] == 0 and wrong["level"] == "a_developper"
    assert set(perfect["by_section"]) == {"numeric", "verbal", "deductive"}


def test_m2_handles_reverse_keyed_items():
    result = score_m2(answers(2, lambda i: {"value": 5}))
    assert result["O"] == 40
    assert result["E"] == 8


def test_m3_rewards_optimal_rankings_by_dimension():
    result = score_m3(answers(3, lambda i: {"ranking": i["correct"]}))
    assert result["raw"] == result["max_possible"] == 12
    assert result["by_dim"]["people"] == 6 and result["dim_max"]["people"] == 6


def test_m4_values_and_engagement():
    def respond(item):
        return {"ranking": ["C", "A", "D", "B"]} if item["type"] == "ranking" else {"value": 4}

    result = score_m4(answers(4, respond))
    assert result["values"]["top3"][0] == "development"
    assert result["engagement"] == 30


def test_global_score_and_signals_stay_in_range():
    m1 = score_m1(answers(1, lambda i: {"selected": i["correct"]["selected"]}))
    m2 = score_m2(answers(2, lambda i: {"value": 4}))
    m3 = score_m3(answers(3, lambda i: {"ranking": i["correct"]}))
    m4 = score_m4(answers(4, lambda i: {"ranking": ["A", "B", "C", "D"]} if i["type"] == "ranking" else {"value": 5}))
    result = compute_global_score(m1, m2, m3, m4)
    assert 0 <= result["score"] <= 100
    assert isinstance(compute_signals(m1, m2, m3, m4), list)
