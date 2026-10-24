"""Étape 4 : nettoyage des noms et dédoublonnage, AVANT toute qualification ou appel payant.

Aucune ligne n'est supprimée : chaque ligne reçoit un Statut (« À qualifier » ou
« Doublon ») et, le cas échéant, un Motif doublon.

Contrôles, dans cet ordre :
  1. exclusions du client : tous les fichiers de clients/<client>/exclusions/
     (une entreprise listée exclut tous ses contacts ; un fichier rangé dans
     exclusions/personnes/ n'exclut que les personnes listées) ;
  2. registre central (prospects déjà extraits, tous clients confondus) ;
  3. doublons à l'intérieur du fichier.

Usage :
    python3 scripts/dedoublonner.py clients/<client>/brut/export.csv --client <client>
        [--registre registre/registre.csv] [--autres-clients bloquer|signaler]
        [--ajouter-au-registre] [--colonne poste="Job Title"]

Sortie : clients/<client>/travail/<nom du fichier>_prepare.csv
"""

import argparse
import datetime
from collections import Counter
from pathlib import Path

from lire_export import (decrire, ecrire_csv, extraire, lire_csv_dicts, lire_fichier,
                         reperer_colonnes)
from normaliser import (cle_email, cle_linkedin, cle_raison_sociale, cle_texte, domaine,
                        nettoyer_personne, nettoyer_raison_sociale, siren)

RACINE = Path(__file__).resolve().parent.parent
COLONNES_REGISTRE = ["linkedin", "email", "personne", "domaine", "siren", "raison_sociale",
                     "client", "date", "fichier"]
NOUVELLES_COLONNES = ["ID ligne", "Statut", "Motif doublon", "Info registre",
                      "Prénom (propre)", "Nom (propre)", "Raison sociale (propre)", "Domaine"]


def cles_entreprise(v):
    cles = set()
    if v.get("domaine"):
        cles.add("domaine:" + v["domaine"])
    if v.get("siren"):
        cles.add("siren:" + v["siren"])
    if v.get("raison_sociale"):
        cles.add("rs:" + v["raison_sociale"])
    return cles


def cles_personne(v):
    """URL LinkedIn, e-mail, et prénom + nom associés à chaque clé de l'entreprise."""
    cles = set()
    if v.get("linkedin"):
        cles.add("li:" + v["linkedin"])
    if v.get("email"):
        cles.add("mail:" + v["email"])
    if v.get("personne"):
        cles.update(f"nom:{v['personne']} @ {cle}" for cle in cles_entreprise(v))
    return cles


def preparer_ligne(brut):
    """Champs propres + clés de comparaison d'une ligne."""
    prenom, nom = nettoyer_personne(brut["prenom"]), nettoyer_personne(brut["nom"])
    return {
        "prenom_propre": prenom,
        "nom_propre": nom,
        "rs_propre": nettoyer_raison_sociale(brut["entreprise"]),
        "domaine": domaine(brut["site"]) or domaine(brut["email"]),
        "siren": siren(brut["siren"]),
        "raison_sociale": cle_raison_sociale(brut["entreprise"]),
        "linkedin": cle_linkedin(brut["linkedin"]),
        "email": cle_email(brut["email"]),
        "personne": cle_texte(f"{prenom} {nom}") if prenom and nom else "",
    }


def motif_fichier(chemin):
    return chemin.stem.replace("_", " ").replace("-", " ").strip()


def charger_exclusions(dossier):
    """Index clé -> motif, construit à partir des fichiers d'exclusion du client."""
    index = {}
    if not dossier.is_dir():
        return index
    for chemin in sorted(dossier.rglob("*")):
        if chemin.suffix.lower() not in (".csv", ".xlsx", ".xlsm", ".txt"):
            continue
        personnes_seulement = chemin.parent.name == "personnes"
        entetes, lignes = lire_fichier(chemin)
        colonnes = reperer_colonnes(entetes)
        motif = f"Exclusion client ({motif_fichier(chemin)})"
        if not any(i is not None for i in colonnes.values()):
            # Liste brute sans en-tête reconnu : domaines ou noms d'entreprises.
            for valeur in [entetes[0]] + [l[0] for l in lignes]:
                dom = domaine(valeur)
                v = {"domaine": dom} if dom else {"raison_sociale": cle_raison_sociale(valeur)}
                for cle in cles_entreprise(v):
                    index.setdefault(cle, (motif, "entreprise"))
            continue
        for ligne in lignes:
            v = preparer_ligne(extraire(ligne, colonnes))
            for cle in cles_personne(v):
                index.setdefault(cle, (motif, "personne"))
            if not personnes_seulement:
                for cle in cles_entreprise(v):
                    index.setdefault(cle, (motif, "entreprise"))
    return index


