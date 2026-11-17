import io
import base64
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response

from app.core.database import get_supabase_admin
from app.core.auth_dep import require_recruiter

try:
    import weasyprint
    from jinja2 import Environment, BaseLoader
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

supabase_admin = get_supabase_admin()
router = APIRouter(prefix="/scores", tags=["pdf"])


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 20mm 15mm; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; color: #1F2937; line-height: 1.5; }

  /* COVER */
  .cover { background: #164A44; color: white; padding: 40px; min-height: 200px; page-break-after: always; border-radius: 8px; }
  .cover-logo { font-size: 28pt; font-weight: bold; letter-spacing: 4px; color: #F5C896; margin-bottom: 8px; }
  .cover-tag { font-size: 9pt; color: rgba(255,255,255,0.5); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 32px; }
  .cover-name { font-size: 26pt; font-weight: bold; color: white; margin-bottom: 6px; }
  .cover-role { font-size: 13pt; color: #F5C896; margin-bottom: 24px; }
  .cover-meta { display: flex; gap: 32px; flex-wrap: wrap; }
  .cover-meta-item { display: flex; flex-direction: column; }
  .cover-meta-label { font-size: 8pt; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; }
  .cover-meta-value { font-size: 11pt; color: rgba(255,255,255,0.85); font-weight: bold; }
  .cover-score { float: right; text-align: center; background: rgba(255,255,255,0.08); border-radius: 12px; padding: 20px 30px; margin-top: -10px; }
  .cover-score-num { font-size: 48pt; font-weight: bold; color: white; line-height: 1; }
  .cover-score-label { font-size: 9pt; color: rgba(255,255,255,0.5); }
  .cover-score-badge { background: rgba(240,85,53,0.3); border-radius: 20px; padding: 4px 12px; font-size: 9pt; color: #F05535; font-weight: bold; margin-top: 6px; display: inline-block; }

  /* SECTIONS */
  .section { margin-bottom: 24px; page-break-inside: avoid; }
  .section-title { font-size: 14pt; font-weight: bold; color: #164A44; border-bottom: 2px solid #164A44; padding-bottom: 6px; margin-bottom: 14px; }
  .section-sub { font-size: 9pt; color: #6B7280; margin-top: -10px; margin-bottom: 12px; }

  /* SCORE BARS */
  .score-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .score-label { width: 160px; font-size: 10pt; color: #374151; }
  .score-bar-bg { flex: 1; height: 8px; background: #F3F4F6; border-radius: 4px; }
  .score-bar-fill { height: 8px; background: linear-gradient(90deg, #164A44, #22a380); border-radius: 4px; }
  .score-val { width: 50px; text-align: right; font-size: 10pt; color: #6B7280; }
  .level-badge { font-size: 8pt; font-weight: bold; padding: 2px 8px; border-radius: 10px; }
  .level-exceptionnel { background: #D1FAE5; color: #065F46; }
  .level-eleve { background: #DCFCE7; color: #166534; }
  .level-solide { background: #E0F2FE; color: #0369A1; }
  .level-modere { background: #FEF3C7; color: #92400E; }
  .level-a_developper { background: #FEE2E2; color: #991B1B; }

  /* NARRATIVE */
  .narrative { background: #F9FAFB; border-left: 3px solid #164A44; padding: 12px 16px; font-size: 10pt; color: #374151; margin-top: 10px; }
  .narrative-coral { border-left-color: #F05535; }

  /* OCEAN RADAR */
  .ocean-wrap { display: flex; gap: 24px; align-items: flex-start; }
  .ocean-chart img { width: 200px; height: 200px; }
  .ocean-dims { flex: 1; }
  .dim-row { margin-bottom: 8px; }
  .dim-label { font-size: 10pt; font-weight: bold; color: #1F2937; }
  .dim-score { font-size: 9pt; color: #6B7280; float: right; }

  /* VALUES */
  .values-wrap { display: flex; gap: 20px; }
  .values-col { flex: 1; }
  .values-title { font-size: 9pt; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; color: #6B7280; margin-bottom: 8px; }
  .value-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 10pt; }
  .value-item-top { background: rgba(22,74,68,0.06); }
  .value-item-bottom { background: rgba(240,85,53,0.05); }

  /* SIGNALS */
  .signals-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .signal { font-size: 9pt; padding: 5px 12px; border-radius: 20px; font-weight: 500; }
  .signal-positive { background: rgba(22,74,68,0.08); color: #0f3530; }
  .signal-alert { background: rgba(240,85,53,0.08); color: #952a14; }

  /* INTERVIEW Q */
  .iq-list { display: flex; flex-direction: column; gap: 10px; }
  .iq-item { background: #FFF8F6; border: 1px solid rgba(240,85,53,0.15); border-radius: 8px; padding: 12px 16px; font-size: 10pt; }
  .iq-num { font-weight: bold; color: #F05535; margin-right: 8px; }

  /* FOOTER */
  .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #E5E7EB; font-size: 8pt; color: #9CA3AF; text-align: center; }

  /* ARCHETYPE */
  .archetype { display: inline-block; background: #164A44; color: #F5C896; padding: 8px 18px; border-radius: 8px; font-size: 11pt; font-weight: bold; margin-bottom: 12px; }
</style>
</head>
<body>

<!-- COVER -->
<div class="cover">
  <div class="cover-score">
    <div class="cover-score-num">{{ global_score }}</div>
    <div class="cover-score-label">/ 100</div>
    <div class="cover-score-badge">{{ global_label_fr }}</div>
  </div>
  <div class="cover-logo">ACME TALENT</div>
  <div class="cover-tag">Rapport d'évaluation · Confidentiel</div>
  <div class="cover-name">{{ candidate_name }}</div>
  <div class="cover-role">{{ package_label }} · {{ level_label }}</div>
  <div class="cover-meta">
    <div class="cover-meta-item">
      <span class="cover-meta-label">Date</span>
      <span class="cover-meta-value">{{ computed_at }}</span>
    </div>
    <div class="cover-meta-item">
      <span class="cover-meta-label">Package</span>
      <span class="cover-meta-value">{{ package }}</span>
    </div>
  </div>
</div>

<!-- SIGNAUX -->
<div class="section">
  <div class="section-title">Signaux inter-modules</div>
  <div class="signals-wrap">
    {% for s in signals %}
    <div class="signal signal-{{ s.type }}">{{ s.label }}</div>
    {% endfor %}
  </div>
</div>

<!-- SYNTHÈSE GLOBALE -->
{% if report and report.global_narrative %}
<div class="section">
  <div class="section-title">Synthèse globale</div>
  <div class="narrative">{{ report.global_narrative }}</div>
</div>
{% endif %}

<!-- M1 -->
<div class="section">
  <div class="section-title">M1 — Raisonnement verbal &amp; numérique</div>
  <div class="section-sub">Score : {{ m1.raw }} / {{ m1_max }} · Niveau : {{ m1.level }}</div>
  {% for section, val in m1.by_section.items() %}
  <div class="score-row">
    <div class="score-label">{{ section }}</div>
    <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (val / 12 * 100)|int }}%"></div></div>
    <div class="score-val">{{ val }}</div>
  </div>
  {% endfor %}
  {% if report and report.m1_narrative %}
  <div class="narrative">{{ report.m1_narrative }}</div>
  {% endif %}
</div>

<!-- M2 OCEAN -->
<div class="section">
  <div class="section-title">M2 — Personnalité OCEAN</div>
  <div class="archetype">{{ archetype_label }}</div>
  <div class="ocean-wrap">
    {% if radar_b64 %}
    <div class="ocean-chart"><img src="data:image/png;base64,{{ radar_b64 }}" /></div>
    {% endif %}
    <div class="ocean-dims">
      <div class="dim-row"><div class="dim-label">Ouverture (O)<span class="dim-score">{{ m2.O }}/40</span></div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (m2.O / 40 * 100)|int }}%"></div></div></div>
      <div class="dim-row"><div class="dim-label">Conscienciosité (C)<span class="dim-score">{{ m2.C }}/40</span></div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (m2.C / 40 * 100)|int }}%"></div></div></div>
      <div class="dim-row"><div class="dim-label">Extraversion (E)<span class="dim-score">{{ m2.E }}/40</span></div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (m2.E / 40 * 100)|int }}%"></div></div></div>
      <div class="dim-row"><div class="dim-label">Agréabilité (A)<span class="dim-score">{{ m2.A }}/40</span></div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (m2.A / 40 * 100)|int }}%"></div></div></div>
      <div class="dim-row"><div class="dim-label">Stabilité émot. (1-N)<span class="dim-score">{{ 40 - m2.N }}/40</span></div>
        <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ ((40 - m2.N) / 40 * 100)|int }}%"></div></div></div>
    </div>
  </div>
  {% if report and report.m2_narrative %}
  <div class="narrative">{{ report.m2_narrative }}</div>
  {% endif %}
</div>

<!-- M3 -->
{% if m3 %}
<div class="section">
  <div class="section-title">M3 — Jugement Situationnel</div>
  <div class="section-sub">Score : {{ m3.raw }} / {{ m3_max }} · Niveau : {{ m3.level }} · Style : {{ m3.style }}</div>
  {% for dim, val in m3.by_dim.items() %}
  <div class="score-row">
    <div class="score-label">{{ dim }}</div>
    <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (val / 20 * 100)|int }}%"></div></div>
    <div class="score-val">{{ val }}</div>
  </div>
  {% endfor %}
  {% if report and report.m3_narrative %}
  <div class="narrative narrative-coral">{{ report.m3_narrative }}</div>
  {% endif %}
</div>
{% endif %}

<!-- M4 -->
<div class="section">
  <div class="section-title">M4 — Motivations &amp; Valeurs</div>
  <div class="section-sub">Engagement : {{ m4.engagement }}/50</div>
  <div class="score-row">
    <div class="score-label">Engagement intrinsèque</div>
    <div class="score-bar-bg"><div class="score-bar-fill" style="width: {{ (m4.engagement / 60 * 100)|int }}%"></div></div>
    <div class="score-val">{{ m4.engagement }}/50</div>
  </div>
  <div class="values-wrap" style="margin-top: 12px;">
    <div class="values-col">
      <div class="values-title">Valeurs dominantes</div>
      {% for v in m4.values.top3 %}
      <div class="value-item value-item-top">{{ loop.index }}. {{ v }}</div>
      {% endfor %}
    </div>
    <div class="values-col">
      <div class="values-title">Valeurs secondaires</div>
      {% for v in m4.values.get('bottom2', m4.values.get('bottom3', []))[:2] %}
      <div class="value-item value-item-bottom">↓ {{ v }}</div>
      {% endfor %}
    </div>
  </div>
  {% if report and report.m4_narrative %}
  <div class="narrative">{{ report.m4_narrative }}</div>
  {% endif %}
</div>

<!-- QUESTIONS D'ENTRETIEN -->
{% if report and report.interview_questions %}
<div class="section">
  <div class="section-title">Questions d'entretien suggérées</div>
  <div class="iq-list">
    {% for q in report.interview_questions %}
    <div class="iq-item"><span class="iq-num">{{ loop.index }}.</span>{{ q }}</div>
    {% endfor %}
  </div>
</div>
{% endif %}

<!-- FOOTER -->
<div class="footer">
  <strong>ACME TALENT</strong> · Rapport confidentiel · {{ computed_at }}<br>
  {% if report and report.ai_disclaimer %}{{ report.ai_disclaimer }}<br>{% endif %}
  Conformément à la CCT n°38 et à l'article 22 du RGPD, ce rapport constitue une aide à la décision et non un avis d'exclusion.
</div>

</body>
</html>"""


def _generate_radar_png(m2: dict) -> str:
    labels = ["O", "C", "E", "A", "Stab"]
    values = [m2["O"], m2["C"], m2["E"], m2["A"], 40 - m2["N"]]
    values_norm = [v / 40 for v in values]

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_norm += values_norm[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))
    ax.set_facecolor("#F9FAFB")
    fig.patch.set_facecolor("#F9FAFB")

    ax.plot(angles, values_norm, color="#164A44", linewidth=2)
    ax.fill(angles, values_norm, color="#164A44", alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=10, color="#164A44", fontweight="bold")
    ax.set_yticklabels([])
    ax.set_ylim(0, 1)
    ax.grid(color="#E5E7EB", linewidth=0.8)
    ax.spines["polar"].set_color("#E5E7EB")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


ARCHETYPE_LABELS = {
    "architect": "L'Architecte",
    "catalyst":  "Le Catalyseur",
    "guardian":  "Le Gardien",
    "explorer":  "L'Explorateur",
    "balanced":  "Profil Équilibré",
}

GLOBAL_LABELS_FR = {
    "tres_solide":    "Très solide",
    "solide":         "Solide",
    "modere":         "Équilibré",
    "en_progression": "En progression",
    "a_explorer":     "À explorer",
}

PACKAGE_LABELS = {
    "leadership":  "Leadership & Management",
    "commercial":  "Commercial & Ventes",
    "operational": "Opérationnel",
    "scan":        "Scan rapide",
}


@router.get("/{session_id}/pdf")
async def export_pdf(
    session_id: UUID,
    recruiter_id: str = Depends(require_recruiter),
):
    if not WEASYPRINT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Export PDF indisponible — WeasyPrint non installé. Exécuter : pip install weasyprint jinja2 matplotlib"
        )

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
        raise HTTPException(status_code=202, detail="Rapport en cours de génération")

    score = score_result.data
    session = session_result.data
    report = score.get("report_text") or {}
    m2 = score["m2_ocean"] or {}
    m3 = None
    if score.get("m3_raw") is not None:
        m3 = {
            "raw": score["m3_raw"],
            "level": score["m3_level"],
            "by_dim": score["m3_by_dim"] or {},
            "style": score["m3_style"] or "transactional",
        }

    try:
        radar_b64 = _generate_radar_png(m2)
    except Exception:
        radar_b64 = ""

    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_TEMPLATE)
    html_content = template.render(
        candidate_name=session["candidate_name"],
        package=session["package"],
        package_label=PACKAGE_LABELS.get(session["package"], session["package"]),
        level_label="Master" if session["package"] == "leadership" else "Bachelier",
        global_score=score["global"],
        global_label=score["global_label"],
        global_label_fr=GLOBAL_LABELS_FR.get(score["global_label"], score["global_label"]),
        signals=score.get("signals") or [],
        m1={
            "raw": score["m1_raw"],
            "level": score["m1_level"],
            "by_section": score["m1_by_section"] or {},
        },
        m1_max=32 if session["package"] == "leadership" else 26,
        m2=m2,
        archetype_label=ARCHETYPE_LABELS.get(m2.get("archetype", "balanced"), "Profil équilibré"),
        m3=m3,
        m3_max=90 if m3 and m3["raw"] > 60 else 60,
        m4={
            "engagement": score["m4_engagement"],
            "values": score["m4_values"] or {},
        },
        report=report,
        radar_b64=radar_b64,
        computed_at=score["computed_at"][:10] if score.get("computed_at") else "N/A",
    )

    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

    candidate_slug = session["candidate_name"].lower().replace(" ", "_")
    filename = f"assessment_rapport_{candidate_slug}_{session_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
