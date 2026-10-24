"""Nettoyage et normalisation des champs prospects.

Deux usages :
- « propre » : valeurs lisibles livrées au client (Jean-Pierre Dupont, Akiro) ;
- « clé » : valeurs comparables pour le dédoublonnage (jean pierre dupont, akiro).
"""

import re
import unicodedata
from urllib.parse import urlparse

FORMES_JURIDIQUES = [
    "sas", "sasu", "sarl", "eurl", "sa", "snc", "sci", "scop", "scp", "scm",
    "selarl", "selas", "selafa", "sca", "gie", "ei", "eirl", "sem", "spa",
    "ltd", "limited", "llc", "inc", "gmbh", "bv", "nv", "srl", "sl", "plc",
]
_FORMES = "|".join(FORMES_JURIDIQUES)
# Forme juridique isolée (« SAS », « S.A.S. », « (SARL) »), en début ou en fin de nom.
RE_FORME_FIN = re.compile(rf"[\s,\-–(]*\b({_FORMES})\b\.?\)?\s*$", re.IGNORECASE)
RE_FORME_DEBUT = re.compile(rf"^\(?\b({_FORMES})\b\.?\)?[\s,\-–]+", re.IGNORECASE)
RE_SIGLE_POINTE = re.compile(r"\b((?:[A-Za-z]\.){2,})(?=\s|$|,|\))")

PARTICULES = {"de", "du", "des", "la", "le", "d", "van", "von", "der", "den", "di", "da", "del"}

DOMAINES_GENERIQUES = {
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "google.com", "sites.google.com", "wixsite.com", "gmail.com",
    "hotmail.com", "hotmail.fr", "outlook.com", "outlook.fr", "yahoo.com",
    "yahoo.fr", "orange.fr", "wanadoo.fr", "free.fr", "sfr.fr", "laposte.net",
    "icloud.com", "live.fr", "live.com", "pagesjaunes.fr", "societe.com",
}

RE_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F900-\U0001F9FF‍️]"
)


def sans_accents(texte):
    texte = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in texte if not unicodedata.combining(c))


def cle_texte(texte):
    """Minuscules, sans accents, sans ponctuation, espaces simples."""
    texte = sans_accents(texte or "").lower()
    texte = re.sub(r"[^a-z0-9]+", " ", texte)
    return texte.strip()


def _est_en_majuscules(texte):
    lettres = [c for c in texte if c.isalpha()]
    return bool(lettres) and all(c.isupper() for c in lettres)


def _est_en_minuscules(texte):
    lettres = [c for c in texte if c.isalpha()]
    return bool(lettres) and all(c.islower() for c in lettres)


def _capitaliser_mot(mot):
    # Gère Jean-Pierre, O'Brien, D'Artagnan.
    morceaux = re.split(r"([\-'’])", mot)
    return "".join(m[:1].upper() + m[1:].lower() if m.isalpha() else m for m in morceaux)


def nettoyer_personne(texte):
    """Prénom ou nom : retire emojis, titres et mentions parasites, corrige la casse."""
    texte = RE_EMOJI.sub("", texte or "")
    texte = re.sub(r"\(.*?\)|\[.*?\]", "", texte)  # (PhD), [Recrutement]
    texte = texte.split(",")[0].split("|")[0]       # « Dupont, MBA », « Dupont | CEO »
    texte = re.sub(r"\s+", " ", texte).strip(" -–.")
    if not texte:
        return ""
    if not (_est_en_majuscules(texte) or _est_en_minuscules(texte)):
        return texte  # casse déjà mixte (McDonald, de La Tour) : on n'y touche pas
    mots = texte.split(" ")
    resultat = []
    for i, mot in enumerate(mots):
        if i > 0 and mot.lower() in PARTICULES:
            resultat.append(mot.lower())
        else:
            resultat.append(_capitaliser_mot(mot))
    return " ".join(resultat)


def retirer_forme_juridique(texte):
    texte = texte or ""
    # « S.A.S. » -> « SAS » pour que la forme soit reconnue.
    texte = RE_SIGLE_POINTE.sub(lambda m: m.group(1).replace(".", ""), texte)
    for _ in range(2):  # « SAS SOCIETE X SARL » : début et fin
        texte = RE_FORME_FIN.sub("", texte)
        texte = RE_FORME_DEBUT.sub("", texte)
    return texte.strip(" ,-–")


def nettoyer_raison_sociale(texte):
    """Raison sociale lisible : sans forme juridique, sans MAJUSCULES intégrales."""
    texte = RE_EMOJI.sub("", texte or "")
    texte = re.sub(r"\s+", " ", texte).strip()
    texte = retirer_forme_juridique(texte)
    if not _est_en_majuscules(texte):
        return texte
    mots = []
    for mot in texte.split(" "):
        lettres = re.sub(r"[^A-Za-z]", "", sans_accents(mot))
        # Sigles courts conservés : BNP, EDF, 3M.
        mots.append(mot if len(lettres) <= 3 else _capitaliser_mot(mot))
    return " ".join(mots)


def cle_raison_sociale(texte):
    return cle_texte(retirer_forme_juridique(texte))


def domaine(texte):
    """Domaine d'un site ou d'un e-mail : « https://www.Akiro.fr/contact » -> « akiro.fr »."""
    texte = (texte or "").strip().lower()
    if not texte or texte in {"introuvable", "n/a", "na", "-", "none"}:
        return ""
    if "@" in texte and "/" not in texte:
        texte = texte.rsplit("@", 1)[1]
    if "://" not in texte:
        texte = "http://" + texte
    hote = urlparse(texte).hostname or ""
    hote = re.sub(r"^www\d*\.", "", hote).strip(".")
    if "." not in hote:
        return ""
    if hote in DOMAINES_GENERIQUES or any(hote.endswith("." + g) for g in DOMAINES_GENERIQUES):
        return ""
    return hote


def cle_linkedin(texte):
    """Identifiant stable d'un profil LinkedIn (profil public ou lien Sales Navigator)."""
    texte = (texte or "").strip()
    m = re.search(r"linkedin\.com/in/([^/?#\s]+)", texte, re.IGNORECASE)
    if m:
        return "in:" + m.group(1).lower().rstrip("/")
    m = re.search(r"linkedin\.com/sales/(?:lead|people)/([^,/?#\s]+)", texte, re.IGNORECASE)
    if m:
        return "sales:" + m.group(1)
    return ""


def cle_email(texte):
    texte = (texte or "").strip().lower()
    return texte if re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", texte) else ""


def siren(texte):
    chiffres = re.sub(r"\D", "", texte or "")
    return chiffres[:9] if len(chiffres) in (9, 14) else ""
