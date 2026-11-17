from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from datetime import datetime, timezone

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import SessionPublic, QuestionOut, BulkAnswerSubmit, ConsentStart
from app.core.database import get_supabase_admin

limiter = Limiter(key_func=get_remote_address)

supabase_admin = get_supabase_admin()
from app.services.scoring import (
    score_m1, score_m2, score_m3, score_m4,
    compute_global_score, compute_signals
)
from app.services.report import generate_report
from app.services.email import send_completion_notification

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/{token}", response_model=SessionPublic)
async def get_session_by_token(token: str):
    result = (
        supabase_admin.table("sessions")
        .select("id, candidate_name, level, modules, lang, status")
        .eq("token", token)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Lien invalide ou expiré")
    return result.data


@router.post("/{token}/start")
@limiter.limit("5/minute")
async def start_session(token: str, payload: ConsentStart, request: Request):
    if not payload.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Le consentement au traitement des données est requis pour commencer le test."
        )

    session = supabase_admin.table("sessions").select("id, status").eq("token", token).single().execute()

    if not session.data:
        raise HTTPException(status_code=404, detail="Token invalide")

    if session.data["status"] == "completed":
        raise HTTPException(status_code=400, detail="Ce test a déjà été complété")

    if session.data["status"] == "pending":
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        client_ip = client_ip.split(",")[0].strip()

        supabase_admin.table("sessions").update({
            "status":          "in_progress",
            "started_at":      datetime.now(timezone.utc).isoformat(),
            "consent_at":      datetime.now(timezone.utc).isoformat(),
            "consent_version": payload.consent_version,
            "consent_ip":      client_ip,
        }).eq("token", token).execute()

    return {"status": "in_progress"}


@router.get("/{token}/questions", response_model=list[QuestionOut])
async def get_questions(token: str):
    session = (
        supabase_admin.table("sessions")
        .select("level, modules, lang, status")
        .eq("token", token)
        .single()
        .execute()
    )
    if not session.data:
        raise HTTPException(status_code=404, detail="Token invalide")

    if session.data["status"] == "completed":
        raise HTTPException(status_code=400, detail="Test déjà complété")

    level = session.data["level"]
    module_names = session.data["modules"] or []
    lang = session.data["lang"]

    _module_name_to_num = {
        "Raisonnement Verbal et Numérique": 1,
        "Test de personnalité OCEAN": 2,
        "Jugement Situationnel — Leadership & Management": 3,
        "Motivations et Valeurs": 4,
    }
    module_nums = [_module_name_to_num[n] for n in module_names if n in _module_name_to_num]
    if not module_nums:
        module_nums = [1, 2, 4]

    level_filter = ["both", level]

    result = (
        supabase_admin.table("questions")
        .select("id, module, position, type, category, text, instruction, options, difficulty, meta")
        .in_("module", module_nums)
        .in_("level", level_filter)
        .eq("lang", lang)
        .order("module")
        .order("position")
        .execute()
    )
    return result.data or []


