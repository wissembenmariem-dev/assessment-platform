import os
import resend
from app.core.config import settings

FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


def send_candidate_invitation(
    candidate_name: str,
    candidate_email: str,
    candidate_link: str,
    level: str = "",
    package: str = "",
) -> bool:
    resend.api_key = settings.resend_api_key

    package_labels = {
        "scan":        "Évaluation Scan",
        "operational": "Évaluation Opérationnelle",
        "commercial":  "Évaluation Commerciale",
        "leadership":  "Évaluation Leadership",
    }
    package_label = package_labels.get(package, "Évaluation")

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #1a1a2e; padding: 32px; text-align: center;">
        <h1 style="color: #e8c97e; margin: 0; font-size: 24px; letter-spacing: 2px;">ACME TALENT</h1>
        <p style="color: #aaa; margin: 8px 0 0; font-size: 12px; letter-spacing: 1px;">EXECUTIVE SEARCH</p>
      </div>

      <div style="padding: 40px 32px; background: #fff;">
        <p style="color: #333; font-size: 16px;">Bonjour <strong>{candidate_name}</strong>,</p>

        <p style="color: #555; line-height: 1.6;">
          Dans le cadre de votre candidature, ACME TALENT vous invite à compléter
          une <strong>{package_label}</strong>.
        </p>

        <p style="color: #555; line-height: 1.6;">
          Cette évaluation vous prendra environ 45 à 60 minutes.
          Choisissez un moment calme et sans interruption pour la compléter.
        </p>

        <div style="text-align: center; margin: 40px 0;">
          <a href="{candidate_link}"
             style="background: #e8c97e; color: #1a1a2e; padding: 16px 40px;
                    text-decoration: none; border-radius: 4px; font-weight: bold;
                    font-size: 16px; letter-spacing: 1px;">
            Commencer l'évaluation →
          </a>
        </div>

        <p style="color: #888; font-size: 13px; line-height: 1.6;">
          Ou copiez ce lien dans votre navigateur :<br>
          <a href="{candidate_link}" style="color: #e8c97e;">{candidate_link}</a>
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">

        <p style="color: #aaa; font-size: 12px;">
          Ce lien est personnel et ne peut être utilisé qu'une seule fois.<br>
          Pour toute question : <a href="mailto:{settings.legal_contact_email}" style="color: #e8c97e;">{settings.legal_contact_email}</a>
        </p>
      </div>

      <div style="background: #f5f5f5; padding: 16px 32px; text-align: center;">
        <p style="color: #aaa; font-size: 11px; margin: 0;">
          © 2026 ACME TALENT
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [candidate_email],
            "subject": f"Votre évaluation ACME TALENT — {package_label}",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[email] Erreur invitation → {candidate_email}: {e}")
        return False


def send_completion_notification(
    candidate_name: str,
    candidate_email: str,
    global_score: int,
    global_label: str,
    session_id: str,
    package: str = "",
) -> bool:
    resend.api_key = settings.resend_api_key

    label_colors = {
        "tres_solide":   "#2d9e6b",
        "solide":        "#4a9eda",
        "modere":        "#e8a838",
        "en_progression": "#e87a38",
        "a_explorer":    "#888888",
    }
    label_fr = {
        "tres_solide":   "Très solide",
        "solide":        "Solide",
        "modere":        "Modéré",
        "en_progression": "En progression",
        "a_explorer":    "À explorer",
    }
    color = label_colors.get(global_label, "#888")
    label_text = label_fr.get(global_label, global_label)

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #1a1a2e; padding: 24px 32px; text-align: center;">
        <h1 style="color: #e8c97e; margin: 0; font-size: 20px; letter-spacing: 2px;">ACME TALENT</h1>
      </div>

      <div style="padding: 32px; background: #fff;">
        <h2 style="color: #1a1a2e; margin: 0 0 24px;">✅ Évaluation complétée</h2>

        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 10px 0; color: #888; font-size: 14px;">Candidat</td>
            <td style="padding: 10px 0; color: #333; font-weight: bold;">{candidate_name}</td>
          </tr>
          <tr>
            <td style="padding: 10px 0; color: #888; font-size: 14px;">Email</td>
            <td style="padding: 10px 0; color: #333;">{candidate_email}</td>
          </tr>
          <tr>
            <td style="padding: 10px 0; color: #888; font-size: 14px;">Package</td>
            <td style="padding: 10px 0; color: #333;">{package.capitalize()}</td>
          </tr>
          <tr>
            <td style="padding: 10px 0; color: #888; font-size: 14px;">Score global</td>
            <td style="padding: 10px 0;">
              <span style="color: {color}; font-weight: bold; font-size: 20px;">{global_score}/100</span>
              <span style="color: {color}; font-size: 14px; margin-left: 8px;">— {label_text}</span>
            </td>
          </tr>
        </table>

        <div style="text-align: center; margin: 32px 0;">
          <p style="color: #888; font-size: 13px;">ID session : {session_id}</p>
        </div>

        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">

        <p style="color: #aaa; font-size: 11px; line-height: 1.6;">
          <strong>Aide à la décision — CCT n°38 &amp; RGPD Art. 22</strong><br>
          Ce rapport est généré par un système d'intelligence artificielle à partir de scores
          calculés algorithmiquement. Il constitue une aide à la décision et ne se substitue
          pas au jugement d'un professionnel RH qualifié. Aucun score ne peut constituer à
          lui seul un critère d'exclusion d'un candidat. Le candidat dispose d'un droit d'accès,
          de rectification et d'effacement de ses données conformément au RGPD.
        </p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [settings.notification_email],
            "subject": f"[assessment] {candidate_name} a complété son évaluation — {global_score}/100",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[email] Erreur notification complétion: {e}")
        return False
