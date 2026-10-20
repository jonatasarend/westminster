import hashlib
from pathlib import Path

import duckdb

def import_SBLGNT():

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

    # 3. Registrar a versão MorphGNT SBLGNT na tabela de versões
    con.execute("""
        INSERT OR IGNORE INTO translations (id, name, language, license, is_original)
        VALUES ('SBLGNT', 'SBL Greek New Testament', 'grc', 'CC BY-SA 3.0', TRUE);
        """)

    # 4. Ler os arquivos TXT da MorphGNT SBLGNT em ordem
    txt_paths = sorted(Path("dados/sblgnt-master").rglob("*.txt"))
    if not txt_paths:
        raise FileNotFoundError("Nenhum arquivo .txt encontrado no diretório dados/")
    verses_records = []
    texts_records = []

    # 5. Importação do NT em grego (arquivo morfológico)

    from collections import defaultdict

    verses = defaultdict(list)
    seen_files = set()

    for txt_path in txt_paths:
        file_hash = hashlib.sha256(txt_path.read_bytes()).digest()
        if file_hash in seen_files:
            print(f"Ignorando cópia duplicada: {txt_path}")
            continue
        seen_files.add(file_hash)

        print(f"Lendo o arquivo {txt_path}...")
        with txt_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                parts = line.split()

                # "Se a linha não tiver pelo menos 4 colunas, ignore-a e vá para a próxima."
                if len(parts) < 4:
                    continue

                # Ex.: 040101 = João 1:1
                verse_code = parts[0]

                # Palavra grega da linha
                greek_word = parts[3]

                verses[verse_code].append(greek_word)

    for verse_code, words in verses.items():

        # Livro do arquivo (01-27) -> Livro do banco (40-66)
        book_id = int(verse_code[:2]) + 39

        chap_num = int(verse_code[2:4])
        verse_num = int(verse_code[4:6])

        # Formato do seu banco: 43001001
        verse_id = (book_id * 1000000) + (chap_num * 1000) + verse_num

        verse_text = " ".join(words)
        verses_records.append((verse_id, book_id, chap_num, verse_num))

        print(
            f'Incluindo versículo: Livro {book_id}, Capítulo {chap_num}, Versículo {verse_num} -> ID {verse_id}, Texto: {verse_text}')

        # tabela verses_texts
        texts_records.append(
            ("SBLGNT", verse_id, verse_text)
        )

    # 6. Inserir os registros em lote (Batch Insert)
    print(f"Inserindo {len(texts_records)} versículos no DuckDB...")

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
    count = con.execute("SELECT COUNT(*) FROM verses_texts WHERE translation_id = 'SBLGNT'").fetchone()[0]
    print(f"Sucesso! Total de versículos salvos para a SBLGNT: {count}")

    # Encerra a conexão salvando as alterações
    con.close()
    
if __name__ == "__main__":
    import_SBLGNT()