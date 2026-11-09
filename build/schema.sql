-- ======================================================================================
-- ESQUEMA v2 — FASE 0 (FUNDAÇÃO) — conforme .md seção 5.2
-- Banco de build: build/biblia_build.duckdb  (fonte da verdade do conteúdo)
-- Tabelas desta fase: núcleo (books, verses, versificação) + traduções PT + sources + release.
-- Tokens, léxico, xrefs, comentários etc. entram nas fases seguintes.
-- ======================================================================================

-- Livros -------------------------------------------------------------------------------
CREATE TABLE books (
    book_id    SMALLINT PRIMARY KEY CHECK (book_id BETWEEN 1 AND 66),
    osis_code  VARCHAR NOT NULL UNIQUE,              -- 'Gen', 'John' (usado por xrefs / OSHB)
    name_pt    VARCHAR NOT NULL,
    abbrev_pt  VARCHAR NOT NULL,                     -- 'Gn', 'Jo'
    testament  VARCHAR NOT NULL CHECK (testament IN ('AT','NT')),
    chapters   SMALLINT                              -- preenchido a partir de verses
);

-- Versificações ------------------------------------------------------------------------
-- 'pt' = canônica do projeto (a das traduções em português). Todas as demais são convertidas
-- para ela via verse_map.
CREATE TABLE versification_schemes (
    scheme_id    VARCHAR PRIMARY KEY,                -- 'pt', 'kjv', 'hebrew'
    description  VARCHAR NOT NULL
);

-- Versículos canônicos (esquema 'pt') ----------------------------------------------------
-- verse_id = book_id*1.000.000 + chapter*1.000 + verse
CREATE TABLE verses (
    verse_id  INTEGER PRIMARY KEY,
    book_id   SMALLINT NOT NULL REFERENCES books(book_id),
    chapter   SMALLINT NOT NULL,
    verse     SMALLINT NOT NULL,                     -- 0 reservado a títulos/superscrições
    CHECK (verse_id = book_id::INTEGER * 1000000 + chapter::INTEGER * 1000 + verse::INTEGER)
);

-- Converte a referência na numeração de uma fonte → verse_id canônico.
-- source_ref é calculado com a mesma fórmula do verse_id, mas na numeração da fonte.
CREATE TABLE verse_map (
    scheme_id  VARCHAR NOT NULL REFERENCES versification_schemes(scheme_id),
    source_ref INTEGER NOT NULL,
    verse_id   INTEGER NOT NULL REFERENCES verses(verse_id),
    PRIMARY KEY (scheme_id, source_ref)
);

-- Traduções em português ---------------------------------------------------------------
CREATE TABLE translations (
    translation_id  VARCHAR PRIMARY KEY,             -- 'BLIVRE', 'TB1917', 'ALM1911'
    name            VARCHAR NOT NULL,
    year            SMALLINT,
    license         VARCHAR NOT NULL,
    attribution     VARCHAR NOT NULL,                -- texto obrigatório a exibir no app
    scheme_id       VARCHAR NOT NULL REFERENCES versification_schemes(scheme_id)
);

CREATE TABLE verse_texts (
    translation_id   VARCHAR NOT NULL REFERENCES translations(translation_id),
    verse_id         INTEGER NOT NULL REFERENCES verses(verse_id),
    text             VARCHAR NOT NULL,
    heading          VARCHAR,                        -- título de seção, se houver
    paragraph_start  BOOLEAN,
    PRIMARY KEY (translation_id, verse_id)
);

-- Fontes de texto original (cadastro; os tokens entram na Fase 2) ------------------------
CREATE TABLE sources (
    source_id    VARCHAR PRIMARY KEY,                -- 'OSHB', 'SBLGNT', 'TR1894'
    language     VARCHAR NOT NULL CHECK (language IN ('hbo','arc','grc')),
    name         VARCHAR NOT NULL,
    license      VARCHAR NOT NULL,
    attribution  VARCHAR NOT NULL,
    scheme_id    VARCHAR NOT NULL REFERENCES versification_schemes(scheme_id)
);

-- Controle de versão do conteúdo ---------------------------------------------------------
CREATE TABLE content_release (
    version   INTEGER PRIMARY KEY,
    built_at  TIMESTAMP NOT NULL,
    notes     VARCHAR
);

-- Índices ------------------------------------------------------------------------------
CREATE INDEX idx_verses_book_chapter ON verses(book_id, chapter);
CREATE INDEX idx_verse_texts_verse   ON verse_texts(verse_id);
