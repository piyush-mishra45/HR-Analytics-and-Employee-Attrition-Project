-- =====================================================================
-- HR Analytics & Employee Attrition  |  MySQL 8.0
-- Script 1 of 4 : create the database
-- Run order     : create_database.sql -> create_tables.sql -> insert_data.sql -> analysis_queries.sql
-- =====================================================================
DROP DATABASE IF EXISTS hr_analytics_db;

CREATE DATABASE hr_analytics_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE hr_analytics_db;
