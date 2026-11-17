# Politique de confidentialité — Plateforme d'évaluation Acme Talent
*Version 1.0 — 2026-04-06*
*À afficher sur la page d'accueil du test candidat (Art. 13 RGPD)*

---

## 1. Qui traite vos données ?

**Responsable de traitement :**  
Acme Talent — [DÉNOMINATION SOCIALE COMPLÈTE]  
[ADRESSE COMPLÈTE]  
[LEGAL_CONTACT_EMAIL]

---

## 2. Pourquoi collectons-nous vos données ?

Dans le cadre de votre processus de candidature, Acme Talent vous invite à compléter une évaluation psychométrique. Vos données sont traitées pour :

- **Évaluer vos aptitudes** dans les domaines du raisonnement, de la personnalité et des motivations professionnelles
- **Générer un rapport d'évaluation** transmis au recruteur en charge de votre dossier
- **Vous envoyer votre lien d'évaluation** par email

**Base légale :**
- Votre consentement explicite (Art. 6§1a et Art. 9§2a RGPD) — recueilli avant le début du test
- L'intérêt légitime d'Acme Talent dans le cadre du processus de recrutement (Art. 6§1f RGPD)

Vous pouvez retirer votre consentement à tout moment (voir section 5).

---

## 3. Quelles données collectons-nous ?

- **Données d'identification :** nom, adresse email
- **Réponses au test :** réponses aux questions de raisonnement, de personnalité, de jugement et de motivation
- **Données techniques :** adresse IP au moment du démarrage (traçabilité du consentement), horodatages
- **Scores calculés :** résultats agrégés par module, score global, rapport narratif

---

## 4. Qui reçoit vos données ?

- **Acme Talent** (recruteurs en charge de votre dossier) — accès complet au rapport
- **L'entreprise cliente** pour laquelle le recrutement est effectué — rapport synthétique uniquement, selon accord préalable
- **Sous-traitants techniques :**

| Sous-traitant | Rôle | Localisation |
|--------------|------|-------------|
| Supabase Inc. | Hébergement de la base de données | USA (données stockées en région EU si configuré) |
| Anthropic Inc. | Génération du rapport narratif par IA (Claude Opus) | USA |
| Resend Inc. | Envoi d'emails | USA |

Tous les transferts hors UE sont encadrés par des Clauses Contractuelles Types approuvées par la Commission européenne (Art. 46 RGPD).

Vos données ne sont **jamais vendues** ni utilisées à des fins de marketing.

---

## 5. Combien de temps conservons-nous vos données ?

Vos données sont conservées **12 mois** à compter de la date de soumission de votre évaluation, puis supprimées automatiquement (y compris vos réponses et votre rapport).

---

## 6. Quels sont vos droits ?

Conformément au RGPD, vous disposez des droits suivants :

| Droit | Fondement | Comment l'exercer |
|-------|-----------|-------------------|
| **Accès** (Art. 15) | Obtenir une copie de vos données | Via votre lien de test : `GET /test/{token}/my-data` ou par email |
| **Portabilité** (Art. 20) | Recevoir vos données en format JSON | Idem |
| **Rectification** (Art. 16) | Corriger des données inexactes | Par email |
| **Effacement** (Art. 17) | Faire supprimer vos données | Via votre lien de test : `DELETE /test/{token}/my-data` ou par email |
| **Opposition** (Art. 21) | Vous opposer au traitement | Par email — décision prise dans les 30 jours |
| **Limitation** (Art. 18) | Suspendre le traitement | Par email |
| **Retrait du consentement** | À tout moment, sans préjudice | Par email |

**Contact :** [LEGAL_CONTACT_EMAIL]  
**Délai de réponse :** 30 jours calendrier (Art. 12§3 RGPD)

En cas de réponse insatisfaisante, vous pouvez introduire une réclamation auprès de l'**Autorité de Protection des Données** :  
[www.autoriteprotectiondonnees.be](https://www.autoriteprotectiondonnees.be) — Rue de la Presse 35, 1000 Bruxelles — contact@apd-gba.be

---

## 7. Décisions automatisées (Art. 22 RGPD)

Votre évaluation produit des scores calculés algorithmiquement. Un **rapport narratif est généré par un système d'intelligence artificielle** (Claude Opus, Anthropic). Ces résultats constituent une **aide à la décision** pour le recruteur — ils ne constituent **jamais** une décision automatisée au sens de l'Art. 22 RGPD et ne peuvent en aucun cas suffire à eux seuls à vous exclure d'un processus de recrutement.

Conformément à la CCT n°38 (Convention collective de travail sur le recrutement, Belgique), vous avez le droit d'être informé des méthodes et critères utilisés, et de contester toute décision basée sur ces résultats.

---

## 8. Sécurité

Vos données sont protégées par :
- Chiffrement en transit (TLS 1.3)
- Chiffrement au repos (base de données chiffrée)
- Accès limité aux recruteurs autorisés via authentification sécurisée
- Lien de test à usage unique — non réutilisable après soumission

---

*Cette politique peut être mise à jour. La version en vigueur est toujours accessible via votre lien de test.*
