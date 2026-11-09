from pathlib import Path
import duckdb
import json

BOOK_MAP = {
    "Genesis": 1,
    "Exodus": 2,
    "Leviticus": 3,
    "Numbers": 4,
    "Deuteronomy": 5,
    "Joshua": 6,
    "Judges": 7,
    "Ruth": 8,
    "1 Samuel": 9,
    "2 Samuel": 10,
    "1 Kings": 11,
    "2 Kings": 12,
    "1 Chronicles": 13,
    "2 Chronicles": 14,
    "Ezra": 15,
    "Nehemiah": 16,
    "Esther": 17,
    "Job": 18,
    "Psalms": 19,
    "Proverbs": 20,
    "Ecclesiastes": 21,
    "Song of Solomon": 22,
    "Isaiah": 23,
    "Jeremiah": 24,
    "Lamentations": 25,
    "Ezekiel": 26,
    "Daniel": 27,
    "Hosea": 28,
    "Joel": 29,
    "Amos": 30,
    "Obadiah": 31,
    "Jonah": 32,
    "Micah": 33,
    "Nahum": 34,
    "Habakkuk": 35,
    "Zephaniah": 36,
    "Haggai": 37,
    "Zechariah": 38,
    "Malachi": 39,
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
    "Revelation": 66
}

def import_WLC():

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

    # 3. Registrar a versão Westminster Leningrad Codex na tabela de versões
    con.execute("""
        INSERT OR IGNORE INTO translations (id, name, language, license, is_original)
        VALUES ('WLC', 'Westminster Leningrad Codex', 'heb', 'CC BY', TRUE);
        """)

    # 4. Ler os arquivos json da Westminster Leningrad Codex em ordem
    json_dir = Path("dados/westminster-leningrad-codex")

    json_files = sorted(
        json_dir.glob("*.json")
    )

    # 5. Importação do AT em hebraico (arquivo morfológico)

    verses_records = []
    texts_records = []

    for json_path in json_files:
        print(f"Lendo {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for book_name, book_data in data.items():

            book_id = BOOK_MAP.get(book_name)

            if book_id is None:
                raise ValueError(
                    f"Livro não encontrado no BOOK_MAP: {book_name}"
                )

            chapters = book_data["chapters"]

            for chapter_num, chapter_data in chapters.items():

                for verse_num, words in chapter_data.items():

                    verse_text = " ".join(
                        word["hebrew"]
                        for word in words
                    )

                    try:
                        chapter_int = int(chapter_num)
                        verse_int = int(verse_num)
                    except ValueError:
                        print(
                            f"Ignorando registro inválido: "
                            f"{book_name} {chapter_num}:{verse_num}"
                        )
                        continue

                    verse_id = (
                        book_id * 1000000
                        + chapter_int * 1000
                        + verse_int
                    )

                    verses_records.append(
                        (
                            verse_id,
                            book_id,
                            chapter_int,
                            verse_int
                        )
                    )

                    texts_records.append(
                        (
                            "WLC",
                            verse_id,
                            verse_text
                        )
                    )

    # 6. Inserir os registros em lote (Batch Insert)
    print(f"Arquivos encontrados: {len(json_files)}")
    print(f"Versículos encontrados: {len(verses_records)}")

    print(f"Inserindo {len(texts_records)} versículos no DuckDB...")

    print(f"Versículos encontrados: {len(verses_records)}")
    print(f"Textos encontrados: {len(texts_records)}")

    if verses_records:
        print("Primeiro registro:")
        print(verses_records[0])
        print(texts_records[0])

        print("Último registro:")
        print(verses_records[-1])
        print(texts_records[-1])
    else:
        print("Nenhum versículo encontrado.")

    # Insere o texto em Hebraico
    if not verses_records:
        print("Nenhum registro para importar.")
        con.close()
        return

    con.executemany("""
        INSERT OR IGNORE INTO verses (id, book_id, chapter, verse)
        VALUES (?, ?, ?, ?);
    """, verses_records)

    con.executemany("""
        INSERT OR IGNORE INTO verses_texts (translation_id, verse_id, text)
        VALUES (?, ?, ?);
    """, texts_records)

    # 7. Validar a importação
    count = con.execute("SELECT COUNT(*) FROM verses_texts WHERE translation_id = 'WLC'").fetchone()[0]
    print(f"Sucesso! Total de versículos salvos para a Westminster Leningrad Codex: {count}")

    # Encerra a conexão salvando as alterações
    con.commit()
    con.close()
    
if __name__ == "__main__":
    import_WLC()