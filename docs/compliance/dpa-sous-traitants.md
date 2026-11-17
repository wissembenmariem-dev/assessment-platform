# Data Processing Agreements — Sous-traitants Acme Talent
*Article 28 RGPD — Obligations contractuelles envers les sous-traitants*
*Dernière mise à jour : 2026-04-06*

---

## Principe

Tout sous-traitant traitant des données personnelles pour le compte d'Acme Talent doit être encadré par un **accord de traitement des données (DPA)** conforme à l'Art. 28 RGPD, garantissant notamment :
- Que le sous-traitant ne traite les données que sur instruction documentée
- Des mesures de sécurité appropriées (Art. 32 RGPD)
- L'assistance pour honorer les droits des personnes concernées
- La notification des violations de données dans les 72h (Art. 33 RGPD)
- La suppression ou restitution des données en fin de contrat

---

## Sous-traitant 1 : Supabase Inc.

| Champ | Valeur |
|-------|--------|
| **Rôle** | Hébergement de la base de données PostgreSQL (sessions, réponses, scores, recruteurs) |
| **Données traitées** | Toutes les données candidats et recruteurs |
| **Localisation** | USA (serveurs disponibles en région EU — **configurer la région EU en production**) |
| **DPA disponible** | Oui — [https://supabase.com/legal/dpa](https://supabase.com/legal/dpa) |
| **Transfert hors UE** | Couvert par CCT UE (Standard Contractual Clauses) |
| **Statut DPA** | ☐ À signer / Accepter via dashboard Supabase |

**Action requise :** Activer la région EU dans les paramètres du projet Supabase. Accepter le DPA via le dashboard Supabase (Settings > Legal).

---

## Sous-traitant 2 : Anthropic Inc.

| Champ | Valeur |
|-------|--------|
| **Rôle** | Génération du rapport narratif via Claude Opus 4.6 |
| **Données transmises** | Nom du candidat · Scores par module · Signaux inter-modules (pas de réponses brutes) |
| **Localisation** | USA |
| **DPA disponible** | Oui — via Anthropic Privacy Policy et API Terms |
| **Transfert hors UE** | Couvert par CCT UE |
| **Statut DPA** | ☐ À vérifier — contacter privacy@anthropic.com pour DPA formel |

**Mesure de minimisation appliquée :** Le prompt envoyé à Anthropic ne contient **pas** les réponses brutes du candidat — uniquement les scores agrégés et le nom. Cela minimise l'exposition des données personnelles.

**Note AI Act :** Anthropic est fournisseur d'un modèle d'IA à usage général (GPAI). Acme Talent est déployeur d'un système à haut risque. Les obligations Art. 26 AI Act s'appliquent.

---

## Sous-traitant 3 : Resend Inc.

| Champ | Valeur |
|-------|--------|
| **Rôle** | Envoi d'emails transactionnels (invitation candidat + notification recruteur) |
| **Données transmises** | Nom · Email · Lien unique · Score global (notification recruteur) |
| **Localisation** | USA |
| **DPA disponible** | Oui — [https://resend.com/legal/dpa](https://resend.com/legal/dpa) |
| **Transfert hors UE** | Couvert par CCT UE |
| **Statut DPA** | ☐ À accepter via dashboard Resend |

**Action requise :** Remplacer `FROM_EMAIL = "onboarding@resend.dev"` par un domaine email Acme Talent vérifié dans Resend avant mise en production.

---

## Checklist de conformité Art. 28

- [ ] DPA signé avec Supabase
- [ ] DPA signé / confirmé avec Anthropic
- [ ] DPA signé avec Resend
- [ ] Clauses CCT UE vérifiées pour chaque sous-traitant
- [ ] Région EU activée sur Supabase
- [ ] Domaine email vérifié sur Resend (pas `onboarding@resend.dev`)
- [ ] Logs de sous-traitance documentés dans le registre des traitements

---

## En cas de violation de données (Art. 33–34 RGPD)

Si un sous-traitant notifie une violation de données :
1. **Dans les 72h** : notifier l'APD (www.autoriteprotectiondonnees.be — notifications@apd-gba.be)
2. Si la violation présente un risque élevé pour les droits des personnes : notifier également les candidats concernés (Art. 34 RGPD)
3. Documenter l'incident dans le registre des violations internes

Contact APD Belgique : rue de la Presse 35, 1000 Bruxelles — +32 (0)2 274 48 00
