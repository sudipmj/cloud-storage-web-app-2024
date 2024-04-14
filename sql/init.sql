CREATE DATABASE cloud_sa2024;

USE cloud_sa2024;

CREATE TABLE t_sec_user (
    user_email VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY,
    sid VARCHAR(255) UNIQUE NOT NULL,
    user_fname VARCHAR(255) NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    user_created_on TIMESTAMP NOT NULL
);

CREATE TABLE t_drive_dtl (
    sid VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY,
    dir_id VARCHAR(255) UNIQUE NOT NULL,
    dir_path VARCHAR(255) NOT NULL,
    dir_size VARCHAR(255) NOT NULL,
    dir_created_on TIMESTAMP NOT NULL,
    FOREIGN KEY (sid)
        REFERENCES t_sec_user (sid)
);

CREATE TABLE t_drive_cont (
    dir_id VARCHAR(255) NOT NULL,
    f_id VARCHAR(255) NOT NULL UNIQUE PRIMARY KEY,
    f_name VARCHAR(255) NOT NULL,
    f_type VARCHAR(255) NOT NULL,
    f_size VARCHAR(255) NOT NULL,
    f_uploaded_on TIMESTAMP NOT NULL,
    FOREIGN KEY (dir_id)
        REFERENCES t_drive_dtl (dir_id)
);