-- ConsumoZero - criação do banco (rodar como root uma única vez)
CREATE DATABASE IF NOT EXISTS consumozero CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE consumozero;

-- Coleta mínima (LGPD): só um APELIDO da casa/comércio. Nada de nome, CPF, endereço ou telefone.
CREATE TABLE IF NOT EXISTS registros (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    apelido        VARCHAR(40)  NOT NULL,
    categoria      ENUM('agua', 'energia', 'alimento') NOT NULL,
    unidade        ENUM('m3', 'kWh', 'kg') NOT NULL,
    quantidade     DECIMAL(10,2) NOT NULL,
    mes_referencia CHAR(7)      NOT NULL,           -- AAAA-MM
    pessoas        TINYINT UNSIGNED NOT NULL,
    criado_em      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_quantidade CHECK (quantidade > 0 AND quantidade <= 100000),
    CONSTRAINT chk_pessoas    CHECK (pessoas BETWEEN 1 AND 50),
    INDEX idx_categoria (categoria),
    INDEX idx_mes (mes_referencia)
);

-- Usuário com privilégio mínimo: só CRUD nesta tabela (a API nunca usa root)
-- TROQUE a senha abaixo e use a mesma no seu .env
CREATE USER IF NOT EXISTS 'consumozero_app'@'localhost' IDENTIFIED BY 'TroqueEstaSenha!2026';
GRANT SELECT, INSERT, UPDATE, DELETE ON consumozero.registros TO 'consumozero_app'@'localhost';
FLUSH PRIVILEGES;

-- Dados fictícios para demonstração
INSERT INTO registros (apelido, categoria, unidade, quantidade, mes_referencia, pessoas) VALUES
('Casa Azul',          'agua',     'm3',  18.50, '2026-09', 4),
('Casa Azul',          'energia',  'kWh', 210.00, '2026-09', 4),
('Casa Azul',          'alimento', 'kg',  22.00, '2026-09', 4),
('Mercadinho Vila',    'energia',  'kWh', 140.00, '2026-09', 2),
('Mercadinho Vila',    'alimento', 'kg',  12.00, '2026-09', 2),
('Horta Comunitaria',  'agua',     'm3',   9.00, '2026-10', 3);
