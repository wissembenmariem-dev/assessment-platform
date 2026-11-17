# Journal des actions utilisateur — Traçabilité et audit
*AI Act Art. 12 (journalisation) · CCT n°38 · RGPD Art. 5§2 (accountability)*
*Document de référence — procédure interne Acme Talent*

---

## Pourquoi ce journal ?

L'AI Act (Règlement UE 2024/1689) impose aux déployeurs de systèmes d'IA à haut risque de conserver des **logs automatiques** permettant de reconstituer le fonctionnement du système (Art. 12). La CCT n°38 impose la traçabilité des décisions de recrutement basées sur des tests psychométriques.

---

## Ce qui est journalisé en base de données

### Table `sessions`

| Champ | Événement journalisé |
|-------|---------------------|
| `created_at` | Création de la session par le recruteur |
| `started_at` | Démarrage du test par le candidat |
| `consent_at` | Acceptation explicite du consentement |
| `consent_version` | Version du texte de consentement affiché |
| `consent_ip` | Adresse IP au moment du consentement |
| `completed_at` | Soumission du test |
| `expires_at` | Date de suppression automatique |
| `status` | État courant : `pending` / `in_progress` / `completed` |

### Table `scores`

| Champ | Événement journalisé |
|-------|---------------------|
| `session_id` | Lien vers la session (traçabilité complète) |
| `model_used` | Modèle IA réellement utilisé pour le rapport |
| `created_at` | Horodatage de la génération du rapport |
| `m1_raw`, `m2_ocean`, etc. | Scores bruts — reconstructibles |
| `global` + `global_label` | Score final et label — base de la décision |
| `signals` | Signaux inter-modules ayant orienté le rapport |

---

## Ce qui n'est PAS journalisé (limites)

- Les actions individuelles du recruteur dans le dashboard (pages visitées, temps passé) ne sont pas journalisées. Si une traçabilité plus fine est requise, ajouter une table `audit_log`.
- Les erreurs de génération du rapport (`_error` dans le JSON) sont loggées en console mais pas en base.

**Action recommandée :** Pour une conformité AI Act plus robuste, ajouter une table `audit_log` :

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    actor_type TEXT NOT NULL,  -- 'candidate' | 'recruiter' | 'system'
    actor_id TEXT,             -- email recruteur ou token candidat (haché)
    action TEXT NOT NULL,      -- 'session_created' | 'test_started' | 'report_generated' | etc.
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Procédure d'audit sur demande (CCT n°38 + RGPD Art. 15)

Si un candidat ou une autorité demande à reconstituer le traitement d'une évaluation :

1. Identifier la session via `session_id` ou l'email candidat
2. Extraire depuis `sessions` : consentement, horodatages, statut
3. Extraire depuis `scores` : tous les scores, `model_used`, `signals`, `report_text`
4. Vérifier `model_used` = modèle IA effectivement utilisé (AI Act Art. 12)
5. Vérifier `consent_version` → lire `legal/consentement-candidat-v1.md` pour le texte exact affiché
6. Documenter la réponse et l'envoyer dans les 30 jours (Art. 12§3 RGPD)

---

## Droits d'accès aux logs

| Acteur | Accès autorisé |
|--------|----------------|
| Candidat | Ses propres données via `GET /test/{token}/my-data` |
| Recruteur Acme Talent | Accès via dashboard — limité aux sessions qu'il a créées |
| Acme Talent (admin) | Accès complet via Supabase admin |
| APD / autorité judiciaire | Sur réquisition — contact [LEGAL_CONTACT_EMAIL] |

---

## Durée de conservation des logs

Conforme à la durée de conservation des sessions : **12 mois** puis suppression automatique via pg_cron (ON DELETE CASCADE sur `scores` et `answers`).

Pour les logs d'audit (`audit_log` si implémenté) : conserver 3 ans minimum (obligations légales en matière de preuves, droit belge).

---

## Incidents et violations

En cas de suspicion de violation des données ou d'utilisation abusive :

1. Suspendre l'accès du compte recruteur concerné
2. Notifier l'APD dans les 72h si la violation affecte des données personnelles (Art. 33 RGPD)
3. Conserver les logs liés à l'incident (ne pas purger manuellement)
4. Contacter [LEGAL_CONTACT_EMAIL]
