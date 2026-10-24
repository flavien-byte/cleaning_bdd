"""Lecture des fichiers (CSV ou Excel) et repérage des colonnes utiles.

Les exports Pharow, Sales Navigator et les fichiers d'exclusion des clients n'ont pas
les mêmes noms de colonnes : on les ramène à des champs communs (prenom, nom, poste,
entreprise, site, linkedin, email, siren).

Usage pour vérifier un fichier :
    python3 scripts/lire_export.py clients/<client>/brut/export.csv
"""

import csv
import io
import sys
from pathlib import Path

from normaliser import cle_texte

# Noms de colonnes reconnus, comparés après cle_texte() (minuscules, sans accents).
SYNONYMES = {
    "prenom": ["prenom", "first name", "firstname", "given name", "contact first name"],
    "nom": ["nom", "nom de famille", "last name", "lastname", "surname", "family name",
            "contact last name"],
    "nom_complet": ["nom complet", "full name", "fullname", "contact name", "name",
                    "lead name"],
    "poste": ["poste", "intitule", "intitule de poste", "intitule du poste", "job title",
              "title", "titre", "fonction", "position", "current title", "role"],
    "entreprise": ["entreprise", "societe", "raison sociale", "nom de l entreprise",
                   "nom entreprise", "company", "company name", "organization",
                   "organisation", "account name", "account", "current company"],
    "site": ["site", "site web", "site internet", "website", "company website",
             "url du site", "site de l entreprise", "domaine", "domain", "company domain",
             "website url", "company url"],
    "linkedin": ["linkedin", "url linkedin", "linkedin url", "profil linkedin",
                 "linkedin profile", "linkedin profile url", "person linkedin url",
                 "profile url", "lead url", "sales navigator url", "linkedin sales url"],
    "email": ["email", "e mail", "mail", "adresse email", "adresse e mail", "work email",
              "email address"],
    "siren": ["siren", "siret", "numero siren", "numero siret"],
}

MOTS_ENTREPRISE = ("company", "entreprise", "societe", "organization", "account")


def lire_fichier(chemin):
    """Renvoie (entetes, lignes) ; chaque ligne est une liste de textes."""
    chemin = Path(chemin)
    if chemin.suffix.lower() in (".xlsx", ".xlsm"):
        return _lire_excel(chemin)
    return _lire_csv(chemin)


def _lire_csv(chemin):
    brut = chemin.read_bytes()
    for encodage in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texte = brut.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    echantillon = texte[:20000]
    try:
        dialecte = csv.Sniffer().sniff(echantillon, delimiters=",;\t|")
    except csv.Error:
        dialecte = csv.excel
    lignes = [l for l in csv.reader(io.StringIO(texte), dialecte) if any(c.strip() for c in l)]
    if not lignes:
        return [], []
    entetes = [e.strip() for e in lignes[0]]
    largeur = len(entetes)
    corps = [(l + [""] * largeur)[:largeur] for l in lignes[1:]]
    return entetes, corps


def _lire_excel(chemin):
    import openpyxl  # pip install openpyxl

    classeur = openpyxl.load_workbook(chemin, read_only=True, data_only=True)
    feuille = classeur.worksheets[0]
    lignes = []
    for ligne in feuille.iter_rows(values_only=True):
        valeurs = ["" if v is None else str(v).strip() for v in ligne]
        if any(valeurs):
            lignes.append(valeurs)
    if not lignes:
        return [], []
    largeur = max(len(l) for l in lignes)
    lignes = [(l + [""] * largeur)[:largeur] for l in lignes]
    return lignes[0], lignes[1:]


def ecrire_csv(chemin, entetes, lignes):
    """Format de livraison Akiro : UTF-8 avec BOM (lisible dans Excel), séparateur virgule."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        ecrivain = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        ecrivain.writerow(entetes)
        ecrivain.writerows(lignes)


def lire_csv_dicts(chemin):
    """Lit un CSV produit par nos scripts en liste de dictionnaires."""
    entetes, lignes = lire_fichier(chemin)
    return entetes, [dict(zip(entetes, l)) for l in lignes]


def reperer_colonnes(entetes, forcees=None):
    """Associe chaque champ commun à l'index d'une colonne (ou None)."""
    cles = [cle_texte(e) for e in entetes]
    trouvees = {}
    for champ, synonymes in SYNONYMES.items():
        trouvees[champ] = None
        for synonyme in synonymes:  # 1) nom exact
            if synonyme in cles:
                trouvees[champ] = cles.index(synonyme)
                break
    # 2) nom approchant, pour les champs non trouvés
    for i, cle in enumerate(cles):
        if trouvees["linkedin"] is None and "linkedin" in cle and not any(m in cle for m in MOTS_ENTREPRISE):
            trouvees["linkedin"] = i
        if trouvees["site"] is None and ("website" in cle or "site web" in cle):
            trouvees["site"] = i
        if trouvees["email"] is None and "email" in cle:
            trouvees["email"] = i
    # « name » seul ne vaut nom complet que s'il n'y a pas de colonnes prénom / nom.
    if trouvees["prenom"] is not None and trouvees["nom"] is not None:
        trouvees["nom_complet"] = None
    for champ, entete in (forcees or {}).items():
        if entete not in entetes:
            raise SystemExit(f"Colonne « {entete} » introuvable dans le fichier.")
        trouvees[champ] = entetes.index(entete)
    return trouvees


def extraire(ligne, colonnes):
    """Dictionnaire champ -> valeur pour une ligne."""
    valeurs = {c: (ligne[i].strip() if i is not None else "") for c, i in colonnes.items()}
    if not valeurs["prenom"] and not valeurs["nom"] and valeurs["nom_complet"]:
        prenom, _, nom = valeurs["nom_complet"].partition(" ")
        valeurs["prenom"], valeurs["nom"] = prenom, nom
    return valeurs


def decrire(entetes, colonnes):
    lignes = []
    for champ, i in colonnes.items():
        lignes.append(f"  {champ:<12} -> {entetes[i] if i is not None else '(absente)'}")
    return "\n".join(lignes)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    entetes, lignes = lire_fichier(sys.argv[1])
    print(f"{len(lignes)} lignes, {len(entetes)} colonnes.")
    print("Colonnes repérées :")
    print(decrire(entetes, reperer_colonnes(entetes)))
