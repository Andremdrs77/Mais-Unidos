CREATE DATABASE db_mais_unidos;

USE db_mais_unidos;

CREATE TABLE tb_users (
    usr_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    usr_name VARCHAR(255) NOT NULL,
    usr_email VARCHAR(255) NOT NULL,
    usr_telephone VARCHAR(20) NOT NULL,
    usr_password TEXT NOT NULL,
    usr_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usr_itemDonationsTotal INT DEFAULT 0,
    usr_valueDonationsTotal DECIMAL(10,2) DEFAULT 0,
    usr_type ENUM('Administrador','Usuário') NOT NULL DEFAULT 'Usuário'
);

CREATE TABLE tb_campaigns (
    cam_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    cam_title VARCHAR(255) NOT NULL,
    cam_description TEXT NOT NULL,
    cam_deadline DATE,
    cam_meta FLOAT,
    cam_reachedMeta FLOAT DEFAULT 0,
    cam_tipo VARCHAR(255) NOT NULL,
    cam_status VARCHAR(255) DEFAULT "Ativa",	
    cam_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cam_deletedAt TIMESTAMP NULL,
    cam_usr_id INT NOT NULL,
    FOREIGN KEY (cam_usr_id) REFERENCES tb_users(usr_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);


CREATE TABLE tb_donations (
    dnt_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    dnt_usr_id INT NOT NULL,           
    dnt_cam_id INT NOT NULL,           
    dnt_value FLOAT DEFAULT NULL,      
    dnt_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dnt_usr_id) REFERENCES tb_users(usr_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (dnt_cam_id) REFERENCES tb_campaigns(cam_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE tb_items (
    itm_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    itm_name VARCHAR(255) NOT NULL, 
    itm_quantity INT NOT NULL, 
    itm_reachedQuantity INT DEFAULT 0, 
    itm_value FLOAT DEFAULT NULL, 
    itm_cam_id INT DEFAULT NULL, 
    FOREIGN KEY (itm_cam_id) REFERENCES tb_campaigns(cam_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);


CREATE TABLE tb_donation_items (
    dni_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    dni_dnt_id INT NOT NULL,  
    dni_item_id INT NOT NULL, 
    dni_quantity INT NOT NULL,
    FOREIGN KEY (dni_dnt_id) REFERENCES tb_donations(dnt_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (dni_item_id) REFERENCES tb_items(itm_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

--
-- FUNÇÃO TOTAL DOADO
--

DELIMITER $$
CREATE FUNCTION total_doado(
    p_id_doador INT, 
    p_data_inicio DATETIME, 
    p_data_fim DATETIME
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT IFNULL(SUM(dnt_value), 0) INTO total
    FROM tb_donations
    WHERE dnt_usr_id = p_id_doador 
    AND dnt_createdAt BETWEEN p_data_inicio AND p_data_fim;
    RETURN total;
END$$
DELIMITER ;

--
-- PROCEDIMENTO ARMAZENADO REGISTRAR_DOACAO
--
DELIMITER $$
CREATE PROCEDURE registrar_doacao(
    IN p_id_doador INT,
    IN p_id_campanha INT,
    IN p_valor FLOAT,
    IN p_tipo_doacao VARCHAR(50)
)
BEGIN
    IF p_tipo_doacao = 'financeiro' THEN
         INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value)
         VALUES (p_id_doador, p_id_campanha, p_valor);
    ELSE
         INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value)
         VALUES (p_id_doador, p_id_campanha, NULL);
    END IF;
END$$
DELIMITER ;


--
-- TRIGGER FECHAR_CAMPANHA
--

DELIMITER $$
CREATE TRIGGER fechar_campanha
BEFORE UPDATE ON tb_campaigns
FOR EACH ROW
BEGIN
    IF NEW.cam_reachedMeta >= NEW.cam_meta THEN
         SET NEW.cam_status = 'Encerrada';
    END IF;
END$$
DELIMITER ;



--
-- Tabela de logs de DOAÇÕES (atualizada)
--

CREATE TABLE logs_doacoes (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    operacao VARCHAR(20) NOT NULL,
    dnt_id INT,
    usr_id INT,
    usr_name VARCHAR(255),
    cam_id INT,
    cam_name VARCHAR(255),
    dnt_value FLOAT,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--
-- Tabela de logs de CAMPANHAS
--
CREATE TABLE logs_campanhas (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    operacao VARCHAR(20) NOT NULL,
    cam_id INT,
    usr_id INT,
    cam_title VARCHAR(255),
    cam_description TEXT,
    cam_deadline DATE,
    cam_meta FLOAT,
    cam_reachedMeta FLOAT,
    cam_tipo VARCHAR(255),
    cam_status VARCHAR(255),
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--
-- Tabela de logs de USUÁRIOS
--
CREATE TABLE logs_usuarios (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    operacao VARCHAR(20) NOT NULL,
    usr_id INT,
    usr_name VARCHAR(255),
    usr_email VARCHAR(255),
    usr_telephone VARCHAR(20),
    usr_type ENUM('Administrador', 'Usuário'),
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

--
-- TRIGGER: log_doacoes_insert
--

DELIMITER $$
CREATE TRIGGER log_doacoes_insert
AFTER INSERT ON tb_donations
FOR EACH ROW
BEGIN
    INSERT INTO logs_doacoes (
        operacao, dnt_id, usr_id, usr_name, cam_id, cam_name, dnt_value
    )
    VALUES (
        'INSERT',
        NEW.dnt_id,
        NEW.dnt_usr_id,
        (SELECT usr_name FROM tb_users WHERE usr_id = NEW.dnt_usr_id),
        NEW.dnt_cam_id,
        (SELECT cam_title FROM tb_campaigns WHERE cam_id = NEW.dnt_cam_id),
        NEW.dnt_value
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_doacoes_update
--
DELIMITER $$
CREATE TRIGGER log_doacoes_update
AFTER UPDATE ON tb_donations
FOR EACH ROW
BEGIN
    INSERT INTO logs_doacoes (
        operacao, dnt_id, usr_id, usr_name, cam_id, cam_name, dnt_value
    )
    VALUES (
        'UPDATE',
        NEW.dnt_id,
        NEW.dnt_usr_id,
        (SELECT usr_name FROM tb_users WHERE usr_id = NEW.dnt_usr_id),
        NEW.dnt_cam_id,
        (SELECT cam_title FROM tb_campaigns WHERE cam_id = NEW.dnt_cam_id),
        NEW.dnt_value
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_doacoes_delete
--
DELIMITER $$
CREATE TRIGGER log_doacoes_delete
AFTER DELETE ON tb_donations
FOR EACH ROW
BEGIN
    INSERT INTO logs_doacoes (
        operacao, dnt_id, usr_id, usr_name, cam_id, cam_name, dnt_value
    )
    VALUES (
        'DELETE',
        OLD.dnt_id,
        OLD.dnt_usr_id,
        (SELECT usr_name FROM tb_users WHERE usr_id = OLD.dnt_usr_id),
        OLD.dnt_cam_id,
        (SELECT cam_title FROM tb_campaigns WHERE cam_id = OLD.dnt_cam_id),
        OLD.dnt_value
    );
END$$
DELIMITER ;


--
-- TRIGGER: log_campanhas_insert
--
DELIMITER $$
CREATE TRIGGER log_campanhas_insert
AFTER INSERT ON tb_campaigns
FOR EACH ROW
BEGIN
    INSERT INTO logs_campanhas (
        operacao, cam_id, usr_id, cam_title, cam_description,
        cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status
    )
    VALUES (
        'INSERT',
        NEW.cam_id,
        NEW.cam_usr_id,
        NEW.cam_title,
        NEW.cam_description,
        NEW.cam_deadline,
        NEW.cam_meta,
        NEW.cam_reachedMeta,
        NEW.cam_tipo,
        NEW.cam_status
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_campanhas_update
--
DELIMITER $$
CREATE TRIGGER log_campanhas_update
AFTER UPDATE ON tb_campaigns
FOR EACH ROW
BEGIN
    INSERT INTO logs_campanhas (
        operacao, cam_id, usr_id, cam_title, cam_description,
        cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status
    )
    VALUES (
        'UPDATE',
        NEW.cam_id,
        NEW.cam_usr_id,
        NEW.cam_title,
        NEW.cam_description,
        NEW.cam_deadline,
        NEW.cam_meta,
        NEW.cam_reachedMeta,
        NEW.cam_tipo,
        NEW.cam_status
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_campanhas_delete
--
DELIMITER $$
CREATE TRIGGER log_campanhas_delete
AFTER DELETE ON tb_campaigns
FOR EACH ROW
BEGIN
    INSERT INTO logs_campanhas (
        operacao, cam_id, usr_id, cam_title, cam_description,
        cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status
    )
    VALUES (
        'DELETE',
        OLD.cam_id,
        OLD.cam_usr_id,
        OLD.cam_title,
        OLD.cam_description,
        OLD.cam_deadline,
        OLD.cam_meta,
        OLD.cam_reachedMeta,
        OLD.cam_tipo,
        OLD.cam_status
    );
END$$
DELIMITER ;


--
-- TRIGGER: log_usuarios_insert
--
DELIMITER $$
CREATE TRIGGER log_usuarios_insert
AFTER INSERT ON tb_users
FOR EACH ROW
BEGIN
    INSERT INTO logs_usuarios (
        operacao, usr_id, usr_name, usr_email, usr_telephone, usr_type
    )
    VALUES (
        'INSERT',
        NEW.usr_id,
        NEW.usr_name,
        NEW.usr_email,
        NEW.usr_telephone,
        NEW.usr_type
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_usuarios_update
--
DELIMITER $$
CREATE TRIGGER log_usuarios_update
AFTER UPDATE ON tb_users
FOR EACH ROW
BEGIN
    INSERT INTO logs_usuarios (
        operacao, usr_id, usr_name, usr_email, usr_telephone, usr_type
    )
    VALUES (
        'UPDATE',
        NEW.usr_id,
        NEW.usr_name,
        NEW.usr_email,
        NEW.usr_telephone,
        NEW.usr_type
    );
END$$
DELIMITER ;

--
-- TRIGGER: log_usuarios_delete
--
DELIMITER $$
CREATE TRIGGER log_usuarios_delete
AFTER DELETE ON tb_users
FOR EACH ROW
BEGIN
    INSERT INTO logs_usuarios (
        operacao, usr_id, usr_name, usr_email, usr_telephone, usr_type
    )
    VALUES (
        'DELETE',
        OLD.usr_id,
        OLD.usr_name,
        OLD.usr_email,
        OLD.usr_telephone,
        OLD.usr_type
    );
END$$
DELIMITER ;

INSERT INTO tb_users (
    usr_name, usr_email, usr_telephone, usr_password, usr_itemDonationsTotal, usr_valueDonationsTotal, usr_type
) VALUES (
    'ADMIN',
    'admin@admin',
    '99999999999',
    'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc',
    0,
    0.00,
    'Administrador'
);

-- Inserção de 5 usuários fictícios com o mesmo hash de senha
INSERT INTO tb_users (usr_name, usr_email, usr_telephone, usr_password, usr_itemDonationsTotal, usr_valueDonationsTotal, usr_type)
VALUES
('Alice', 'alice@example.com', '1111111111', 'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc', 0, 0.00, 'Usuário'),
('Bob', 'bob@example.com', '2222222222', 'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc', 0, 0.00, 'Usuário'),
('Charlie', 'charlie@example.com', '3333333333', 'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc', 0, 0.00, 'Usuário'),
('David', 'david@example.com', '4444444444', 'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc', 0, 0.00, 'Usuário'),
('Eve', 'eve@example.com', '5555555555', 'scrypt:32768:8:1$zLT8bioiVhKT2x1i$7f85c334e1d9bb769424eb4b2e59c72d8b5f3b60e29e6ac1bf1a4f77ed3a001b3a1dc4302239930b14cd3dba2cf05dc39b99d7c816ec1b0c3f924936b5bbbdbc', 0, 0.00, 'Usuário');

-- Inserção de campanhas

-- Campanha 1: Financeiro, criada por Alice (usr_id = 1)
INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status, cam_usr_id)
VALUES ('Campanha A', 'Campanha para arrecadação de fundos', '2023-12-31', 1000, 200, 'Financeiro', 'Ativa', 1);

-- Campanha 2: Itens, criada por Bob (usr_id = 2)
INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status, cam_usr_id)
VALUES ('Campanha B', 'Campanha de doação de itens', '2023-11-30', 100, 50, 'Itens', 'Ativa', 2);

-- Campanha 3: Itens e Financeiro, criada por Charlie (usr_id = 3)
INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status, cam_usr_id)
VALUES ('Campanha C', 'Campanha mista para arrecadação de fundos e itens', '2023-10-31', 500, 300, 'Itens e Financeiro', 'Ativa', 3);

-- Campanha 4: Financeiro, encerrada, criada por David (usr_id = 4)
INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status, cam_usr_id)
VALUES ('Campanha D', 'Campanha encerrada', '2023-05-31', 1000, 1000, 'Financeiro', 'Encerrada', 4);

-- Campanha 5: Itens, criada por Eve (usr_id = 5)
INSERT INTO tb_campaigns (cam_title, cam_description, cam_deadline, cam_meta, cam_reachedMeta, cam_tipo, cam_status, cam_usr_id)
VALUES ('Campanha E', 'Campanha para arrecadação de itens', '2023-09-30', 50, 20, 'Itens', 'Ativa', 5);

-- Inserção de itens
-- Para Campanha 2 (Itens)
INSERT INTO tb_items (itm_name, itm_quantity, itm_cam_id, itm_value) VALUES ('Camisetas', 100, 2, NULL);

-- Para Campanha 3 (Itens e Financeiro)
INSERT INTO tb_items (itm_name, itm_quantity, itm_cam_id, itm_value) VALUES 
('Cobertores', 50, 3, 20),
('Agasalhos', 30, 3, 30);

-- Para Campanha 5 (Itens)
INSERT INTO tb_items (itm_name, itm_quantity, itm_cam_id, itm_value) VALUES ('Alimentos', 50, 5, NULL);

-- Inserção de doações com datas diferentes
INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt) VALUES
(1, 1, 100, '2023-01-15 10:00:00'),
(2, 1, 200, '2023-02-20 15:30:00'),
(4, 3, 150, '2023-04-05 09:45:00'),
(5, 3, 100, '2023-04-10 11:20:00'),
(1, 4, 300, '2023-05-01 14:00:00');

-- Inserção de doação de itens (tb_donation_items)
-- Para a doação 3 (Campanha 2) – supondo que o itm_id da 'Camisetas' seja 1
INSERT INTO tb_donation_items (dni_dnt_id, dni_item_id, dni_quantity) VALUES (3, 1, 10);

-- Inserção adicional de doações para testar os filtros de datas
INSERT INTO tb_donations (dnt_usr_id, dnt_cam_id, dnt_value, dnt_createdAt) VALUES
(3, 1, 50, '2023-07-20 10:00:00'),
(5, 4, 250, '2023-09-05 09:00:00'),
(1, 3, 75, '2023-10-12 11:00:00'),
(2, 2, 120, '2023-10-15 16:00:00');


SELECT * FROM tb_users;
SELECT * FROM tb_campaigns;
SELECT * FROM tb_items;
SELECT * FROM tb_donations;
SELECT * FROM tb_donation_items;
SELECT * FROM logs_doacoes;
SELECT * FROM logs_campanhas;
SELECT * FROM logs_usuarios;