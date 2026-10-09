# CLAUDE.md — Création de bases de prospects Akiro

À relire au début de chaque session.

## Contexte

- Utilisateur : Flavien Villeneuve, co-fondateur d'Akiro (agence française de cold call B2B). Il crée les bases de prospects des clients : ciblage, extraction, nettoyage, validation client, enrichissement, import dans l'outil d'appels.
- Flavien n'est pas développeur : expliquer simplement ce qui est fait quand c'est technique, et demander avant d'exécuter quelque chose qu'il ne comprendrait pas.
- Répondre en français.

## Objectifs

1. **Priorité n°1 : la qualité des bases.** Les clients valident chaque liste avant les appels : zéro intrus sur les intitulés de poste, zéro entreprise hors cible. Chaque ligne est qualifiée indépendamment, avec un verdict par critère et une justification. La relecture humaine ne doit plus porter que sur les cas « À vérifier ».
2. **Priorité n°2 (plus tard) :** enchaîner les étapes (enrichissement Pipecorn, import Minari) depuis ici. On ne commence pas par là.

## Chaîne actuelle

1. Export des prospects depuis Pharow (CSV) ou Sales Navigator.
2. Nettoyage des intitulés de poste et de la pertinence des entreprises.
3. Mise en forme dans un Google Sheet, envoi au client pour validation.
4. Après validation : enrichissement des mobiles avec Pipecorn (API).
5. Import dans Minari (outil de cold call, API), avec mapping des champs par client.

## Méthode de qualification

Principe : ne jamais juger 1 000 lignes dans un seul contexte (la qualité se dégrade). Chaque ligne est qualifiée **indépendamment, avec le même prompt**.

1. Flavien fournit le contexte client (`clients/<client>/contexte.md`) : ce qu'il vend, à qui, intitulés acceptés/refusés, critères entreprise (secteur, taille, zone, B2B obligatoire, exclusions, concurrents).
2. **Claude écrit lui-même** le prompt de qualification à partir de cette cible.
3. Pour chaque ligne : récupérer le contenu du site web de l'entreprise (ScrapingBee si la clé est en place, sinon visite directe), puis répondre **Oui / Non / À vérifier** sur chaque critère :
   - une colonne par critère ;
   - une colonne **Verdict** : Oui si tous les critères sont Oui, Non si l'un est Non, À vérifier sinon ;
   - une colonne **Justification** en une phrase.
4. **Boucle de test** : 50 lignes → relire soi-même les 50 verdicts → corriger le prompt → 50 nouvelles lignes… jusqu'à moins de 2 erreurs sur 50 (3 itérations maximum). Ensuite seulement, lancer sur toute la liste.
5. En parallèle : nettoyer prénom, nom et raison sociale (pas de forme juridique SAS/SARL/SA/EURL…, pas de MAJUSCULES intégrales).
6. Lignes sans site web : chercher le site officiel ; en cas d'homonyme, trancher selon le secteur et la ville ; écrire « introuvable » plutôt que deviner.
7. Livrer le CSV (voir format ci-dessous) + un résumé : nombre de Oui / Non / À vérifier et les 5 motifs d'exclusion les plus fréquents.
8. Ne poser des questions qu'à la fin, sauf blocage réel.

## Règles permanentes

- Le déclaratif (code NAF, secteur LinkedIn, intitulé seul) est un **indice, jamais une preuve**. C'est le site qui tranche.
- Un verdict **par critère**, jamais un « pertinent oui/non » global.
- Toujours tester sur 50 lignes avant un traitement complet.
- Jamais de lignes supprimées : les Non restent, avec leur verdict, pour pouvoir justifier au client.
- Quand un process a fonctionné pour un client, le transformer en skill réutilisable :
  - `skills/akiro-cleaning` : skill socle (règles communes) ;
  - `skills/cleaning-<client>` : cible, critères, exclusions apprises, mapping Minari.

## Format de livraison

- CSV **UTF-8 avec BOM** (lisible dans Excel), séparateur **virgule**, une ligne par prospect.
- Colonnes d'origine conservées ; **nouvelles colonnes ajoutées à gauche**.
- Déposé dans `clients/<client>/propre/`.

## Arborescence

```
clients/
  _modele/            modèle à copier pour un nouveau client
  <client>/
    contexte.md       cible et critères du client
    brut/             exports d'origine (Pharow, Sales Navigator)
    propre/           fichiers qualifiés livrés
scripts/              scripts de traitement (scraping, qualification, nettoyage)
skills/               skills réutilisables (akiro-cleaning, cleaning-<client>)
.env                  clés API (jamais versionné)
```

## Clés API et outils

- Les clés sont dans `.env` à la racine (ou dans les variables d'environnement de la session cloud). **Jamais** dans un script, jamais dans un fichier versionné, jamais affichées dans le chat.
- Ordre de branchement :
  | Outil | Usage | Priorité |
  | --- | --- | --- |
  | ScrapingBee (`SCRAPINGBEE_API_KEY`) | Contenu des sites web à grande échelle | Maintenant |
  | Pipecorn (`PIPECORN_API_KEY`) | Enrichissement des mobiles | Plus tard |
  | Minari (`MINARI_API_KEY`) | Import de la liste finale | Plus tard |
  | Sales Navigator | Aide à construire l'URL de recherche depuis la cible | Plus tard |
