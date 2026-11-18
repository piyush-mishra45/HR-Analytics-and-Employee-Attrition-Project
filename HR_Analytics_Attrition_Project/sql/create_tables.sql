-- =====================================================================
-- Script 2 of 4 : normalised schema (3NF-style star around `employees`)
--
--   departments (1) ----< employees >---- (1) job_roles
--                            |1
--                            |-- 1 employee_satisfaction
--                            |-- 1 attrition_analysis
--
-- `job_roles` is deliberately NOT tied to one department: in the source data the
-- role "Manager" appears in all three departments.
-- =====================================================================
USE hr_analytics_db;

CREATE TABLE departments (
    department_id    INT          NOT NULL,
    department_name  VARCHAR(50)  NOT NULL,
    CONSTRAINT pk_departments PRIMARY KEY (department_id),
    CONSTRAINT uq_department_name UNIQUE (department_name)
) ENGINE=InnoDB;

CREATE TABLE job_roles (
    job_role_id    INT          NOT NULL,
    job_role_name  VARCHAR(60)  NOT NULL,
    CONSTRAINT pk_job_roles PRIMARY KEY (job_role_id),
    CONSTRAINT uq_job_role_name UNIQUE (job_role_name)
) ENGINE=InnoDB;

CREATE TABLE employees (
    employee_number            INT           NOT NULL,
    age                        INT           NOT NULL,
    gender                     VARCHAR(10)   NOT NULL,
    marital_status             VARCHAR(10)   NOT NULL,
    education                  INT           NOT NULL,   -- 1 Below College ... 5 Doctor
    education_field            VARCHAR(30)   NOT NULL,
    department_id              INT           NOT NULL,
    job_role_id                INT           NOT NULL,
    job_level                  INT           NOT NULL,   -- 1..5
    business_travel            VARCHAR(20)   NOT NULL,
    distance_from_home         INT           NOT NULL,
    monthly_income             INT           NOT NULL,   -- currency units as in the source data
    percent_salary_hike        INT           NOT NULL,
    performance_rating         INT           NOT NULL,
    stock_option_level         INT           NOT NULL,
    num_companies_worked       INT           NOT NULL,
    total_working_years        INT           NOT NULL,
    training_times_last_year   INT           NOT NULL,
    years_at_company           INT           NOT NULL,
    years_in_current_role      INT           NOT NULL,
    years_since_last_promotion INT           NOT NULL,
    years_with_curr_manager    INT           NOT NULL,
    overtime                   VARCHAR(3)    NOT NULL,
    CONSTRAINT pk_employees PRIMARY KEY (employee_number),
    CONSTRAINT fk_emp_department FOREIGN KEY (department_id) REFERENCES departments (department_id),
    CONSTRAINT fk_emp_job_role   FOREIGN KEY (job_role_id)   REFERENCES job_roles (job_role_id),
    CONSTRAINT chk_emp_age       CHECK (age BETWEEN 16 AND 70),
    CONSTRAINT chk_emp_income    CHECK (monthly_income > 0),
    CONSTRAINT chk_emp_overtime  CHECK (overtime IN ('Yes', 'No'))
) ENGINE=InnoDB;

CREATE INDEX idx_emp_department ON employees (department_id);
CREATE INDEX idx_emp_job_role   ON employees (job_role_id);

CREATE TABLE employee_satisfaction (
    employee_number           INT NOT NULL,
    environment_satisfaction  INT NOT NULL,   -- 1 Low ... 4 Very High
    job_satisfaction          INT NOT NULL,
    relationship_satisfaction INT NOT NULL,
    work_life_balance         INT NOT NULL,   -- 1 Bad ... 4 Best
    job_involvement           INT NOT NULL,
    CONSTRAINT pk_satisfaction PRIMARY KEY (employee_number),
    CONSTRAINT fk_sat_employee FOREIGN KEY (employee_number) REFERENCES employees (employee_number),
    CONSTRAINT chk_sat_range CHECK (environment_satisfaction BETWEEN 1 AND 4
                                AND job_satisfaction BETWEEN 1 AND 4
                                AND relationship_satisfaction BETWEEN 1 AND 4
                                AND work_life_balance BETWEEN 1 AND 4
                                AND job_involvement BETWEEN 1 AND 4)
) ENGINE=InnoDB;

CREATE TABLE attrition_analysis (
    employee_number  INT          NOT NULL,
    attrition        VARCHAR(3)   NOT NULL,   -- 'Yes' = left the company
    attrition_flag   TINYINT      NOT NULL,   -- 1 / 0 helper for SUM() and AVG()
    age_group        VARCHAR(10)  NOT NULL,
    salary_slab      VARCHAR(20)  NOT NULL,
    tenure_band      VARCHAR(10)  NOT NULL,
    promotion_gap    VARCHAR(10)  NOT NULL,
    CONSTRAINT pk_attrition PRIMARY KEY (employee_number),
    CONSTRAINT fk_attr_employee FOREIGN KEY (employee_number) REFERENCES employees (employee_number),
    CONSTRAINT chk_attr_value CHECK (attrition IN ('Yes', 'No')),
    CONSTRAINT chk_attr_flag  CHECK (attrition_flag IN (0, 1))
) ENGINE=InnoDB;
