# Analyse d'impact relative à la protection des données (DPIA)
*Article 35 RGPD — Obligatoire pour les traitements à haut risque*
*Plateforme d'évaluation psychométrique Acme Talent*
*Version 1.0 — 2026-04-06*

---

## Pourquoi une DPIA est-elle requise ?

Le traitement Acme Talent répond à **plusieurs critères** identifiés par les lignes directrices WP248 rev.01 du Comité Européen à la Protection des Données (CEPD) comme rendant une DPIA obligatoire :

| Critère WP248 | Applicable ? | Justification |
|--------------|-------------|--------------|
| Évaluation/scoring de personnes | ✅ Oui | Scores cognitifs, personnalité, motivations |
| Décision automatisée avec effet significatif | ✅ Oui | Rapport généré par IA, impact sur le recrutement |
| Traitement à grande échelle (potentiel) | ✅ Oui | Plateforme multi-candidats |
| Données sensibles (personnalité) | ✅ Oui | Profil psychologique OCEAN |
| Utilisation de technologies innovantes (IA) | ✅ Oui | Claude Opus 4.6 pour le rapport narratif |
| Transfert hors UE | ✅ Oui | Anthropic, Supabase, Resend (USA) |

**Conclusion : DPIA obligatoire avant mise en production.**

---

## Section 1 — Description du traitement

**Responsable de traitement :** Acme Talent  
**Objet :** Évaluation psychométrique de candidats à un poste via une plateforme web  
**Nature des données :** Scores cognitifs, profil de personnalité OCEAN, motivations, jugement situationnel  
**Personnes concernées :** Candidats à un poste transmis par Acme Talent  
**Finalité :** Aide au recrutement  
**Sous-traitants :** Supabase, Anthropic, Resend  

---

## Section 2 — Nécessité et proportionnalité

| Question | Réponse |
|----------|---------|
| La finalité est-elle légitime et explicite ? | ✅ Oui — recrutement, base CCT n°38 |
| Les données collectées sont-elles limitées au strict nécessaire ? | ✅ Oui — pas de données brutes transmises à Anthropic |
| La durée de conservation est-elle limitée ? | ✅ 12 mois + purge automatique |
| Le consentement est-il libre, éclairé, spécifique et univoque ? | ✅ Recueilli avant le test, versionné, horodaté |
| Le candidat est-il informé de l'IA ? | ✅ Disclaimer AI Act dans le rapport et le consentement |
| Le candidat peut-il exercer ses droits ? | ✅ Endpoints /my-data + email |
| Une décision finale peut-elle reposer uniquement sur les scores ? | ❌ Non — interdit par CCT n°38 et RGPD Art. 22 (documenté dans CGU) |

---

## Section 3 — Risques identifiés et mesures

### Risque 1 — Discrimination algorithmique

| | |
|-|-|
| **Description** | Les scores pourraient conduire à une discrimination indirecte si mal utilisés |
| **Probabilité** | Moyenne |
| **Gravité** | Élevée (impact emploi) |
| **Mesures** | Labels neutres sans jugement de valeur · CGU interdisant l'exclusion sur score unique · Entretien obligatoire · Formation recruteurs |
| **Risque résiduel** | Faible |

### Risque 2 — Violation de données (sous-traitants)

| | |
|-|-|
| **Description** | Fuite de données chez Supabase, Anthropic ou Resend |
| **Probabilité** | Faible |
| **Gravité** | Élevée (données personnelles + profil psychologique) |
| **Mesures** | DPA signés · Région EU Supabase · TLS 1.3 · RLS · Minimisation données envoyées à Anthropic |
| **Risque résiduel** | Faible |

### Risque 3 — Accès non autorisé au dashboard recruteur

| | |
|-|-|
| **Description** | Accès à des rapports par un tiers non autorisé |
| **Probabilité** | Faible |
| **Gravité** | Élevée |
| **Mesures** | JWT HS256 · Bcrypt mots de passe · HTTPS uniquement · Pas de recruiter_id hardcodé |
| **Risque résiduel** | Faible |

### Risque 4 — Sur-interprétation du rapport IA

| | |
|-|-|
| **Description** | Le rapport narratif est présenté comme une vérité absolue plutôt qu'une aide |
| **Probabilité** | Moyenne |
| **Gravité** | Moyenne |
| **Mesures** | Disclaimer AI Act visible · Formulations conditionnelles imposées au LLM · CGU signées par recruteurs |
| **Risque résiduel** | Faible |

### Risque 5 — Données conservées trop longtemps

| | |
|-|-|
| **Description** | Données candidats conservées au-delà des 12 mois réglementaires |
| **Probabilité** | Faible (purge automatique) |
| **Gravité** | Moyenne |
| **Mesures** | `expires_at` sur chaque session · pg_cron hebdomadaire · ON DELETE CASCADE |
| **Risque résiduel** | Très faible |

---

## Section 4 — Consultation préalable (Art. 36 RGPD)

Si les mesures ci-dessus **ne réduisent pas suffisamment** les risques résiduels, une consultation préalable de l'APD est obligatoire avant le démarrage du traitement.

**Décision :** Sur base des mesures documentées, les risques résiduels sont jugés faibles. Consultation préalable APD **non requise** à ce stade — à réévaluer si le volume de candidats traités dépasse 5 000 par an.

---

## Section 5 — Actions restantes avant mise en production

- [ ] Signer les DPA avec Supabase, Anthropic, Resend
- [ ] Activer la région EU sur Supabase
- [ ] Remplacer le domaine email par défaut dans Resend
- [ ] Former les recruteurs aux obligations CCT n°38 et RGPD Art. 22
- [ ] Remplir les champs [LEGAL_CONTACT_EMAIL] et [ADRESSE] dans tous les documents légaux
- [ ] Publier la politique de confidentialité sur la page d'accueil du test
- [ ] Valider la DPIA avec un juriste spécialisé RGPD avant le premier usage en production

---

*Ce document doit être révisé lors de tout changement substantiel du traitement (nouveau module, nouveau sous-traitant, changement de finalité).*
