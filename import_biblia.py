import json
import duckdb

def import_biblia_livre():

    # 1. Conectar (ou criar) ao banco de dados DuckDB
    db_path = "bible_interlinear.db"
    print(f"Conectando ao banco de dados DuckDB em {db_path}...")
    con = duckdb.connect(db_path)

    # 2. Ler e executar o schema.sql
    print("Executando o arquivo schema.sql...")
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()
        con.execute(schema_sql)

    # 3. Registrar a versão Bíblia Livre na tabela de versões
    con.execute("""
        INSERT OR IGNORE INTO translations (id, name, language, license, is_original)
        VALUES ('BLIVRE', 'Bíblia Livre', 'pt', 'CC BY-SA 4.0', FALSE);
        """)

    # 4. Ler o arquivo JSON com o texto da Bíblia Livre
    json_path = "biblialivre.json"
    print(f"Lendo o arquivo {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        biblia_data = json.load(f)

    verses_records = []
    texts_records = []

    # 5. Percorrer o JSON e montar os registros
    # Este loop assume a estrutura padrão em matriz:
    # [ { "book_id": 1, "chapters": [ ["Versículo 1", "Versículo 2", ...], ... ] }, ... ]
    for book in biblia_data:
        book_id = book["id"]

        for chap_num, chapter_verses in enumerate(book["capitulos"], start=1):
            for verse_num, text_content in enumerate(chapter_verses, start=1):
                # Fórmula determinística do ID do versículo

                book_id = int(book_id)  # Certifique-se de que book_id é um inteiro
                chap_num = int(chap_num)  # Certifique-se de que chap_num é um inteiro
                verse_num = int(verse_num)  # Certifique-se de que verse_num é um inteiro

                verse_id = (book_id * 1000000) + (chap_num * 1000) + verse_num

                # Registro para tabela canônica 'verses'
                verses_records.append((verse_id, book_id, chap_num, verse_num))

                # Registro para tabela de textos 'verse_texts'
                texts_records.append(('BLIVRE', verse_id, text_content))

    # 6. Inserir os registros em lote (Batch Insert)
    print(f"Inserindo {len(verses_records)} versícuos no DuckDB...")

    # Insere na tabela canônica de versículos
    con.executemany("""
        INSERT OR IGNORE INTO verses (id, book_id, chapter, verse)
        VALUES (?, ?, ?, ?);
    """, verses_records)

    # Insere o texto em português
    con.executemany("""
        INSERT OR IGNORE INTO verse_texts (translation_id, verse_id, text)
        VALUES (?, ?, ?);
    """, texts_records)

    # 7. Validar a importação
    count = con.execute("SELECT COUNT(*) FROM verse_texts WHERE translation_id = 'BLIVRE'").fetchone()[0]
    print(f"Sucesso! Total de versículos salvos para a Bíblia Livre: {count}")

    # Encerra a conexão salvando as alterações
    con.close()

if __name__ == "__main__":
    import_biblia_livre()