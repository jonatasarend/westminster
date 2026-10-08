-- ======================================================================================
-- ESQUEMA DE BANCO DE DADOS - BÍBLIA INTERLINEAR ( SQL + DUCKDB )
-- ======================================================================================

-- 1. TABELA DE LIVROS DA BÍBLIA
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,                         -- 1 a 66
    code VARCHAR(10) NOT NULL UNIQUE,               -- 'GEN', 'EXO', 'LEV', 'NUM'
    name VARCHAR(100) NOT NULL,                     -- 'Gênesis', 'Êxodo', 'Levítico', 'Números'
    testament VARCHAR(2) NOT NULL,                  -- 'OT', 'NT'
    book_order INTEGER NOT NULL                     -- 1 a 66
);

-- 2. TABELA CANÔNICA DE VERSÍCULOSS
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY,                         -- ID determinístico (ex: 1001001 para Gênesis 1:1)
    book_id INTEGER NOT NULL REFERENCES books(id),
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
);

-- 3. TABELA DE TRADUÇÕES
CREATE TABLE IF NOT EXISTS translations (
    id VARCHAR(20) PRIMARY KEY,                       -- 'NVI', 'ARA', 'ACF'
    name VARCHAR(100) NOT NULL,                       -- 'Nova Versão Internacional', 'Almeida Revista e Atualizada', 'Almeida Corrigida Fiel'
    language VARCHAR(10) NOT NULL,                     -- 'pt', 'en', 'es'
    license VARCHAR(100) NOT NULL,                    -- 'CC BY-SA 4.0', 'Public Domain'
    is_original BOOLEAN NOT NULL DEFAULT FALSE        -- Indica se é a tradução ou original
);

-- 4. TEXTO CORRIDO DAS TRADUÇÕES
CREATE TABLE IF NOT EXISTS verses_texts (
    translation_id VARCHAR(20) NOT NULL REFERENCES translations(id),
    verse_id INTEGER NOT NULL REFERENCES verses(id),
    text TEXT NOT NULL,                                -- Texto corrido do versículo na tradução especificada
    PRIMARY KEY (translation_id, verse_id)
);

-- 5. CADASTRO DE MANUSCRITOS / TEXTOS ORIGINAIS
CREATE TABLE IF NOT EXISTS source_texts (
    id VARCHAR(20) PRIMARY KEY,                       -- 'MT', 'LXX', 'VUL'
    name VARCHAR(100) NOT NULL,                       -- 'Texto Massorético', 'Septuaginta', 'Vulgata'
    language VARCHAR(10) NOT NULL,                    -- 'he', 'gr', 'la'
);

-- 6. TOKENS DO TEXTO ORIGINAL (PALAVRA POR PALAVRA / INTERLINEAR)
CREATE TABLE IF NOT EXISTS original_tokens (
    id BIGINT PRIMARY KEY,                                      -- ID único para cada token,
    verse_id INTEGER NOT NULL REFERENCES verses(id),            -- Referência ao versículo
    source_id VARCHAR(20) NOT NULL REFERENCES source_texts(id), -- Referência ao texto original
    token_order INTEGER NOT NULL,                               -- Ordem do token no versículo
    surface_text VARCHAR(100) NOT NULL,                         -- Texto do token (palavra)
    vocalizes_text VARCHAR(100),                                -- Texto com vogais
    lemma VARCHAR(100),                                         -- Forma canônica do token
    morphology VARCHAR(100),                                    -- Informação morfológica
    strong_id VARCHAR(10),                                       -- Referência ao Strong's Concordance
    literal_pt VARCHAR(100)                                     -- Tradução literal do token para o português
);

-- 7. DICIONÁRIO / LÉXICO STRONG EM PORTUGUÊS
CREATE TABLE IF NOT EXISTS strong_dictionary (
    strong_id VARCHAR(10) PRIMARY KEY,                         -- Referência ao Strong's Concordance
    language VARCHAR(10) NOT NULL,                                -- 'he', 'gr'
    transliteration VARCHAR(100),                                 -- Transliteração do termo
    pronunciation VARCHAR(100),                                   -- Pronúncia do termo
    short_def VARCHAR(255),                                           -- Definição curta
    detailed_def TEXT                                               -- Definição detalhada
);

-- ======================================================================================
-- ÍNDICES PARA OTIMIZAÇÃO DE CONSULTAS
-- ======================================================================================

CREATE INDEX IF NOT EXISTS idx_verses_book_chap ON verses(book_id, chapter);
CREATE INDEX IF NOT EXISTS idx_verses_texts_lookup ON verses_texts(verse_id, translation_id);
CREATE INDEX IF NOT EXISTS idx_tokens_verse_source ON original_tokens(verse_id, source_id, token_order);
CREATE INDEX IF NOT EXISTS idx_tokens_strong ON original_tokens(strong_id);