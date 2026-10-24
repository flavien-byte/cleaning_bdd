"""Étape 5 (fin) : assemble le fichier livré au client et son résumé.

Entrées :
  - le fichier préparé par dedoublonner.py (clients/<client>/travail/<nom>_prepare.csv) ;
  - le fichier de verdicts écrit pendant la qualification : une ligne par « ID ligne »,
    une colonne par critère (Oui / Non / À vérifier) et une colonne « Justification ».
    Il peut être partiel : les lignes absentes restent « À vérifier » (non qualifiées).

Le Verdict est calculé ici, jamais à la main : Oui si tous les critères sont Oui,
Non si l'un est Non, À vérifier sinon. Les doublons gardent le Verdict « Doublon ».

Usage :
    python3 scripts/livrer.py clients/<client>/travail/<nom>_prepare.csv
        [--verdicts clients/<client>/travail/<nom>_verdicts.csv]

Sortie : clients/<client>/propre/<nom>_qualifie.csv (UTF-8 avec BOM, virgule) + résumé.
"""

import argparse
from collections import Counter
from pathlib import Path

from lire_export import ecrire_csv, lire_csv_dicts, lire_fichier
from normaliser import cle_texte

RACINE = Path(__file__).resolve().parent.parent
VALEURS = {"oui": "Oui", "non": "Non", "a verifier": "À vérifier"}
COLONNES_TECHNIQUES = ["Statut", "Motif doublon", "Info registre"]  # le motif passe dans Justification


def normaliser_valeur(texte):
    return VALEURS.get(cle_texte(texte), "À vérifier")


def calculer_verdict(valeurs):
    if not valeurs:
        return "À vérifier"
    if "Non" in valeurs:
        return "Non"
    if all(v == "Oui" for v in valeurs):
        return "Oui"
    return "À vérifier"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prepare")
    parser.add_argument("--verdicts")
    args = parser.parse_args()

    prepare = Path(args.prepare).resolve()
    entetes, lignes = lire_fichier(prepare)
    criteres, verdicts = [], {}
    if args.verdicts:
        entetes_v, lignes_v = lire_csv_dicts(args.verdicts)
        criteres = [c for c in entetes_v if c not in ("ID ligne", "Justification", "Verdict")]
        verdicts = {r["ID ligne"]: r for r in lignes_v}

    i_id, i_statut, i_motif = (entetes.index(c) for c in ("ID ligne", "Statut", "Motif doublon"))
    a_garder = [i for i, e in enumerate(entetes) if e not in COLONNES_TECHNIQUES]
    nouvelles = ["Verdict"] + criteres + ["Justification"]

    sortie, compte, exclusions = [], Counter(), Counter()
    for ligne in lignes:
        if ligne[i_statut] == "Doublon":
            verdict, valeurs, justification = "Doublon", [""] * len(criteres), ligne[i_motif]
        else:
            r = verdicts.get(ligne[i_id])
            if r:
                valeurs = [normaliser_valeur(r.get(c, "")) for c in criteres]
                justification = r.get("Justification", "").strip()
            else:
                valeurs, justification = ["À vérifier"] * len(criteres), "Non qualifiée"
            verdict = calculer_verdict(valeurs)
            for critere, valeur in zip(criteres, valeurs):
                if valeur == "Non":
                    exclusions[critere] += 1
        compte[verdict] += 1
        sortie.append([verdict] + valeurs + [justification] + [ligne[i] for i in a_garder])

    nom = prepare.stem.removesuffix("_prepare")
    destination = prepare.parent.parent / "propre" / f"{nom}_qualifie.csv"
    ecrire_csv(destination, nouvelles + [entetes[i] for i in a_garder], sortie)

    print(f"Fichier livré : {destination.relative_to(RACINE)} ({len(sortie)} lignes)\n")
    for verdict in ("Oui", "Non", "À vérifier", "Doublon"):
        print(f"  {verdict:<11}: {compte[verdict]}")
    if exclusions:
        print("\nCritères les plus souvent à « Non » :")
        for critere, n in exclusions.most_common(5):
            print(f"  - {critere} : {n}")


if __name__ == "__main__":
    main()
