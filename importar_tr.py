from pathlib import Path
import duckdb
import json

BOOK_MAP = {
    "Matthew": 40,
    "Mark": 41,
    "Luke": 42,
    "John": 43,
    "Acts": 44,
    "Romans": 45,
    "1 Corinthians": 46,
    "2 Corinthians": 47,
    "Galatians": 48,
    "Ephesians": 49,
    "Philippians": 50,
    "Colossians": 51,
    "1 Thessalonians": 52,
    "2 Thessalonians": 53,
    "1 Timothy": 54,
    "2 Timothy": 55,
    "Titus": 56,
    "Philemon": 57,
    "Hebrews": 58,
    "James": 59,
    "1 Peter": 60,
    "2 Peter": 61,
    "1 John": 62,
    "2 John": 63,
    "3 John": 64,
    "Jude": 65,
    "Revelation": 66,
}

def import_TR1894():

    # 1. Conectar (ou criar) ao banco de dados DuckDB
    db_path = "bible_interlinear.db"
    print(f"Conectando ao banco de dados DuckDB em {db_path}...")
    con = duckdb.connect(db_path)
    
    # 2. Ler e executar o schema.sql
    print("Executando o arquivo schema.sql...")
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
        con.execute(schema_sql)

    print("Executando o arquivo seed_base.sql...")
    with open("seed_base.sql", "r", encoding="utf-8") as f:
        seed_sql = f.read()
        con.execute(seed_sql)

    # 3. Registrar a versão Textus Receptus na tabela de versões
    con.execute("""
        INSERT OR IGNORE INTO translations (id, name, language, license, is_original)
        VALUES ('TR1894', 'Textus Receptus', 'grc', 'CC BY-SA 3.0', TRUE);
        """)

    # 4. Ler os arquivos json da Textus Receptus em ordem
    json_path = Path("dados/textus-receptus-master/data/gnt.flat.json")

    # 5. Importação do NT em grego (arquivo morfológico)

    verses_records = []
    texts_records = []

    print(f"Lendo {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:

        book_name = item["book_name"]
        book_id = BOOK_MAP.get(book_name)
        if book_id is None:
            raise ValueError(
                f"Livro não encontrado no BOOK_MAP: {book_name}"
            )
        chap_num = item["chapter"]
        verse_num = item["verse"]

        verse_id = (
            book_id * 1000000
            + chap_num * 1000
            + verse_num
        )

        verse_text = item["greek_text"]

        verses_records.append(
            (
                verse_id,
                book_id,
                chap_num,
                verse_num
            )
        )

        texts_records.append(
            (
                "TR1894",
                verse_id,
                verse_text
            )
        )

    # 6. Inserir os registros em lote (Batch Insert)
    print(f"Inserindo {len(texts_records)} versículos no DuckDB...")

    print(f"Versículos encontrados: {len(verses_records)}")
    print(f"Textos encontrados: {len(texts_records)}")

    print("Primeiro registro:")
    print(verses_records[0])

    print(texts_records[0])

    # Insere o texto em Grego
    con.executemany("""
        INSERT OR IGNORE INTO verses (id, book_id, chapter, verse)
        VALUES (?, ?, ?, ?);
    """, verses_records)

    con.executemany("""
        INSERT OR IGNORE INTO verses_texts (translation_id, verse_id, text)
        VALUES (?, ?, ?);
    """, texts_records)

    # 7. Validar a importação
    count = con.execute("SELECT COUNT(*) FROM verses_texts WHERE translation_id = 'TR1894'").fetchone()[0]
    print(f"Sucesso! Total de versículos salvos para a Textus Receptus: {count}")

    # Encerra a conexão salvando as alterações
    con.commit()
    con.close()
    
if __name__ == "__main__":
    import_TR1894()