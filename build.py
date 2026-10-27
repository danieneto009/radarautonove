#!/usr/bin/env python3
"""Gera as páginas de edição diária e o sitemap do Radar Autonove.

Lê as notícias do bloco <script id="news-data"> do index.html e cria:
  - edicao/AAAA-MM-DD/index.html  (uma página estática por dia, indexável)
  - edicao/index.html             (arquivo com todas as edições)
  - sitemap.xml                   (home + arquivo + todas as edições)

Uso: python3 build.py   (roda sozinho no GitHub Actions a cada push)
"""
import html
import json
import os
import re
import shutil
from collections import defaultdict
from datetime import date

SITE = "https://radarautonove.com.br"
ROOT = os.path.dirname(os.path.abspath(__file__))
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
               "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

e = lambda s: html.escape(str(s or ""), quote=True)


def d_obj(k):
    y, m, d = map(int, k.split("-"))
    return date(y, m, d)


def curto(k):
    d = d_obj(k)
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def longo(k):
    d = d_obj(k)
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES_LONGO[d.month - 1]} de {d.year}"


def load():
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<script id="news-data" type="application/json">(.*?)</script>', src, re.S)
    news = json.loads(m.group(1))
    # Reaproveita o CSS principal da home para manter a mesma identidade visual
    styles = re.findall(r"<style>(.*?)</style>", src, re.S)
    css = max(styles, key=len)
    return news, css


EXTRA_CSS = """
.crumbs{font-size:13px;color:var(--muted);margin-top:22px}
.crumbs a,.pager a,.arch a{color:var(--plate);font-weight:600;text-decoration:none}
:root[data-theme="dark"] .crumbs a,:root[data-theme="dark"] .pager a,:root[data-theme="dark"] .arch a{color:var(--world)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .crumbs a,:root:not([data-theme="light"]) .pager a,:root:not([data-theme="light"]) .arch a{color:var(--world)}}
.crumbs a:hover,.pager a:hover,.arch a:hover{text-decoration:underline}
.plate-link{color:inherit;text-decoration:none}
.pager{margin-top:30px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:14px}
.arch{list-style:none;padding:0;margin:24px 0 0;display:grid;gap:10px}
.arch li{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:14px 18px;display:flex;flex-direction:column;gap:4px}
.arch .when{font:700 18px/1.1 var(--display);letter-spacing:.04em;text-transform:uppercase}
.arch .sub{font-size:13.5px;color:var(--muted)}
"""


