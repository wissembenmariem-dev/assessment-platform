# Texte de consentement candidat — Version v1.0
*Référencé dans le code comme `consent_version: "v1.0"`*
*Affiché sur l'écran de démarrage du test, avant toute collecte de données*
*Conserver cette version même après mises à jour — traçabilité RGPD Art. 7*

---

## Texte à afficher au candidat (verbatim)

---

**Avant de commencer votre évaluation**

Dans le cadre de votre candidature, Acme Talent vous invite à compléter une évaluation psychométrique. Pour vous la proposer, nous devons traiter certaines de vos données personnelles.

**Ce que nous collectons :**
- Vos informations d'identification (nom, email)
- Vos réponses aux questionnaires d'évaluation
- Votre adresse IP et la date/heure de démarrage (pour horodater votre consentement)
- Les scores calculés à partir de vos réponses

**Pourquoi :**
Ces données permettent de générer un rapport d'évaluation transmis au recruteur Acme Talent en charge de votre dossier. Un rapport narratif est également produit par intelligence artificielle (Claude Opus, Anthropic). Ce rapport est une aide à la décision — il ne constitue pas un bilan psychologique certifié et ne peut jamais être l'unique base d'une décision de recrutement.

**Conservation :**
Vos données sont conservées pendant 12 mois, puis supprimées automatiquement.

**Vos droits :**
Vous pouvez accéder à vos données, les télécharger ou demander leur suppression via votre lien de test, ou en contactant [LEGAL_CONTACT_EMAIL]. Vous pouvez également introduire une réclamation auprès de l'Autorité de Protection des Données (www.autoriteprotectiondonnees.be).

**Votre consentement est nécessaire pour démarrer l'évaluation.** Il peut être retiré à tout moment, mais entraînera la suppression de vos données et l'impossibilité de participer au processus.

---

☐ **J'ai lu et j'accepte** que Acme Talent traite mes données personnelles dans le cadre de cette évaluation, conformément à la politique de confidentialité ci-dessus.

[Commencer l'évaluation →]

---

## Notes techniques (usage interne)

- Ce texte correspond à `consent_version = "v1.0"` stocké dans la table `sessions`
- La date/heure du clic est stockée dans `consent_at`
- L'IP du candidat est stockée dans `consent_ip` (depuis `X-Forwarded-For`)
- Ne jamais modifier ce fichier rétroactivement — créer une version `v1.1`, `v2.0`, etc.
- En cas de modification substantielle du traitement, une nouvelle version avec re-consentement est obligatoire (Art. 7§3 RGPD)

## Historique des versions

| Version | Date | Modifications |
|---------|------|--------------|
| v1.0 | 2026-04-06 | Version initiale |
