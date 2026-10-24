---
name: akiro-onboarding
description: Onboarding d'un nouveau client Akiro — transforme le transcript du kickoff et le brief en contexte.md, liste les questions manquantes, propose les filtres Sales Navigator / Pharow et écrit le prompt de qualification. Déclencher quand Flavien dit « nouveau client », « voici le kickoff de … », « voici le brief de … », « onboarde … », « prépare la cible de … ».
---

# Onboarding d'un nouveau client

Étapes 1 et 2 de la machine (voir `CLAUDE.md`). Aucun accès externe nécessaire.

## 1. Créer le dossier client

- Nom de dossier : minuscules, sans accents, tirets (`clients/maison-dupont/`).
- Copier `clients/_modele/` (contexte.md, prompt_qualification.md, brut/, exclusions/, travail/, propre/).

## 2. Remplir `contexte.md` depuis le kickoff et le brief

Sources, par ordre d'importance :
- **le transcript du kickoff** (appel de lancement avec le client) : collé par Flavien, ou
  retrouvé dans Notion (notes de réunion) s'il y est. L'enregistrer tel quel dans
  `clients/<client>/kickoff.md` (jamais résumé à la place de l'original) ;
- le brief écrit, les mails, le site du client, une ancienne liste validée ;
- les listes fournies par le client : **wishlist** (comptes qu'il veut absolument),
  **no-go** (comptes interdits : clients, concurrents, partenaires, déjà en cours).

Dans le transcript, relever en particulier :
- les intitulés cités comme bons et ceux écartés (« pas les RH », « surtout pas les acheteurs ») ;
- secteurs, tailles, zones, et les exceptions dites en passant (« sauf la grande distribution ») ;
- les noms d'entreprises cités (wishlist, no-go, concurrents, clients actuels) ;
- les exemples de clients idéaux du client : ils servent d'exemples « Oui » dans le prompt.
Citer la phrase du transcript à côté de chaque règle tirée de l'appel, pour pouvoir la retrouver.

Remplir chaque section avec ce qui est explicite. Ne rien inventer : ce qui manque devient
une question. Les listes wishlist / no-go vont dans `exclusions/` (no-go) et dans `contexte.md`.

## 3. Questions manquantes (une seule liste, à la fin)

Vérifier systématiquement :
- intitulés **refusés** (souvent oubliés) et intitulés ambigus (« Manager », « Responsable ») ;
- taille : effectif ou CA, bornes min/max ;
- zone : France entière, régions, DOM-TOM, Belgique/Suisse ;
- B2B obligatoire ? Les franchises, réseaux, administrations, associations sont-ils dans la cible ?
- concurrents à exclure (noms ET sites) ;
- fichiers d'exclusion : clients existants, prospects en cours, listes déjà appelées ;
- volume visé (nombre de prospects) et date de démarrage des appels.

## 4. Filtres de recherche

Proposer, prêts à copier :
- Sales Navigator : intitulés (requête booléenne `("Directeur commercial" OR "DAF") NOT stagiaire`),
  fonction, niveau hiérarchique, secteurs, effectif, zone, « a changé de poste », etc. ;
- Pharow : les mêmes critères dans ses filtres (NAF en indice seulement).
Noter les filtres retenus dans `contexte.md` (section dédiée).
Ne jamais inventer un identifiant de filtre Sales Navigator (secteur, zone…) : partir d'une URL
réelle créée par Flavien et la modifier. Si une recherche dépasse la limite d'export, le skill
`salesnav-slicer` (dépôt github.com/zoxeavv/salesnav-slicer) la découpe en sous-recherches ;
il pilote Chrome, donc il s'utilise depuis Claude sur l'ordinateur de Flavien, pas dans le cloud.

## 5. Prompt de qualification

Remplir `clients/<client>/prompt_qualification.md` à partir du modèle :
- un critère par ligne de la cible (intitulé, secteur, B2B, taille, zone, concurrent…), chacun
  répondant Oui / Non / À vérifier, avec des exemples concrets d'acceptés / refusés ;
- le site tranche, le déclaratif n'est qu'un indice ;
- format de sortie : une ligne CSV `ID ligne,<critères…>,Justification`.
Ce prompt sera ajusté pendant la boucle de test (skill `akiro-cleaning`).

## 6. Fin

Résumer à Flavien en quelques lignes : cible retenue, critères, questions ouvertes, et ce qu'il
doit déposer (export dans `brut/`, fichiers d'exclusion dans `exclusions/`).
