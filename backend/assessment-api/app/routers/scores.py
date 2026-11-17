from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.models.schemas import ScoreOut
from app.core.database import get_supabase_admin
from app.core.auth_dep import require_recruiter

supabase_admin = get_supabase_admin()

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/{session_id}", response_model=ScoreOut)
async def get_score(
    session_id: UUID,
    recruiter_id: str = Depends(require_recruiter),
):
    session_result = (
        supabase_admin.table("sessions")
        .select("id, candidate_name, package, recruiter_id")
        .eq("id", str(session_id))
        .eq("recruiter_id", recruiter_id)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    score_result = (
        supabase_admin.table("scores")
        .select("*")
        .eq("session_id", str(session_id))
        .maybe_single()
        .execute()
    )

    if not score_result or not score_result.data:
        raise HTTPException(
            status_code=202,
            detail="Le rapport est en cours de génération. Réessayez dans quelques secondes."
        )

    score = score_result.data
    session = session_result.data

    return ScoreOut(
        session_id=session_id,
        candidate_name=session.get("candidate_name", ""),
        package=session.get("package", ""),
        m1={
            "raw": score["m1_raw"],
            "level": score["m1_level"],
            "by_section": score["m1_by_section"],
        },
        m2=score["m2_ocean"],
        m3={
            "raw": score["m3_raw"],
            "level": score["m3_level"],
            "by_dim": score["m3_by_dim"],
            "style": score["m3_style"],
        } if score.get("m3_raw") is not None else None,
        m4={
            "engagement": score["m4_engagement"],
            "values": score["m4_values"],
        },
        global_score=score["global"],
        global_label=score["global_label"],
        signals=score["signals"] or [],
        report=score["report_text"],
        model_used=score.get("model_used", "unknown"),
        computed_at=score["computed_at"],
    )
