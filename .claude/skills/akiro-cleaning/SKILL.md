---
name: akiro-cleaning
description: Skill socle du nettoyage des bases de prospects Akiro — dédoublonnage, nettoyage des noms, qualification ligne par ligne avec verdict par critère, boucle de test sur 50 lignes, livraison CSV. Déclencher quand Flavien dépose un export Pharow / Sales Navigator ou dit « nettoie », « qualifie », « dédoublonne », « prépare la liste de … », « livre la base de … ».
---

# Nettoyage et qualification d'une base de prospects

Étapes 3 à 5 de la machine (voir `CLAUDE.md`). Règles communes à tous les clients ; les
spécificités d'un client vivent dans `clients/<client>/contexte.md` et `prompt_qualification.md`
(et plus tard dans un skill `cleaning-<client>`).

Avant de commencer : relire `contexte.md` et `prompt_qualification.md` du client. S'il n'y a
pas de prompt de qualification, passer d'abord par le skill `akiro-onboarding`.

## 1. Vérifier le fichier

```
python3 scripts/lire_export.py clients/<client>/brut/<export>
```
Contrôler les colonnes repérées. Si une colonne est mal reconnue, la forcer à l'étape suivante
avec `--colonne poste="Job Title"`. Ne jamais modifier le fichier dans `brut/`.

## 2. Dédoublonner et nettoyer les noms (TOUJOURS en premier)

```
python3 scripts/dedoublonner.py clients/<client>/brut/<export> --client <client> --ajouter-au-registre
```
- Lit les exclusions du client (`exclusions/` = entreprises, `exclusions/personnes/` = personnes),
  le registre central (`registre/registre.csv`) et les doublons internes.
- Écrit `clients/<client>/travail/<export>_prepare.csv` : colonnes ajoutées à gauche (ID ligne,
  Statut, Motif doublon, Info registre, prénom / nom / raison sociale propres, Domaine).
- Option `--autres-clients signaler` si Flavien accepte de re-proposer un prospect déjà extrait
  pour un autre client (par défaut : bloqué).
- Les lignes « Doublon » restent dans le fichier mais ne sont ni qualifiées ni enrichies.
- Relancer sur le même fichier est sans danger (ses propres lignes du registre sont ignorées).

Relire rapidement les noms propres produits (casse, particules, sigles) et corriger à la main
les cas bizarres dans le fichier de verdicts si besoin.

## 3. Récupérer le contenu des sites

```
python3 scripts/recuperer_sites.py clients/<client>/travail/<export>_prepare.csv clients/<client>/travail/sites
```
- Une seule fois par domaine, cache dans `travail/sites/` (jamais repayé). Visite directe,
  ScrapingBee en secours. Au 24/10/2026 : environ 88 % des sites récupérés du premier coup.
- Lignes sans site ou site en panne : ce sont les sous-agents qui cherchent (recherche web)
  pendant la qualification. Homonyme → trancher par secteur et ville ; sinon « introuvable ».
- Sources de secours fiables : annuaire officiel des entreprises
  (`recherche-entreprises.api.gouv.fr`, joignable : effectif, NAF, siège), Pappers, annuaires
  professionnels (Ordre, Compteo, Finalib). Le statut « QUALIFIED / DISQUALIFIED » de Pipecorn
  n'est qu'un indice (il rate les entreprises mal renseignées).

## 4. Qualifier ligne par ligne

- Uniquement les lignes « À qualifier ».
- Chaque ligne est jugée **indépendamment, avec le même prompt** (`prompt_qualification.md`).
  Ne jamais juger des centaines de lignes dans un seul contexte.
- Mise en œuvre : sous-agents (outil Agent) recevant chacun le prompt + un paquet de 10 lignes
  maximum (données de la ligne + extrait du site), avec la consigne de juger chaque ligne
  séparément et de rendre une ligne CSV par prospect.
- Format de sortie d'un agent : `"ID ligne","<critère 1>",…,"Justification","Site officiel"`.
- **Entre deux vagues d'agents, transmettre les sites officiels déjà trouvés** à tous les
  prospects du même cabinet (champ « Site officiel déjà trouvé » dans le lot) : sinon un agent
  trouve le site et un autre non, et les verdicts entreprise divergent.
- Après la dernière vague : vérifier que les prospects d'une même entreprise ont les mêmes
  verdicts entreprise, harmoniser à la main en le notant dans la justification.
- Rassembler les réponses dans `clients/<client>/travail/<export>_verdicts.csv` :
  `ID ligne,<critère 1>,<critère 2>,…,Justification` (valeurs Oui / Non / À vérifier).

### Boucle de test (obligatoire)

1. 50 lignes → relire soi-même les 50 verdicts, ligne par ligne.
2. Compter les erreurs. Corriger le prompt (noter la correction dans l'historique du prompt).
3. 50 nouvelles lignes. Recommencer jusqu'à moins de 2 erreurs sur 50 — 3 itérations maximum.
4. Ensuite seulement : toute la liste.

## 5. Livrer

```
python3 scripts/livrer.py clients/<client>/travail/<export>_prepare.csv --verdicts clients/<client>/travail/<export>_verdicts.csv
```
- Le Verdict est calculé par le script (Oui si tous Oui, Non si un Non, À vérifier sinon ;
  « Doublon » pour les doublons, avec le motif en justification).
- Sortie : `clients/<client>/propre/<export>_qualifie.csv`, UTF-8 avec BOM, virgule, nouvelles
  colonnes à gauche, colonnes d'origine conservées, aucune ligne supprimée.
- Résumé à donner à Flavien : nombre de Oui / Non / À vérifier / Doublon et les 5 motifs
  d'exclusion les plus fréquents (critères à Non + motifs de doublon), en une dizaine de lignes.

## 6. Capitaliser

Après le retour du client : ajouter les refus et nouvelles règles dans `contexte.md`
(« Exclusions apprises ») et dans le prompt de qualification. Quand le process a fonctionné
pour un client, en faire un skill `.claude/skills/cleaning-<client>/SKILL.md`.

## Rappels

- Le déclaratif (NAF, secteur LinkedIn, intitulé seul) est un indice, jamais une preuve.
- Un verdict par critère, jamais un « pertinent oui/non » global.
- Questions à Flavien : à la fin, sauf blocage réel. Expliquer simplement ce qui est fait.
- Clés API : jamais affichées, jamais écrites dans un fichier versionné.
