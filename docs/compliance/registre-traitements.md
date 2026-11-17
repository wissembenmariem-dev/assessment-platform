# Registre des activités de traitement — Acme Talent
*Article 30 RGPD — Tenu à jour par le responsable de traitement*

**Responsable de traitement :** Acme Talent (dénomination sociale complète à compléter)  
**Adresse :** [ADRESSE]  
**Contact RGPD :** [LEGAL_CONTACT_EMAIL]  
**Dernière mise à jour :** 2026-04-06

---

## Traitement 1 — Évaluation psychométrique des candidats

| Champ | Valeur |
|-------|--------|
| **Finalité** | Évaluation des aptitudes cognitives, traits de personnalité et motivations professionnelles des candidats dans le cadre d'un processus de recrutement |
| **Base légale** | Art. 6§1f RGPD — intérêt légitime du responsable de traitement (processus de recrutement) · Art. 9§2a RGPD pour les données de personnalité (consentement explicite recueilli avant le test) |
| **Catégories de personnes** | Candidats à un poste transmis par Acme Talent |
| **Catégories de données** | Nom · Adresse email · Réponses aux questionnaires (raisonnement, personnalité OCEAN, jugement situationnel, motivations) · Scores calculés · Adresse IP (consentement) · Horodatages |
| **Destinataires** | Acme Talent (recruteurs internes) · Entreprises clientes pour lesquelles le recrutement est effectué (rapport synthétique uniquement) |
| **Transferts hors UE** | Anthropic Inc. (USA) — Claude Opus 4.6 pour génération du rapport narratif — couvert par Clauses Contractuelles Types (CCT) UE |
| **Durée de conservation** | 12 mois à compter de la date de soumission du test (`expires_at`) — purge automatique hebdomadaire via pg_cron |
| **Mesures de sécurité** | Chiffrement en transit (TLS 1.3) · Chiffrement au repos (Supabase/PostgreSQL) · Accès recruteur via JWT HS256 · RLS Supabase · Tokens d'accès candidat à usage unique · Consentement IP horodaté |
| **DPIA requise** | Oui — voir `docs/compliance/dpia-checklist.md` (traitement de données de personnalité à grande échelle, décision assistée) |

---

## Traitement 2 — Gestion des comptes recruteurs

| Champ | Valeur |
|-------|--------|
| **Finalité** | Authentification et traçabilité des actions des recruteurs utilisant la plateforme |
| **Base légale** | Art. 6§1b RGPD — exécution d'un contrat (contrat de service Acme Talent) |
| **Catégories de personnes** | Recruteurs Acme Talent |
| **Catégories de données** | Email · Hash du mot de passe (bcrypt) · Horodatages de connexion |
| **Destinataires** | Acme Talent uniquement |
| **Transferts hors UE** | Supabase Inc. (USA) — couvert par CCT UE |
| **Durée de conservation** | Durée du contrat de travail + 3 ans (obligations légales belges) |
| **Mesures de sécurité** | JWT HS256 · Bcrypt · Accès HTTPS uniquement |
| **DPIA requise** | Non |

---

## Traitement 3 — Envoi d'emails transactionnels

| Champ | Valeur |
|-------|--------|
| **Finalité** | Envoi du lien de test au candidat et notification de complétion au recruteur |
| **Base légale** | Art. 6§1b RGPD — nécessaire à l'exécution d'une démarche précontractuelle |
| **Sous-traitant** | Resend Inc. (USA) — voir `docs/compliance/dpa-sous-traitants.md` |
| **Données transmises** | Nom · Email · Lien unique · Score global (notification recruteur uniquement) |
| **Durée de conservation** | Logs Resend : 30 jours (configurable via tableau de bord Resend) |
| **Transferts hors UE** | Resend Inc. (USA) — CCT UE |

---

## Sous-traitants techniques (Art. 28 RGPD)

| Sous-traitant | Rôle | Localisation | Base transfert |
|--------------|------|-------------|---------------|
| Supabase Inc. | Base de données PostgreSQL + stockage | USA (région EU disponible) | CCT UE |
| Anthropic Inc. | Génération rapport narratif (Claude Opus 4.6) | USA | CCT UE |
| Resend Inc. | Envoi d'emails transactionnels | USA | CCT UE |

> **Action requise :** Vérifier que les DPA (Data Processing Agreements) sont signés avec chaque sous-traitant. Voir `docs/compliance/dpa-sous-traitants.md`.

---

## Droits des personnes concernées

Les candidats peuvent exercer leurs droits (Art. 15–22 RGPD) :
- Via l'endpoint `GET /test/{token}/my-data` (droit d'accès + portabilité)
- Via l'endpoint `DELETE /test/{token}/my-data` (droit à l'effacement)
- Par email à [LEGAL_CONTACT_EMAIL]
- Auprès de l'Autorité de Protection des Données (APD) : www.autoriteprotectiondonnees.be

Délai de réponse : 30 jours calendrier (Art. 12§3 RGPD).
