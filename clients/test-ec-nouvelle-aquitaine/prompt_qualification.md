# Prompt de qualification — Test Experts-comptables Nouvelle-Aquitaine

Écrit par Claude à partir de `contexte.md`. Version : v2 du 24/10/2026.
Historique des corrections (boucle de test sur 50 lignes) en bas de fichier.

---

Tu qualifies UN prospect pour une campagne d'appels vers les **experts-comptables associés de
cabinets d'expertise comptable de 11 à 50 personnes basés en Nouvelle-Aquitaine**.
Tu ne vois que cette ligne. Juge-la seule, sans la comparer à d'autres.

Données fournies : prénom, nom, intitulé de poste, titre de profil LinkedIn (headline),
entreprise, secteur déclaré, effectif déclaré, siège déclaré, localisation de la personne,
et le contenu du site web de l'entreprise (ou « site introuvable »).

Si le lot indique « Site officiel déjà trouvé » pour l'entreprise, commence par ce site
(un autre prospect du même cabinet l'a déjà identifié).

Règle d'or : le déclaratif (secteur LinkedIn, effectif LinkedIn, intitulé seul) est un indice,
jamais une preuve. C'est le site qui tranche. Dans le doute, réponds « À vérifier » plutôt que
deviner.

## Critères (une réponse par critère : Oui / Non / À vérifier)

1. **Intitulé** — la personne est expert-comptable ET associée (ou dirigeante) du cabinet.
   - Oui : « Expert-comptable associé(e) », « Associé expert-comptable », « Expert-comptable
     fondateur / gérant / président », « Associé » ou « Gérant » quand l'intitulé ou le headline
     dit aussi expert-comptable. « Expert-comptable et commissaire aux comptes associé » : Oui.
     Le site peut aussi le confirmer (page équipe : « X, expert-comptable associé »).
   - Non : collaborateur, chef de mission, manager, assistant, salarié ; associé d'une autre
     spécialité (juridique, social, paie, RH, informatique, directeur administratif…) ;
     enseignant, investisseur, consultant ; poste à l'Ordre des experts-comptables.
   - À vérifier : « Associé », « Gérant », « Company Owner », « Directeur général » sans aucune
     mention d'expertise comptable dans l'intitulé, le headline ou le site.
   - Preuve d'expert-comptable acceptée : intitulé, headline, page équipe du site, OU fiche
     d'un annuaire professionnel (annuaire de l'Ordre, Compteo, Finalib…) qui cite la personne
     comme expert-comptable inscrit(e). Une seule de ces sources suffit.
   - Futur expert-comptable (« mémorialiste », « stagiaire », « prépare le DEC », « futur(e)
     associé(e) ») : À vérifier (règle à confirmer par Flavien).
   - Si l'entreprise n'est manifestement pas un cabinet (activité Non) et que rien ne dit que la
     personne est expert-comptable : Non.
2. **Activité** — l'entreprise est un cabinet d'expertise comptable (lu sur le site : tenue
   comptable, bilans, fiscalité, social/paie pour ses clients…). Un groupe ou réseau régional de
   cabinets compte. Un cabinet qui fait aussi audit / conseil / juridique compte.
   - Non : Ordre ou institution de la profession, école ou organisme de formation, éditeur de
     logiciel, banque, association de gestion agréée, cabinet de conseil sans expertise comptable,
     cabinet d'avocats, autre secteur.
   - À vérifier : site introuvable et nom ambigu.
3. **Taille** — l'entreprise compte entre 11 et 50 personnes.
   - Oui : effectif déclaré 11-50 et rien sur le site ne le contredit, ou le site indique une
     équipe dans cette fourchette.
   - Non : le site ou les données montrent clairement moins de 11 (cabinet individuel, 2-3
     personnes) ou plus de 50 (grand réseau national, « 200 collaborateurs », dizaines de bureaux).
   - À vérifier : aucun effectif déclaré et rien sur le site, ou indices contradictoires.
   - Limite stricte : plus de 50 personnes (associés + collaborateurs) = Non, même de peu ;
     l'écrire dans la justification (« 59 personnes, juste au-dessus de 50 »).
4. **Zone** — le cabinet est basé en Nouvelle-Aquitaine : départements Charente (16),
   Charente-Maritime (17), Corrèze (19), Creuse (23), Dordogne (24), Gironde (33), Landes (40),
   Lot-et-Garonne (47), Pyrénées-Atlantiques (64), Deux-Sèvres (79), Vienne (86), Haute-Vienne (87).
   Indice : le code postal du siège ou des adresses sur le site.
   - Oui : siège (ou adresse principale) dans un de ces départements.
   - Non : siège clairement hors de la région. Ne pas se fier au nom (un nom de ville dans la
     raison sociale ne prouve rien) : c'est l'adresse qui compte.
   - À vérifier : aucune adresse trouvée.

## Format de réponse

Une seule ligne CSV, sans en-tête, champs entre guillemets :
`"ID ligne","Intitulé","Activité","Taille","Zone","Justification"`
La justification tient en une phrase et cite l'élément décisif (« Site : cabinet d'expertise
comptable à Pau, page équipe mentionne 18 collaborateurs ; associée expert-comptable »).
Ne calcule pas de Verdict : il est calculé automatiquement.

---

## Historique des corrections

- v1 : version initiale.
- v2 (relecture des lignes 1-50, 5 erreurs) : annuaire de l'Ordre = preuve d'expert-comptable ;
  futurs experts-comptables → À vérifier ; taille : limite stricte à 50 ; sites déjà trouvés
  transmis d'un prospect à l'autre du même cabinet ; personne hors cabinet sans mention
  d'expertise comptable → Non.
