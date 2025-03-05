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
    usr_type ENUM('Administrador', 'Usuário padrão') NOT NULL DEFAULT 'Usuário padrão'
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

select * from tb_users;
select * from tb_campaigns;
select * from tb_items;
select * from tb_donations;
select * from tb_donation_items;