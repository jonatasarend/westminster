import duckdb

# Conecta ao banco
con = duckdb.connect("bible_interlinear.db")

# Busca versículo em todas as traduções
resultado = con.execute("""
    SELECT
        vt.translation_id,
        t.name,
        vt.text
    FROM verses_texts vt
    JOIN translations t
        ON vt.translation_id = t.id
    WHERE vt.verse_id = 1001001
    ORDER BY vt.translation_id
""").fetchall()

# Exibe os resultados
for trad_id, nome, texto in resultado:

    print(f"[{trad_id}] {nome}")
    print(texto)

    print("\nPalavras:")

    palavras = texto.split()

    for i, palavra in enumerate(palavras, start=1):
        print(f"{i:02d}: {palavra}")

    print("\n" + "=" * 60 + "\n")

# Fecha o banco
con.close()