def charger_registre(chemin, fichier_courant, client):
    """Index clé -> (client, date, type), hors lignes issues de ce même fichier."""
    personnes, entreprises = {}, {}
    if not chemin or not Path(chemin).exists():
        return personnes, entreprises
    _, lignes = lire_csv_dicts(chemin)
    for r in lignes:
        if r.get("fichier") == fichier_courant and r.get("client") == client:
            continue  # relance sur le même fichier : pas un doublon
        info = (r.get("client", ""), r.get("date", ""))
        for cle in cles_personne(r):
            personnes.setdefault(cle, info)
        for cle in cles_entreprise(r):
            entreprises.setdefault(cle, info)
    return personnes, entreprises


def date_fr(iso):
    try:
        return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("export")
    parser.add_argument("--client", required=True)
    parser.add_argument("--registre", default=str(RACINE / "registre" / "registre.csv"))
    parser.add_argument("--autres-clients", choices=["bloquer", "signaler"], default="bloquer",
                        help="Prospect déjà extrait pour un AUTRE client : doublon (bloquer) ou simple mention (signaler).")
    parser.add_argument("--ajouter-au-registre", action="store_true",
                        help="Ajoute les prospects « À qualifier » de ce fichier au registre.")
    parser.add_argument("--colonne", action="append", default=[],
                        help="Forcer une colonne : champ=Entête (champs : prenom, nom, poste, entreprise, site, linkedin, email, siren).")
    args = parser.parse_args()

    export = Path(args.export).resolve()
    dossier_client = RACINE / "clients" / args.client
    if not dossier_client.is_dir():
        raise SystemExit(f"Dossier client introuvable : {dossier_client}")

    forcees = dict(c.split("=", 1) for c in args.colonne)
    entetes, lignes = lire_fichier(export)
    colonnes = reperer_colonnes(entetes, forcees)
    print(f"{export.name} : {len(lignes)} lignes.\nColonnes repérées :\n{decrire(entetes, colonnes)}\n")

    exclusions = charger_exclusions(dossier_client / "exclusions")
    reg_personnes, reg_entreprises = charger_registre(args.registre, export.name, args.client)

    vus = {}  # clé personne -> numéro de la première ligne
    sortie, ajouts, motifs = [], [], Counter()
    for numero, ligne in enumerate(lignes, start=1):
        v = preparer_ligne(extraire(ligne, colonnes))
        k_pers, k_ent = cles_personne(v), cles_entreprise(v)
        motif, categorie, info = "", "", ""

        for cle in sorted(k_pers) + sorted(k_ent):
            if cle in exclusions:
                source, niveau = exclusions[cle]
                motif = categorie = f"{source} : même {niveau}"
                break
        if not motif:
            for cle in sorted(k_pers):
                if cle in reg_personnes:
                    client, date = reg_personnes[cle]
                    texte = f"Déjà extrait le {date_fr(date)} pour {client}"
                    if client == args.client or args.autres_clients == "bloquer":
                        motif, categorie = "Doublon : " + texte, f"Déjà extrait pour {client}"
                    else:
                        info = texte
                    break
        if not motif:
            for cle in sorted(k_pers):
                if cle in vus:
                    motif = f"Doublon : même personne que la ligne {vus[cle]}"
                    categorie = "Doublon dans le fichier"
                    break
        if not info:
            for cle in sorted(k_ent):
                if cle in reg_entreprises:
                    client, date = reg_entreprises[cle]
                    info = f"Entreprise déjà extraite le {date_fr(date)} pour {client}"
                    break
        if not motif:
            for cle in k_pers:
                vus.setdefault(cle, numero)

        statut = "Doublon" if motif else "À qualifier"
        if motif:
            motifs[categorie] += 1
        else:
            ajouts.append(v)
        sortie.append([str(numero), statut, motif, info, v["prenom_propre"], v["nom_propre"],
                       v["rs_propre"], v["domaine"]] + ligne)

    destination = dossier_client / "travail" / f"{export.stem}_prepare.csv"
    ecrire_csv(destination, NOUVELLES_COLONNES + entetes, sortie)

    print(f"À qualifier : {len(ajouts)}")
    print(f"Doublons    : {len(lignes) - len(ajouts)}")
    for motif, n in motifs.most_common():
        print(f"  - {motif} : {n}")
    print(f"\nFichier écrit : {destination.relative_to(RACINE)}")

    if args.ajouter_au_registre:
        chemin = Path(args.registre).resolve()
        existantes = []
        if chemin.exists():
            _, anciennes = lire_csv_dicts(chemin)
            existantes = [[r.get(c, "") for c in COLONNES_REGISTRE] for r in anciennes
                          if not (r.get("fichier") == export.name and r.get("client") == args.client)]
        aujourd_hui = datetime.date.today().isoformat()
        nouvelles = [[v[c] for c in COLONNES_REGISTRE[:6]] + [args.client, aujourd_hui, export.name]
                     for v in ajouts]
        ecrire_csv(chemin, COLONNES_REGISTRE, existantes + nouvelles)
        print(f"Registre : {len(nouvelles)} prospects ajoutés ({chemin.relative_to(RACINE)}).")


if __name__ == "__main__":
    main()
