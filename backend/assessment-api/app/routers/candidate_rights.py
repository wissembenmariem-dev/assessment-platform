from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_supabase_admin

router = APIRouter(prefix="/test", tags=["droits-rgpd"])

supabase_admin = get_supabase_admin()


@router.get("/{token}/my-data")
async def get_my_data(token: str):
    session_result = (
        supabase_admin.table("sessions")
        .select(
            "id, candidate_name, candidate_email, package, lang, status, "
            "consent_at, consent_version, created_at, started_at, completed_at, expires_at"
        )
        .eq("token", token)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(status_code=404, detail="Token invalide ou données déjà supprimées.")

    session = session_result.data

    scores_result = (
        supabase_admin.table("scores")
        .select("global, global_label, m1_raw, m1_level, m4_engagement, computed_at, model_used")
        .eq("session_id", session["id"])
        .execute()
    )
    scores = scores_result.data[0] if scores_result.data else None

    return {
        "info": "Données personnelles vous concernant — RGPD Art. 15",
        "responsable_traitement": f"Acme Talent — {settings.legal_contact_email}",
        "session": {
            "candidate_name":  session["candidate_name"],
            "candidate_email": session["candidate_email"],
            "package":         session.get("package"),
            "lang":            session["lang"],
            "status":          session["status"],
            "created_at":      session["created_at"],
            "started_at":      session["started_at"],
            "completed_at":    session["completed_at"],
            "expires_at":      session["expires_at"],
        },
        "consentement": {
            "consent_at":      session["consent_at"],
            "consent_version": session["consent_version"],
            "note": f"Le texte complet de cette version est disponible sur demande à {settings.legal_contact_email}",
        },
        "scores_agrégés": scores,
        "droits": {
            "effacement":      f"DELETE /api/v1/test/{token}/my-data",
            "contact":         settings.legal_contact_email,
            "délai_réponse":   "30 jours (Art. 12§3 RGPD)",
            "réclamation_apd": "https://www.autoriteprotectiondonnees.be",
        },
    }


@router.delete("/{token}/my-data")
async def delete_my_data(token: str):
    session_result = (
        supabase_admin.table("sessions")
        .select("id, candidate_name, candidate_email")
        .eq("token", token)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=404,
            detail="Token invalide ou données déjà supprimées."
        )

    deleted_at = datetime.now(timezone.utc).isoformat()

    supabase_admin.table("sessions").delete().eq("token", token).execute()

    return {
        "message": "Vos données ont été supprimées conformément à l'Art. 17 RGPD.",
        "deleted_at": deleted_at,
        "données_supprimées": ["session", "réponses", "scores", "rapport"],
        "contact": settings.legal_contact_email,
    }
