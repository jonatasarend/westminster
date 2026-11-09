"""Validações da Fase 0 sobre build/biblia_build.duckdb.

    python build/validar.py [--db build/biblia_build.duckdb] [--divergencias]

Sai com código 1 se alguma verificação falhar. Com --divergencias, lista as referências do
arquivo de referências cruzadas (esquema 'kjv') que não resolvem no esquema canônico 'pt'.
"""
import argparse
import sys
from pathlib import Path

import duckdb

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
XREF = RAIZ / "dados" / "cross_references.txt"

# Totais de capítulos conhecidos da Bíblia protestante (66 livros)
CAPITULOS_AT, CAPITULOS_NT = 929, 260


def checar(con):
    falhas = []

    def ok(nome, condicao, detalhe=""):
        print(f"[{'OK' if condicao else 'FALHA'}] {nome} {detalhe}")
        if not condicao:
            falhas.append(nome)

    q = lambda sql: con.execute(sql).fetchone()[0]

    ok("66 livros (39 AT + 27 NT)",
       q("SELECT count(*) FROM books") == 66 and q("SELECT count(*) FROM books WHERE testament='AT'") == 39)
    ok("capítulos AT/NT",
       (q("SELECT sum(chapters) FROM books WHERE testament='AT'"),
        q("SELECT sum(chapters) FROM books WHERE testament='NT'")) == (CAPITULOS_AT, CAPITULOS_NT))
    n = q("SELECT count(*) FROM verses")
    ok("versículos canônicos", 31100 <= n <= 31105, f"({n})")
    ok("sem versículos órfãos de livro",
       q("SELECT count(*) FROM verses v LEFT JOIN books b USING (book_id) WHERE b.book_id IS NULL") == 0)
    ok("versículos contíguos em cada capítulo (1..N, sem buracos)",
       q("""SELECT count(*) FROM (SELECT book_id, chapter, min(verse) mn, max(verse) mx, count(*) c
            FROM verses GROUP BY 1, 2) WHERE mn <> 1 OR mx <> c""") == 0)
    ok("capítulos contíguos em cada livro",
       q("""SELECT count(*) FROM (SELECT book_id, min(chapter) mn, max(chapter) mx, count(DISTINCT chapter) c
            FROM verses GROUP BY 1) WHERE mn <> 1 OR mx <> c""") == 0)
    ok("todo versículo tem texto em toda tradução registrada",
       q("""SELECT count(*) FROM translations t CROSS JOIN verses v
            LEFT JOIN verse_texts x ON x.translation_id = t.translation_id AND x.verse_id = v.verse_id
            WHERE x.verse_id IS NULL""") == 0)
    ok("sem textos vazios", q("SELECT count(*) FROM verse_texts WHERE length(trim(text)) = 0") == 0)
    ok("verse_map 'pt' é identidade total",
       q("SELECT count(*) FROM verse_map WHERE scheme_id='pt' AND source_ref = verse_id") == n)
    ok("traduções com licença e atribuição",
       q("SELECT count(*) FROM translations WHERE license IS NULL OR attribution IS NULL") == 0)
    return falhas


def divergencias(con):
    """Referências das xrefs (numeração KJV) que não existem em verse_map('kjv')."""
    con.execute(f"""
        CREATE TEMP TABLE stg_xref AS
        SELECT * FROM read_csv('{XREF.as_posix()}', delim='\t', header=false, skip=1,
               columns={{'from_ref':'VARCHAR','to_ref':'VARCHAR','votes':'INTEGER'}})
    """)
    con.execute("""
        CREATE TEMP TABLE refs AS
        SELECT from_ref AS ref FROM stg_xref
        UNION SELECT split_part(to_ref, '-', 1) FROM stg_xref
        UNION SELECT coalesce(nullif(split_part(to_ref, '-', 2), ''), split_part(to_ref, '-', 1)) FROM stg_xref
    """)
    total = con.execute("SELECT count(*) FROM refs").fetchone()[0]
    rows = con.execute("""
        WITH r AS (
          SELECT ref, b.book_id,
                 split_part(ref, '.', 2)::INT AS cap, split_part(ref, '.', 3)::INT AS ver
          FROM refs JOIN books b ON b.osis_code = split_part(ref, '.', 1)
        )
        SELECT ref, b.book_id * 1000000 + cap * 1000 + ver AS source_ref
        FROM r JOIN books b USING (book_id)
        WHERE source_ref NOT IN (SELECT source_ref FROM verse_map WHERE scheme_id = 'kjv')
        ORDER BY source_ref
    """).fetchall()
    sem_livro = con.execute("""
        SELECT DISTINCT split_part(ref, '.', 1) FROM refs
        WHERE split_part(ref, '.', 1) NOT IN (SELECT osis_code FROM books)""").fetchall()
    print(f"\nReferências distintas nas xrefs: {total} | sem livro no banco: {len(sem_livro)} | "
          f"sem correspondência na versificação canônica: {len(rows)}")
    for ref, sr in rows:
        print(f"  {ref}  (source_ref={sr})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(RAIZ / "build" / "biblia_build.duckdb"))
    ap.add_argument("--divergencias", action="store_true")
    args = ap.parse_args()

    con = duckdb.connect(args.db, read_only=True)
    falhas = checar(con)
    if args.divergencias:
        divergencias(con)
    con.close()
    if falhas:
        print(f"\n{len(falhas)} verificação(ões) falharam.")
        sys.exit(1)
    print("\nTodas as verificações passaram.")


if __name__ == "__main__":
    main()
