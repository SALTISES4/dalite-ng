CREATE DATABASE dalite_ng;
CREATE USER 'dalite'@'localhost' IDENTIFIED BY 'dalite_password123';
GRANT ALL PRIVILEGES ON dalite_ng.* TO 'dalite'@'localhost';