def page(title, desc, canonical, css, body, ld):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Radar Autonove">
<meta property="og:locale" content="pt_BR">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap">
<style>body{{margin:0}}{css}{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap">
{body}
  <footer>Resumos escritos a partir das fontes citadas; clique em cada link para ler a matéria completa. <a href="/">Edição de hoje</a> · <a href="/edicao/">Todas as edições</a></footer>
</div>
</body>
</html>
"""


def mast(edition_label, sub):
    return f"""  <header class="mast">
    <a class="plate-link" href="/"><div class="plate">
      <div class="band"><span>BR · Mercosul</span><span>Notícias automotivas</span></div>
      <h1>Radar Autonove</h1>
    </div></a>
    <div class="edition"><strong>{e(edition_label)}</strong>{e(sub)}</div>
  </header>"""


def article(n):
    lead = n.get("lead")
    region = "br" if n.get("region") == "br" else "mundo"
    loj = (f'<div class="lojista"><b>Para o lojista · </b>{e(n["lojista"])}</div>'
           if n.get("lojista") else "")
    return (f'<article class="{"lead" if lead else ""}"><div class="meta">'
            f'<span class="tag {region}">{"Brasil" if region == "br" else "Mundo"}</span>'
            f'<span>{e(n.get("cat"))}</span></div>'
            f'<h3>{e(n.get("title"))}</h3><p>{e(n.get("text"))}</p>{loj}'
            f'<div class="src">Fonte: <a href="{e(n.get("url"))}" target="_blank" rel="noopener">'
            f'{e(n.get("src"))} ↗</a></div></article>')


def build():
    news, css = load()
    by_day = defaultdict(list)
    for n in news:
        by_day[n["date"]].append(n)
    days = sorted(by_day, reverse=True)  # mais recente primeiro

    out_dir = os.path.join(ROOT, "edicao")
    # Recria do zero para não deixar edições órfãs
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    for i, k in enumerate(days):
        items = sorted(by_day[k], key=lambda n: 0 if n.get("lead") else 1)
        leads = [n for n in items if n.get("lead")] or items
        url = f"{SITE}/edicao/{k}/"
        title = f"Notícias automotivas de {curto(k)} · Radar Autonove"
        desc = (f"Edição de {longo(k)}: {leads[0]['title']}. "
                f"{len(items)} notícias do Brasil e do mundo com leitura para o lojista de seminovos.")
        if len(desc) > 300:
            desc = desc[:297].rsplit(" ", 1)[0] + "…"
        newer = days[i - 1] if i > 0 else None
        older = days[i + 1] if i + 1 < len(days) else None
        pager = '<nav class="pager" aria-label="Outras edições">'
        pager += (f'<a href="/edicao/{older}/">← {e(curto(older))}</a>' if older else "<span></span>")
        pager += (f'<a href="/edicao/{newer}/">{e(curto(newer))} →</a>' if newer
                  else '<a href="/">Edição de hoje →</a>')
        pager += "</nav>"
        body = (mast(curto(k), "Edição diária · Brasil e mundo") +
                f'\n  <p class="crumbs"><a href="/">Início</a> › <a href="/edicao/">Edições</a> › {e(curto(k))}</p>'
                f'\n  <main><section class="day"><h2>{e(longo(k))}</h2><div class="grid">'
                + "".join(article(n) for n in items) + "</div></section></main>\n  " + pager)
        ld = {
            "@context": "https://schema.org", "@type": "CollectionPage",
            "name": title, "url": url, "inLanguage": "pt-BR", "datePublished": k,
            "isPartOf": {"@type": "WebSite", "name": "Radar Autonove", "url": SITE + "/"},
            "publisher": {"@type": "Organization", "name": "Autonove Multimarcas"},
            "mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": j + 1, "name": n["title"], "url": n["url"]}
                for j, n in enumerate(items)]},
        }
        d = os.path.join(out_dir, k)
        os.makedirs(d)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(title, desc, url, css, body, ld))

    # Página de arquivo
    lis = []
    for k in days:
        items = by_day[k]
        lead = next((n for n in items if n.get("lead")), items[0])
        lis.append(f'<li><a class="when" href="/edicao/{k}/">{e(longo(k))}</a>'
                   f'<span class="sub">{len(items)} notícias · {e(lead["title"])}</span></li>')
    title = "Todas as edições · Radar Autonove"
    desc = "Arquivo de todas as edições diárias do Radar Autonove: notícias automotivas do Brasil e do mundo."
    body = (mast(f"{len(days)} edições", "Arquivo · Brasil e mundo") +
            '\n  <p class="crumbs"><a href="/">Início</a> › Edições</p>'
            '\n  <main><ul class="arch">' + "".join(lis) + "</ul></main>")
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title,
          "url": f"{SITE}/edicao/", "inLanguage": "pt-BR",
          "isPartOf": {"@type": "WebSite", "name": "Radar Autonove", "url": SITE + "/"}}
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(title, desc, f"{SITE}/edicao/", css, body, ld))

    # Sitemap
    latest = days[0] if days else date.today().isoformat()
    urls = [(f"{SITE}/", latest, "daily", "1.0"), (f"{SITE}/edicao/", latest, "daily", "0.8")]
    urls += [(f"{SITE}/edicao/{k}/", k, "monthly", "0.6") for k in days]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, cf, pr in urls:
        xml.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lm}</lastmod>\n"
                   f"    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>")
    xml.append("</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(xml))

    print(f"{len(days)} edições geradas; sitemap com {len(urls)} URLs.")


if __name__ == "__main__":
    build()