@router.post("/{token}/submit")
@limiter.limit("3/minute")
async def submit_test(token: str, payload: BulkAnswerSubmit, background_tasks: BackgroundTasks, request: Request):
    session = (
        supabase_admin.table("sessions")
        .select("id, status, lang, candidate_name, candidate_email, level, modules")
        .eq("token", token)
        .single()
        .execute()
    )
    if not session.data:
        raise HTTPException(status_code=404, detail="Token invalide")
    if session.data.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Test déjà complété")

    session_id   = session.data["id"]
    level        = session.data.get("level", "bachelier")
    module_names = session.data.get("modules") or []

    _module_name_to_num = {
        "Raisonnement Verbal et Numérique": 1,
        "Test de personnalité OCEAN": 2,
        "Jugement Situationnel — Leadership & Management": 3,
        "Motivations et Valeurs": 4,
    }
    expected_modules = {_module_name_to_num[n] for n in module_names if n in _module_name_to_num} or {1, 2, 4}

    if not payload.answers:
        raise HTTPException(status_code=400, detail="Aucune réponse soumise")

    submitted_modules = {ans.module for ans in payload.answers}
    missing_modules = expected_modules - submitted_modules
    if missing_modules:
        raise HTTPException(
            status_code=400,
            detail=f"Modules incomplets : M{', M'.join(str(m) for m in sorted(missing_modules))} sans réponses"
        )

    answers_to_insert = [
        {
            "session_id": session_id,
            "question_id": str(ans.question_id),
            "module": ans.module,
            "response": ans.response,
        }
        for ans in payload.answers
    ]
    if answers_to_insert:
        supabase_admin.table("answers").insert(answers_to_insert).execute()

    supabase_admin.table("sessions").update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat()
    }).eq("token", token).execute()

    background_tasks.add_task(
        _process_results,
        session_id=session_id,
        level=level,
        modules=module_names,
        lang=session.data["lang"],
        candidate_name=session.data["candidate_name"],
        candidate_email=session.data["candidate_email"],
        answers=payload.answers,
    )

    return {"status": "completed", "message": "Merci. Vos résultats ont été transmis à Acme Talent."}


async def _process_results(session_id: str, level: str, modules: list, lang: str,
                            candidate_name: str, candidate_email: str, answers: list):
    try:
        await _process_results_inner(
            session_id, level, modules, lang, candidate_name, candidate_email, answers
        )
    except Exception as e:
        import traceback
        print(f"[process_results] ERREUR pour session {session_id}: {e}")
        traceback.print_exc()


async def _process_results_inner(session_id: str, level: str, modules: list, lang: str,
                                  candidate_name: str, candidate_email: str, answers: list):
    question_ids = [str(a.question_id) for a in answers]
    q_result = (
        supabase_admin.table("questions")
        .select("id, slug, type, category, correct, meta, scoring")
        .in_("id", question_ids)
        .execute()
    )
    items = {row["id"]: row for row in (q_result.data or [])}

    raw_answers = [
        {
            **{k: v for k, v in items.get(str(a.question_id), {}).items() if k != "id"},
            "module": a.module,
            "response": a.response,
        }
        for a in answers
    ]

    m1_answers = [a for a in raw_answers if a["module"] == 1]
    m2_answers = [a for a in raw_answers if a["module"] == 2]
    m3_answers = [a for a in raw_answers if a["module"] == 3]
    m4_answers = [a for a in raw_answers if a["module"] == 4]

    m1 = score_m1(m1_answers)
    m2 = score_m2(m2_answers)
    m3 = score_m3(m3_answers) if m3_answers else None
    m4 = score_m4(m4_answers)

    global_data = compute_global_score(m1, m2, m3, m4)
    signals = compute_signals(m1, m2, m3, m4)

    report = await generate_report(
        candidate_name=candidate_name,
        level=level,
        modules=modules,
        lang=lang,
        m1=m1, m2=m2, m3=m3, m4=m4,
        global_score=global_data["score"],
        global_label=global_data["label"],
        signals=signals,
    )

    model_used = report.pop("_model_used", "unknown")

    score_data = {
        "session_id":    session_id,
        "m1_raw":        m1["raw"],
        "m1_level":      m1["level"],
        "m1_by_section": m1["by_section"],
        "m2_ocean":      m2,
        "m3_raw":        m3["raw"]     if m3 else None,
        "m3_level":      m3["level"]   if m3 else None,
        "m3_by_dim":     m3["by_dim"]  if m3 else None,
        "m3_style":      m3["style"]   if m3 else None,
        "m4_engagement": m4["engagement"],
        "m4_values":     m4["values"],
        "global":        global_data["score"],
        "global_label":  global_data["label"],
        "signals":       signals,
        "report_text":   report,
        "model_used":    model_used,
    }

    supabase_admin.table("scores").insert(score_data).execute()

    supabase_admin.table("sessions").update({
        "score_global": global_data["score"]
    }).eq("id", session_id).execute()

    send_completion_notification(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        global_score=global_data["score"],
        global_label=global_data["label"],
        session_id=session_id,
    )


