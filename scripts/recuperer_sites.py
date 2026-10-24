"""Étape 5 (début) : récupère le texte des sites des entreprises, une seule fois par domaine.

Pour chaque domaine du fichier préparé : page d'accueil + jusqu'à 4 pages équipe / contact /
cabinet / qui sommes-nous. Visite directe d'abord (gratuite), ScrapingBee en secours
(clé ajoutée par le proxy). Cache : un fichier texte par domaine ; un domaine déjà en cache
n'est jamais re-téléchargé (donc jamais repayé).

Usage :
    python3 scripts/recuperer_sites.py clients/<client>/travail/<nom>_prepare.csv clients/<client>/travail/sites
"""
import csv, re, sys, json, urllib.parse, concurrent.futures as cf
from pathlib import Path
import requests
from html.parser import HTMLParser

prep, outdir = Path(sys.argv[1]), Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
MOTS = re.compile(r"equipe|équipe|team|associ|qui-sommes|qui_sommes|a-propos|about|cabinet|contact|nous|implantation|agence|bureau", re.I)

class P(HTMLParser):
    def __init__(s): super().__init__(); s.t=[]; s.l=[]; s.skip=0
    def handle_starttag(s, tag, a):
        if tag in ("script","style","noscript","svg"): s.skip+=1
        if tag=="a":
            h=dict(a).get("href"); 
            if h: s.l.append(h)
    def handle_endtag(s, tag):
        if tag in ("script","style","noscript","svg") and s.skip: s.skip-=1
    def handle_data(s, d):
        if not s.skip and d.strip(): s.t.append(d.strip())

def get(url):
    try:
        r = requests.get(url, headers=UA, timeout=20, allow_redirects=True)
        if r.status_code < 400 and "html" in r.headers.get("content-type","html"):
            r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower()=="iso-8859-1" else r.encoding
            return r.url, r.text
    except Exception as e:
        return None, None
    return None, None

def scrapingbee(url):
    try:
        r = requests.get("https://app.scrapingbee.com/api/v1/", params={"url": url, "render_js": "false"}, timeout=60)
        if r.status_code < 400: return url, r.text
    except Exception: pass
    return None, None

def parse(html):
    p=P(); 
    try: p.feed(html)
    except Exception: pass
    return " ".join(p.t), p.l

def traite(dom, url):
    f = outdir / f"{dom}.txt"
    if f.exists(): return dom, "cache"
    if not url.startswith("http"): url = "https://" + url
    final, html = get(url)
    via = "direct"
    if not html:
        final, html = scrapingbee(url); via = "scrapingbee"
    if not html:
        f.write_text("SITE INACCESSIBLE : " + url, encoding="utf-8"); return dom, "echec"
    texte, liens = parse(html)
    pages = [f"=== {final}\n{texte[:5000]}"]
    vus = {final}
    base = urllib.parse.urlparse(final).netloc
    cand = []
    for h in liens:
        u = urllib.parse.urljoin(final, h).split("#")[0]
        if urllib.parse.urlparse(u).netloc == base and u not in vus and MOTS.search(urllib.parse.urlparse(u).path) and not re.search(r"\.(pdf|jpg|png)$", u, re.I):
            vus.add(u); cand.append(u)
    for u in cand[:4]:
        fu, h = get(u)
        if h: pages.append(f"=== {fu}\n{parse(h)[0][:3500]}")
    f.write_text("\n\n".join(pages)[:16000], encoding="utf-8")
    return dom, via

rows = list(csv.DictReader(open(prep, encoding="utf-8-sig")))
todo = {}
for r in rows:
    if r.get("Domaine") and r.get("Website"):
        todo.setdefault(r["Domaine"], r["Website"])
with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(lambda kv: traite(*kv), todo.items()))
from collections import Counter
print(len(todo), "domaines", Counter(v for _, v in res))
print([d for d, v in res if v == "echec"])
