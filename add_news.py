#!/usr/bin/env python3
"""Insere uma nova edição de notícias no index.html do Radar Autonove.

Uso:
  python3 add_news.py nova_edicao.json            # adiciona (falha se a data já existir)
  python3 add_news.py nova_edicao.json --replace  # substitui as notícias daquela data

O JSON de entrada é uma lista de notícias, todas com a MESMA data, no formato:
  {"date": "AAAA-MM-DD", "region": "br"|"mundo", "cat": "...", "lead": true (opcional),
   "title": "...", "text": "...", "lojista": "...", "src": "...", "url": "https://..."}

Regras validadas: campos obrigatórios, região válida, URL http(s), exatamente um
destaque (lead) por região, sem URL repetida (nem com edições anteriores).
Depois de rodar, faça commit/push do index.html: o GitHub Actions gera as
páginas de edição e o sitemap sozinho.
"""
import json
import re
import sys
from datetime import date

INDEX = "index.html"
REQ = ["date", "region", "cat", "title", "text", "src", "url"]  # "lojista" é recomendado
ORDER = ["date", "region", "cat", "lead", "title", "text", "lojista", "src", "url"]
BLOCK = re.compile(r'(<script id="news-data" type="application/json">)(.*?)(</script>)', re.S)


def fail(msg):
    print("ERRO:", msg)
    sys.exit(1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    replace = "--replace" in sys.argv
    if len(args) != 1:
        fail("informe o arquivo JSON da edição")

    new = json.load(open(args[0], encoding="utf-8"))
    if not isinstance(new, list) or not new:
        fail("o JSON deve ser uma lista não vazia")

    dates = {n.get("date") for n in new}
    if len(dates) != 1:
        fail(f"todas as notícias devem ter a mesma data (achei {sorted(map(str, dates))})")
    day = dates.pop()
    try:
        date.fromisoformat(day)
    except Exception:
        fail(f"data inválida: {day}")

    for i, n in enumerate(new, 1):
        miss = [k for k in REQ if not str(n.get(k, "")).strip()]
        if miss:
            fail(f"notícia {i} sem {miss}")
        if n["region"] not in ("br", "mundo"):
            fail(f"notícia {i}: região deve ser 'br' ou 'mundo'")
        if not n["url"].startswith(("http://", "https://")):
            fail(f"notícia {i}: URL inválida")
        if not str(n.get("lojista", "")).strip():
            n.pop("lojista", None)
            print(f"aviso: notícia {i} sem leitura para o lojista")
        if n.get("lead") is not True:
            n.pop("lead", None)
    for reg in ("br", "mundo"):
        regs = [n for n in new if n["region"] == reg]
        if regs and sum(1 for n in regs if n.get("lead")) != 1:
            fail(f"região '{reg}' precisa de exatamente 1 notícia com \"lead\": true")
    urls = [n["url"] for n in new]
    if len(urls) != len(set(urls)):
        fail("há URLs repetidas na nova edição")

    html = open(INDEX, encoding="utf-8").read()
    m = BLOCK.search(html)
    if not m:
        fail("bloco news-data não encontrado no index.html")
    old = json.loads(m.group(2))

    if any(n["date"] == day for n in old):
        if not replace:
            fail(f"a edição {day} já existe (use --replace para substituir)")
        old = [n for n in old if n["date"] != day]
    dup = set(urls) & {n["url"] for n in old}
    if dup:
        fail(f"notícias já publicadas em edições anteriores: {sorted(dup)}")

    clean = [{k: n[k] for k in ORDER if k in n} for n in new]
    allnews = sorted(clean + old, key=lambda n: n["date"], reverse=True)  # sort estável
    body = "\n[\n" + ",\n".join(" " + json.dumps(n, ensure_ascii=False) for n in allnews) + "\n]\n"
    html = html[: m.start(2)] + body + html[m.end(2):]
    open(INDEX, "w", encoding="utf-8").write(html)
    br = sum(1 for n in clean if n["region"] == "br")
    print(f"OK: edição {day} com {len(clean)} notícias ({br} Brasil, {len(clean) - br} Mundo). Total no site: {len(allnews)}")


if __name__ == "__main__":
    main()
