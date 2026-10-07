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