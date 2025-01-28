CREATE DATABASE db_mais_unidos;

USE db_mais_unidos;

-- Tabela de Usuários
CREATE TABLE tb_users (
    usr_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    usr_name VARCHAR(255) NOT NULL,
    usr_email VARCHAR(255) NOT NULL,
    usr_telephone VARCHAR(20) NOT NULL,
    usr_password TEXT NOT NULL,
    usr_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usr_itemDonations INT DEFAULT 0,
    usr_valueDonations DECIMAL(10,2) DEFAULT 0,
    usr_engagedCampaigns INT DEFAULT 0
);

-- Tabela de Campanhas
CREATE TABLE tb_campaigns (
    cam_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    cam_title VARCHAR(255) NOT NULL,
    cam_description TEXT NOT NULL,
    cam_deadline DATE, -- Prazo da campanha
    cam_meta FLOAT, -- Meta de arrecadação
    cam_reachedMeta FLOAT DEFAULT 0, -- Quantidade arrecadada
    cam_tipo VARCHAR(255) NOT NULL, -- Tipo da campanha
    cam_status VARCHAR(255) DEFAULT "Ativa",	
    cam_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cam_deletedAt TIMESTAMP NULL,
    cam_usr_id INT NOT NULL,
    FOREIGN KEY (cam_usr_id) REFERENCES tb_users(usr_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Tabela de Doações
CREATE TABLE tb_donations (
    dnt_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    dnt_usr_id INT NOT NULL,           -- Usuário que fez a doação
    dnt_cam_id INT NOT NULL,           -- Campanha associada
    dnt_value FLOAT DEFAULT NULL,      -- Valor doado em dinheiro (se aplicável)
    dnt_createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dnt_usr_id) REFERENCES tb_users(usr_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (dnt_cam_id) REFERENCES tb_campaigns(cam_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabela de Itens
CREATE TABLE tb_items (
    itm_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    itm_name VARCHAR(255) NOT NULL, -- Nome do item a ser arrecadado
    itm_quantity INT NOT NULL, -- Quantidade de itens a ser arrecadada
    itm_reachedQuantity INT DEFAULT 0, -- Quantidade de itens arrecadados
    itm_value FLOAT DEFAULT NULL, -- Valor do item (caso o tipo seja itens_e_valor)
    itm_cam_id INT DEFAULT NULL, -- Relaciona o item à campanha
    FOREIGN KEY (itm_cam_id) REFERENCES tb_campaigns(cam_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- Tabela de Itens Relacionados a Doações
CREATE TABLE tb_donation_items (
    dni_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    dni_dnt_id INT NOT NULL,  -- Relaciona com a doação
    dni_item_id INT NOT NULL, -- Relaciona com o item
    dni_quantity INT NOT NULL, -- Quantidade do item doado
    FOREIGN KEY (dni_dnt_id) REFERENCES tb_donations(dnt_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (dni_item_id) REFERENCES tb_items(itm_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

select * from tb_users;
select * from tb_campaigns;
select * from tb_items;

update tb_campaigns set cam_reachedMeta = 10 where cam_id = 3;