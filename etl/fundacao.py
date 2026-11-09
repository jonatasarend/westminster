"""Fase 0 — Fundação: recria do zero o banco de build (DuckDB) com o núcleo do esquema v2.

    python etl/fundacao.py [--out build/biblia_build.duckdb]

Etapas (idempotentes: o arquivo de saída é sempre recriado):
  1. aplica build/schema.sql
  2. books            <- etl/books.csv
  3. versification    <- 'pt' (canônica), 'kjv' (referências cruzadas), 'hebrew' (OSHB)
  4. verses           <- estrutura capítulo/versículo da Bíblia Livre (versificação 'pt')
  5. translations / verse_texts <- Bíblia Livre (biblialivre.json)
  6. verse_map        <- identidade para 'pt'; 'kjv' = identidade + exceções de etl/verse_map_kjv.csv
  7. sources, content_release
Validações ficam em build/validar.py.
"""
import argparse
import csv
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent


def copiar(con, tabela: str, linhas, colunas: str = ""):
    """Carga em lote (COPY via CSV temporário): executemany é linha a linha e muito lento."""
    fd, caminho = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(linhas)
        con.execute(f"COPY {tabela} {colunas} FROM '{Path(caminho).as_posix()}' (FORMAT csv, HEADER false)")
    finally:
        os.unlink(caminho)


def verse_id(book_id: int, chapter: int, verse: int) -> int:
    return book_id * 1_000_000 + chapter * 1_000 + verse


def carregar_livros(con):
    with open(RAIZ / "etl" / "books.csv", encoding="utf-8", newline="") as f:
        linhas = [(int(r["book_id"]), r["osis_code"], r["name_pt"], r["abbrev_pt"], r["testament"])
                  for r in csv.DictReader(f)]
    copiar(con, "books", linhas, "(book_id, osis_code, name_pt, abbrev_pt, testament)")
    return len(linhas)


def carregar_versificacoes(con):
    con.executemany("INSERT INTO versification_schemes VALUES (?,?)", [
        ("pt", "Canônica do projeto: numeração das traduções em português (Bíblia Livre)"),
        ("kjv", "Padrão inglês (KJV/OpenBible): usada pelas referências cruzadas"),
        ("hebrew", "Numeração do texto hebraico (WLC/OSHB)"),
    ])


def carregar_biblia_livre(con):
    with open(RAIZ / "biblialivre.json", encoding="utf-8") as f:
        dados = json.load(f)

    versiculos, textos = [], []
    for livro in dados:
        book_id = int(livro["id"])
        for cap, versos in enumerate(livro["capitulos"], start=1):
            for num, texto in enumerate(versos, start=1):
                vid = verse_id(book_id, cap, num)
                versiculos.append((vid, book_id, cap, num))
                textos.append(("BLIVRE", vid, texto.strip()))

    copiar(con, "verses", versiculos)
    con.execute("""
        INSERT INTO translations VALUES
        ('BLIVRE', 'Bíblia Livre', NULL, 'CC BY-SA 4.0',
         'Bíblia Livre — licença CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)', 'pt')
    """)
    copiar(con, "verse_texts", textos, "(translation_id, verse_id, text)")
    con.execute("""
        UPDATE books SET chapters = (SELECT max(chapter) FROM verses v WHERE v.book_id = books.book_id)
    """)
    return len(versiculos)


def carregar_verse_map(con):
    # 'pt': identidade (permite consultar qualquer esquema da mesma forma)
    con.execute("INSERT INTO verse_map SELECT 'pt', verse_id, verse_id FROM verses")

    # 'kjv': identidade + exceções curadas em etl/verse_map_kjv.csv
    #   colunas: source_ref (verse_id na numeração KJV), verse_id ('' = sem equivalente em 'pt')
    excecoes = {}
    arq = RAIZ / "etl" / "verse_map_kjv.csv"
    if arq.exists():
        with open(arq, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                excecoes[int(r["source_ref"])] = int(r["verse_id"]) if r["verse_id"] else None

    linhas = {}
    for (vid,) in con.execute("SELECT verse_id FROM verses").fetchall():
        linhas[vid] = vid
    for ref, destino in excecoes.items():
        if destino is None:
            linhas.pop(ref, None)
        else:
            linhas[ref] = destino
    copiar(con, "verse_map", [("kjv", k, v) for k, v in linhas.items()])
    return len(excecoes)


def carregar_fontes(con):
    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?)", [
        ("OSHB", "hbo", "Open Scriptures Hebrew Bible (base WLC)", "CC BY 4.0",
         "Open Scriptures Hebrew Bible — CC BY 4.0 (hb.openscriptures.org)", "hebrew"),
        ("SBLGNT", "grc", "SBL Greek New Testament + MorphGNT", "SBLGNT EULA / CC BY-SA 3.0 (MorphGNT)",
         "SBLGNT © Society of Biblical Literature e Logos Bible Software; morfologia MorphGNT (CC BY-SA 3.0)",
         "pt"),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RAIZ / "build" / "biblia_build.duckdb"))
    args = ap.parse_args()

    saida = Path(args.out)
    saida.parent.mkdir(parents=True, exist_ok=True)
    for sufixo in ("", ".wal"):
        Path(str(saida) + sufixo).unlink(missing_ok=True)

    con = duckdb.connect(str(saida))
    con.execute((RAIZ / "build" / "schema.sql").read_text(encoding="utf-8"))

    print(f"books: {carregar_livros(con)}")
    carregar_versificacoes(con)
    print(f"verses/verse_texts (BLIVRE): {carregar_biblia_livre(con)}")
    print(f"verse_map: exceções kjv aplicadas = {carregar_verse_map(con)}")
    carregar_fontes(con)
    con.execute("INSERT INTO content_release VALUES (0, ?, 'Fase 0: núcleo + Bíblia Livre')",
                [datetime.now()])
    con.execute("CHECKPOINT")
    con.close()
    print(f"OK -> {saida}")


if __name__ == "__main__":
    main()
