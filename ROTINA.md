# Rotina diária do Radar Autonove

Guia seguido pela atualização automática (e por quem for publicar à mão).

## O que publicar
- Uma edição por dia, com a data de hoje (fuso de São Paulo).
- 12 a 14 notícias: 6–7 do Brasil (`"region": "br"`) e 6–7 do mundo (`"region": "mundo"`).
- Só notícias das últimas ~24–36 h, de fontes confiáveis, com link direto para a matéria.
- Exatamente 1 destaque por região (`"lead": true`): a notícia mais relevante para quem vende seminovos.
- Nada repetido de edições anteriores (o `add_news.py` bloqueia URL repetida; evite também o mesmo fato com outro link).

## Pauta (prioridade)
1. Brasil: preços e descontos de zero-km, lançamentos, vendas/emplacamentos (Fenabrave), seminovos e usados, crédito/financiamento, IPVA e legislação, recalls, novas marcas (chinesas).
2. Mundo: China (BYD, GWM, Geely etc.), elétricos e baterias, EUA, Europa, resultados de montadoras, tecnologia.

Fontes usadas com frequência: Notícias Automotivas, AutoPapo, Auto+ TV, AutoData, Fenabrave, CnEVPost, Electrek, Gasgoo, Reuters, Bloomberg.

## Como escrever cada notícia
- `title`: manchete própria, clara, com o número principal quando houver (até ~110 caracteres).
- `text`: 2–3 frases com as próprias palavras (nunca copiar trechos da fonte), com os fatos e números essenciais.
- `lojista`: 1 frase prática — o que isso muda para a loja de seminovos (preço de referência, avaliação na troca, giro, estoque, financiamento).
- `cat`: uma de Lançamentos, Preços, Seminovos, Mercado, Crédito, IPVA, Legislação, Recall, Segurança, Novas marcas, Montadoras, Resultados, Indústria, China, EUA, Europa, América do Sul, Elétricos, Baterias, Tecnologia.
- `src`: nome do veículo; `url`: link da matéria.

## Publicar
```bash
python3 add_news.py edicao_AAAA-MM-DD.json   # valida e insere no index.html
git add index.html && git commit -m "Edição AAAA-MM-DD" && git push
```
O GitHub Actions gera `edicao/AAAA-MM-DD/`, o arquivo de edições e o `sitemap.xml` sozinho. Não edite essas pastas à mão e não faça commit do JSON temporário.
