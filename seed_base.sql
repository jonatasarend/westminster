-- Registrar as versões da Bíblia no banco de dados
INSERT OR IGNORE INTO translations (id, name, language, license, is_original) VALUES
('BLIVRE', 'Bíblia Livre', 'pt-BR', 'CC BY-SA 4.0', FALSE);

INSERT OR IGNORE INTO source_texts (id, name, language) VALUES
('WLC', 'Westminster Leningrad Codex', 'hebrew'),
('OSHB', 'Open Scriptures Hebrew Bible', 'hebrew'),
('SBLGNT', 'SBL Greek New Testament', 'greek'),
('TR', 'Textus Receptus (1894)', 'greek');

-- Inserindo livros da Bíblia
INSERT OR IGNORE INTO books (id, code, name, testament, book_order) VALUES
(1, 'GN', 'Gênesis', 'OT', 1),
(2, 'EX', 'Êxodo', 'OT', 2),
(3, 'LV', 'Levítico', 'OT', 3),
(4, 'NM', 'Números', 'OT', 4),
(5, 'DT', 'Deuteronômio', 'OT', 5),
(6, 'JS', 'Josué', 'OT', 6),
(7, 'JZ', 'Juízes', 'OT', 7),
(8, 'RT', 'Rute', 'OT', 8),
(9, '1SA', '1 Samuel', 'OT', 9),
(10, '2SA', '2 Samuel', 'OT', 10),
(11, '1RS', '1 Reis', 'OT', 11),
(12, '2RS', '2 Reis', 'OT', 12),
(13, '1CR', '1 Crônicas', 'OT', 13),
(14, '2CR', '2 Crônicas', 'OT', 14),
(15, 'ED', 'Esdras', 'OT', 15),
(16, 'NE', 'Neemias', 'OT', 16),
(17, 'ET','Ester','OT',17),
(18, 'JÓ', 'Jó', 'OT', 18),
(19, 'SL', 'Salmos', 'OT', 19),
(20, 'PV', 'Provérbios', 'OT', 20),
(21, 'EC', 'Eclesiastes', 'OT', 21),
(22, 'CT', 'Cânticos dos Cânticos', 'OT', 22),
(23, 'IS', 'Isaías', 'OT', 23),
(24, 'JR', 'Jeremias', 'OT', 24),
(25, 'LM', 'Lamentações de Jeremias', 'OT', 25),
(26, 'EZ', 'Ezequiel', 'OT', 26),
(27, 'DN', 'Daniel', 'OT', 27),
(28, 'OS', 'Oseias', 'OT', 28),
(29, 'JL','Joel','OT',29),
(30, 'AM','Amós','OT',30),
(31, 'OB','Obadias','OT',31),
(32, 'JN','Jonas','OT',32),
(33, 'MQ','Miquéias','OT',33),
(34, 'NA','Naum','OT',34),
(35, 'HC','Habacuque','OT',35),
(36, 'SF','Sofonias','OT',36),
(37, 'AG','Ageu','OT',37),
(38, 'ZC','Zacarias','OT',38),
(39, 'ML','Malaquias','OT',39),
(40, 'MT','Mateus','NT',40),
(41, 'MC','Marcos','NT',41),
(42, 'LC','Lucas','NT',42),
(43, 'JO','João','NT',43),
(44, 'AT','Atos dos Apóstolos','NT',44),
(45, 'RM','Romanos','NT',45),
(46, '1CO','1 Coríntios','NT',46),
(47, '2CO','2 Coríntios','NT',47),
(48, 'GL','Gálatas','NT',48),
(49, 'EF','Efésios','NT',49),
(50, 'FP','Filipenses','NT',50),
(51, 'CL','Colossenses','NT',51),
(52, '1TS','1 Tessalonicenses','NT',52),
(53, '2TS','2 Tessalonicenses','NT',53),
(54, '1TM','1 Timóteo','NT',54),
(55, '2TM','2 Timóteo','NT',55),
(56, 'TT','Tito','NT',56),
(57, 'FM','Filemom','NT',57),
(58, 'HB','Hebreus','NT',58),
(59, 'TG','Tiago','NT',59),
(60, '1PE','1 Pedro','NT',60),
(61, '2PE','2 Pedro','NT',61),
(62, '1JO','1 João','NT',62),
(63, '2JO','2 João','NT',63),
(64, '3JO','3 João','NT',64),
(65, 'JD','Judas','NT',65),
(66, 'AP','Apocalipse','NT',66);

-- Registrar Genesis 1:1 e João 1:1 na tabela canônica de versículos
INSERT OR IGNORE INTO verses (id, book_id, chapter, verse) VALUES
(1001001, 1, 1, 1),  -- Gênesis 1:1
(43001001, 43, 1, 1); -- João 1:1

-- Inserir textos corridos para os versículos registrados
INSERT OR IGNORE INTO verses_texts (translation_id, verse_id, text) VALUES
('BLIVRE', 1001001, 'No princípio, Deus criou os céus e a terra.'),
('BLIVRE', 43001001, 'No princípio era o Verbo, e o Verbo estava com Deus, e o Verbo era Deus.');