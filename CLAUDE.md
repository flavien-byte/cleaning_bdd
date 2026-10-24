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
  - `.claude/skills/akiro-cleaning` : skill socle (règles communes) — existe ;
  - `.claude/skills/akiro-onboarding` : brief → `contexte.md` → prompt de qualification — existe ;
  - `.claude/skills/cleaning-<client>` : cible, critères, exclusions apprises, mapping Minari.

## Dédoublonnage

But : ne jamais re-traiter ni re-payer (crédits Pipecorn, scraping, qualification) un prospect déjà connu.

- **Registre central** de tout ce qui a déjà été extrait : personnes (clé : URL LinkedIn ; à défaut prénom + nom + domaine de l'entreprise, normalisés) et entreprises (domaine du site ; à défaut SIREN ou raison sociale normalisée), avec la date et le client concerné.
- **Exclusions par client** dans `clients/<client>/exclusions/` : clients existants du client, prospects déjà en cours chez lui, listes déjà appelées. Fichiers fournis par Flavien, formats variés.
- Le dédoublonnage passe **en premier**, avant la qualification et avant tout appel payant.
- Conformément à la règle « jamais de lignes supprimées », un doublon reste dans le fichier avec un motif (ex. « Doublon : déjà extrait le 12/09 pour <client> », « Déjà client »), mais il n'est ni qualifié ni enrichi.
- Construit (24/10) : `scripts/dedoublonner.py`. Ordre des contrôles : exclusions du client → registre → doublons internes. Un fichier dans `exclusions/` exclut les **entreprises** listées (tous leurs contacts) ; un fichier dans `exclusions/personnes/` n'exclut que les **personnes** listées. Le motif reprend le nom du fichier : bien nommer les fichiers (`deja-clients.xlsx`, `en-cours.csv`…).
- Registre : pour l'instant `registre/registre.csv` (global, une ligne par prospect extrait, avec client, date, fichier). Proposition : le basculer dans **Airtable** (connecteur déjà branché) — en attente de la validation de Flavien.
- Prospect déjà extrait pour un **autre** client : bloqué par défaut ; option « signaler seulement » disponible. Règle définitive et durée de validité (6 mois, 12 mois, toujours ?) à trancher par Flavien.

## Feuille de route de la « machine »

Plan conçu avec Flavien le 24/10/2026. État de chaque étape :

| # | Étape | Qui fait quoi | État |
| --- | --- | --- | --- |
| 1 | Onboarding client : brief en vrac → questions → `contexte.md` → `prompt_qualification.md` | Flavien colle le brief ; Claude remplit (skill `akiro-onboarding`) | ✅ prêt |
| 2 | Filtres Sales Navigator / Pharow à partir de la cible | Claude propose les filtres à copier ; URL complète auto plus tard si utile | ✅ prêt (version simple) |
| 3 | Extraction des prospects | Flavien dépose l'export dans `brut/` ; `scripts/lire_export.py` reconnaît les colonnes | ✅ manuel / ⏳ Pipecorn (doc API + accès) |
| 4 | Dédoublonnage (exclusions client + registre + doublons internes) + nettoyage des noms | `scripts/dedoublonner.py` | ✅ prêt (registre en fichier ; Airtable à valider) |
| 5 | Qualification ligne par ligne, boucle de test 50 lignes, livraison CSV + résumé | Sous-agents Claude, même prompt par ligne ; `scripts/livrer.py` calcule le Verdict | 🟠 intitulés jugeables ; critères entreprise **bloqués** tant que les sites sont inaccessibles |
| 6 | Google Sheet pour validation client | Aujourd'hui : Flavien importe le CSV. Plus tard : compte de service Google (API joignable) ou n8n | ✅ manuel / ⏳ auto |
| 7 | Enrichissement mobiles (Pipecorn) puis import Minari | N'enrichir que les Oui validés par le client, jamais un doublon ; crédits estimés avant ; test sur 5 lignes | ⏳ doc API + accès |
| 8 | Capitalisation : exclusions apprises → `contexte.md`, prompt, skill `cleaning-<client>` ; registre à jour | Claude après chaque retour client | ✅ prêt |

### Décisions du 24/10/2026 (2e échange)

- **On avance en deux temps.** Phase 1 : jusqu'au fichier propre, envoyé au client pour validation (étapes 1 à 6). Phase 2 : Pipecorn + Minari (étape 7). On ne commence la phase 2 qu'une fois la phase 1 rodée.
- **Le kickoff est la source n°1 du contexte client** : Flavien colle le transcript (ou Claude le retrouve dans Notion) ; il est gardé tel quel dans `clients/<client>/kickoff.md`, les règles qui en sortent vont dans `contexte.md` avec la phrase citée. Le client fournit aussi une **wishlist** et une liste **no-go**.
- **Les entreprises aussi doivent être nettoyées**, pas seulement les intitulés : il faut des informations sur chaque entreprise (site via ScrapingBee, données Pipecorn, à défaut recherche web). En attendant l'accès aux sites, la recherche web intégrée peut servir pour la boucle de test sur 50 lignes.
- **Objectif : ne plus faire d'export à la main.** Claude construit la recherche Sales Navigator à partir du contexte, puis la liste est récupérée directement (piste : outils Pipecorn — à vérifier une fois connecté). On ne pilote pas LinkedIn en direct depuis le cloud (bloqué, et risque pour le compte LinkedIn).
- **salesnav-slicer** (github.com/zoxeavv/salesnav-slicer, d'un collègue) : découpe une recherche Sales Navigator **d'entreprises** trop grosse (≥ 1 000 résultats) en sous-recherches exportables, en pilotant Chrome. Il ne récupère pas les listes. Il s'utilise depuis Claude sur l'ordinateur de Flavien (Chrome), pas dans cette session cloud.
- **Pipecorn** : serveur MCP officiel `https://mcp.pipecorn.com/mcp` (clé dans l'en-tête `X-API-Key`). Déclaré dans `.mcp.json` à la racine ; il fonctionnera quand (1) la variable `PIPECORN_API_KEY` sera dans les secrets de l'environnement et (2) `mcp.pipecorn.com` sera autorisé dans le réseau.
- **Minari** : clé à mettre dans les secrets de l'environnement sous `MINARI_API_KEY`, jamais dans le chat (une clé collée le 24/10 doit être régénérée par Flavien).
- **Nommage des listes dans Google Sheets** : convention à valider par Flavien.

### Accès constatés le 24/10/2026 (à revérifier en début de session)

- **Bloqués** par le réglage réseau de l'environnement cloud : ScrapingBee, Pipecorn (dont mcp.pipecorn.com), Minari, LinkedIn, sites des entreprises (visite directe et outil de lecture web), annuaire officiel des entreprises (api.gouv), societe.com, api.airtable.com en direct.
- **Joignables** : API Google (Sheets/Drive, il faut un compte de service), recherche web intégrée (limitée), connecteur **Airtable** (utilisable par Claude), connecteur **Notion**.
- Connecteur **n8n Akiro** : installé côté claude.ai mais pas activé dans les sessions de ce dépôt. n8n ayant accès à Internet, il peut servir de **passerelle** (ScrapingBee, Pipecorn, Minari) si le réglage réseau reste bloqué.
- Débloquer en direct : menu de l'environnement cloud → Edit → Network access → ajouter les domaines (ScrapingBee, Pipecorn, Minari). Réglage grisé chez Flavien : probablement à faire par un administrateur de l'organisation claude.ai. Doc : https://code.claude.com/docs/en/cloud-environments#network-access
- Aucune clé API présente dans la session au 24/10.

### Questions ouvertes pour Flavien

Bloquantes :
1. Accès réseau : qui administre l'organisation claude.ai, peut-il autoriser ScrapingBee / Pipecorn / Minari ? Sinon, OK pour passer par n8n ?
2. Registre : OK pour Airtable, global avec colonne client ? Prospect déjà extrait pour un autre client : bloqué ou seulement signalé ? Durée de validité ?
3. Premier client test : lequel, avec un vrai export et le brief ?

Bientôt :
4. Un export type Pharow et un Sales Navigator (même 20 lignes) pour figer la lecture des colonnes.
5. Forme des exclusions envoyées par les clients (Excel CRM, liste d'entreprises, domaines…).
6. Google Sheets : import manuel ou compte de service ? Modèle de Sheet commun (case « validé » pour le client) ?
7. Comment le client valide aujourd'hui (supprime, colore, ajoute une colonne) ?
8. Le dépôt GitHub est-il bien privé ? (registre et exports contiennent des données personnelles.)

Plus tard : doc API Pipecorn et forfait ; doc API Minari et mapping par client ; volume mensuel ScrapingBee.

## Format de livraison

- CSV **UTF-8 avec BOM** (lisible dans Excel), séparateur **virgule**, une ligne par prospect.
- Colonnes d'origine conservées ; **nouvelles colonnes ajoutées à gauche**.
- Déposé dans `clients/<client>/propre/`.

## Arborescence

```
clients/
  _modele/                  modèle à copier pour un nouveau client
  <client>/
    contexte.md             cible et critères du client
    prompt_qualification.md prompt écrit par Claude, corrigé pendant la boucle de test
    brut/                   exports d'origine (Pharow, Sales Navigator) — jamais modifiés
    exclusions/             clients existants, en cours… (exclut les entreprises)
      personnes/            listes déjà appelées… (exclut seulement les personnes)
    travail/                fichiers intermédiaires (_prepare.csv, _verdicts.csv, cache des sites)
    propre/                 fichiers qualifiés livrés
registre/registre.csv       prospects déjà extraits, tous clients (en attendant Airtable)
scripts/
  lire_export.py            lecture CSV/Excel, repérage des colonnes
  normaliser.py             nettoyage prénom / nom / raison sociale, clés de comparaison
  dedoublonner.py           étape 4
  livrer.py                 calcul du Verdict, CSV livré, résumé
.claude/skills/             skills chargés automatiquement (akiro-onboarding, akiro-cleaning, cleaning-<client>)
.env                        clés API (jamais versionné)
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
