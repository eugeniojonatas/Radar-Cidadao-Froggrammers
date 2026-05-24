CREATE DATABASE radarcidadao;

USE radarcidadao;

CREATE TABLE feedbacks (

    id INT AUTO_INCREMENT PRIMARY KEY,

    deputado_id INT NOT NULL,

    nome VARCHAR(100) NOT NULL,

    nota INT NOT NULL,

    comentario TEXT NOT NULL,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);