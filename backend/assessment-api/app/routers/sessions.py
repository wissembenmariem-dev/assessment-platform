from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.models.schemas import SessionCreate, SessionOut, DashboardStats
from app.core.database import get_supabase_admin
from app.core.auth_dep import require_recruiter
from app.core.config import settings
from app.services.token import generate_token, generate_candidate_link
from app.services.email import send_candidate_invitation

supabase_admin = get_supabase_admin()

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionOut, status_code=201)
async def create_session(
    payload: SessionCreate,
    recruiter_id: str = Depends(require_recruiter),
):
    token = generate_token()

    data = {
        "recruiter_id": recruiter_id,
        "candidate_name": payload.candidate_name,
        "candidate_email": payload.candidate_email,
        "level": payload.level,
        "modules": payload.modules,
        "lang": payload.lang,
        "token": token,
        "status": "pending",
        "position_visee": payload.position_visee,
        "entreprise_cible": payload.entreprise_cible,
    }

    result = supabase_admin.table("sessions").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Impossible de créer la session")

    session = result.data[0]
    candidate_link = generate_candidate_link(settings.app_base_url, token)
    session["candidate_link"] = candidate_link

    if settings.resend_api_key:
        send_candidate_invitation(
            candidate_name=payload.candidate_name,
            candidate_email=payload.candidate_email,
            candidate_link=candidate_link,
            level=payload.level,
        )

    return session


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(recruiter_id: str = Depends(require_recruiter)):
    result = (
        supabase_admin.table("sessions")
        .select("status, score_global")
        .eq("recruiter_id", recruiter_id)
        .execute()
    )

    sessions = result.data or []
    total = len(sessions)
    completed = [s for s in sessions if s["status"] == "completed"]
    pending = [s for s in sessions if s["status"] in ("pending", "in_progress")]
    scores = [s["score_global"] for s in completed if s["score_global"] is not None]

    return DashboardStats(
        total_sent=total,
        total_completed=len(completed),
        completion_rate=round(len(completed) / total * 100, 1) if total > 0 else 0,
        avg_score=round(sum(scores) / len(scores), 1) if scores else None,
        pending_count=len(pending),
    )


@router.get("/", response_model=list[SessionOut])
async def list_sessions(recruiter_id: str = Depends(require_recruiter)):
    result = (
        supabase_admin.table("sessions")
        .select("*")
        .eq("recruiter_id", recruiter_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: UUID,
    recruiter_id: str = Depends(require_recruiter),
):
    result = (
        supabase_admin.table("sessions")
        .select("*")
        .eq("id", str(session_id))
        .eq("recruiter_id", recruiter_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return result.data
