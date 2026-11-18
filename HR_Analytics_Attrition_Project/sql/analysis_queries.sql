-- =====================================================================
-- Script 4 of 4 : 30 analysis queries  |  MySQL 8.0
-- Each query starts with a "-- Q<n>:" header so the validator can split them.
-- Attrition rate convention: ROUND(100 * leavers / headcount, 2)
-- =====================================================================
USE hr_analytics_db;

-- ---------------------------------------------------------------------
-- SECTION A : HEADLINE KPIs
-- ---------------------------------------------------------------------

-- Q1: Total employee count
SELECT COUNT(*) AS total_employees
FROM employees;

-- Q2: Active employee count
SELECT COUNT(*) AS active_employees
FROM attrition_analysis
WHERE attrition = 'No';

-- Q3: Employees who left the company
SELECT COUNT(*) AS employees_left
FROM attrition_analysis
WHERE attrition = 'Yes';

-- Q4: Overall attrition percentage
SELECT COUNT(*)                                         AS total_employees,
       SUM(attrition_flag)                              AS leavers,
       ROUND(100.0 * SUM(attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM attrition_analysis;

-- Q5: One-row KPI card using CASE WHEN
SELECT COUNT(*)                                              AS total_employees,
       SUM(CASE WHEN a.attrition = 'No'  THEN 1 ELSE 0 END)  AS active_employees,
       SUM(CASE WHEN a.attrition = 'Yes' THEN 1 ELSE 0 END)  AS attrition_count,
       ROUND(AVG(e.age), 1)                                  AS avg_age,
       ROUND(AVG(e.monthly_income), 0)                       AS avg_monthly_income
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number;

-- ---------------------------------------------------------------------
-- SECTION B : ATTRITION BY DIMENSION (JOIN / GROUP BY / ORDER BY)
-- ---------------------------------------------------------------------

-- Q6: Department-wise attrition
SELECT d.department_name,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN departments d        ON d.department_id = e.department_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY d.department_name
ORDER BY attrition_rate_pct DESC;

-- Q7: Job-role-wise attrition
SELECT j.job_role_name,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN job_roles j          ON j.job_role_id = e.job_role_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY j.job_role_name
ORDER BY attrition_rate_pct DESC;

-- Q8: Gender-wise attrition
SELECT e.gender,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY e.gender
ORDER BY attrition_rate_pct DESC;

-- Q9: Average monthly salary - overall and by attrition status
SELECT 'All employees' AS segment, ROUND(AVG(monthly_income), 0) AS avg_monthly_income
FROM employees
UNION ALL
SELECT CASE a.attrition WHEN 'Yes' THEN 'Left' ELSE 'Active' END,
       ROUND(AVG(e.monthly_income), 0)
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY a.attrition;

-- Q10: Highest-paying departments
SELECT d.department_name,
       ROUND(AVG(e.monthly_income), 0) AS avg_monthly_income,
       MAX(e.monthly_income)           AS max_monthly_income,
       COUNT(*)                        AS employees
FROM employees e
JOIN departments d ON d.department_id = e.department_id
GROUP BY d.department_name
ORDER BY avg_monthly_income DESC;

-- Q11: Age-wise employee distribution
SELECT a.age_group,
       COUNT(*)                                             AS employees,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM employees), 2) AS pct_of_workforce,
       SUM(a.attrition_flag)                                AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2)   AS attrition_rate_pct
FROM attrition_analysis a
GROUP BY a.age_group
ORDER BY a.age_group;

-- Q12: Overtime analysis
SELECT e.overtime,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct,
       ROUND(AVG(e.monthly_income), 0)                   AS avg_monthly_income
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY e.overtime
ORDER BY attrition_rate_pct DESC;

-- Q13: Job satisfaction analysis (with readable labels)
SELECT s.job_satisfaction,
       CASE s.job_satisfaction WHEN 1 THEN 'Low' WHEN 2 THEN 'Medium'
                               WHEN 3 THEN 'High' ELSE 'Very High' END AS satisfaction_label,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employee_satisfaction s
JOIN attrition_analysis a ON a.employee_number = s.employee_number
GROUP BY s.job_satisfaction
ORDER BY s.job_satisfaction;

-- Q14: Employees with more than 5 years of total experience, by department
SELECT d.department_name,
       COUNT(*)                          AS employees_over_5_yrs_experience,
       ROUND(AVG(e.monthly_income), 0)   AS avg_monthly_income
FROM employees e
JOIN departments d ON d.department_id = e.department_id
WHERE e.total_working_years > 5
GROUP BY d.department_name
ORDER BY employees_over_5_yrs_experience DESC;

-- Q15: Employees with no recent promotion (5+ years since last promotion)
SELECT d.department_name,
       COUNT(*)                                          AS employees_no_promotion_5plus_yrs,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN departments d        ON d.department_id = e.department_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
WHERE e.years_since_last_promotion >= 5
GROUP BY d.department_name
ORDER BY employees_no_promotion_5plus_yrs DESC;

-- Q16: Average working years - overall, by department and attrition status
SELECT d.department_name,
       ROUND(AVG(e.total_working_years), 2)                                    AS avg_total_working_years,
       ROUND(AVG(e.years_at_company), 2)                                       AS avg_years_at_company,
       ROUND(AVG(CASE WHEN a.attrition = 'Yes' THEN e.years_at_company END), 2) AS avg_tenure_of_leavers,
       ROUND(AVG(CASE WHEN a.attrition = 'No'  THEN e.years_at_company END), 2) AS avg_tenure_of_stayers
FROM employees e
JOIN departments d        ON d.department_id = e.department_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY d.department_name;

-- Q17: Attrition by salary category (CASE WHEN computed directly on income)
SELECT CASE WHEN e.monthly_income < 3000  THEN '1. Low (<3K)'
            WHEN e.monthly_income < 6000  THEN '2. Medium (3K-6K)'
            WHEN e.monthly_income < 10000 THEN '3. High (6K-10K)'
            ELSE                               '4. Very High (10K+)' END AS salary_category,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY salary_category
ORDER BY salary_category;

-- Q18: Attrition by work-life balance
SELECT s.work_life_balance,
       CASE s.work_life_balance WHEN 1 THEN 'Bad' WHEN 2 THEN 'Good'
                                WHEN 3 THEN 'Better' ELSE 'Best' END AS wlb_label,
       COUNT(*)                                          AS employees,
       SUM(a.attrition_flag)                             AS leavers,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employee_satisfaction s
JOIN attrition_analysis a ON a.employee_number = s.employee_number
GROUP BY s.work_life_balance
ORDER BY s.work_life_balance;

-- ---------------------------------------------------------------------
-- SECTION C : HAVING, SUBQUERIES
-- ---------------------------------------------------------------------

-- Q19: HAVING + scalar subquery - job roles above company-average attrition (min 30 staff)
SELECT j.job_role_name,
       COUNT(*)                                          AS employees,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN job_roles j          ON j.job_role_id = e.job_role_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY j.job_role_name
HAVING COUNT(*) >= 30
   AND 100.0 * SUM(a.attrition_flag) / COUNT(*) >
       (SELECT 100.0 * SUM(attrition_flag) / COUNT(*) FROM attrition_analysis)
ORDER BY attrition_rate_pct DESC;

-- Q20: HAVING - department x overtime segments with at least 20 employees
SELECT d.department_name,
       e.overtime,
       COUNT(*)                                          AS employees,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
FROM employees e
JOIN departments d        ON d.department_id = e.department_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY d.department_name, e.overtime
HAVING COUNT(*) >= 20
ORDER BY attrition_rate_pct DESC;

-- Q21: Subquery in WHERE - leavers who earned below the average income of their own job role
SELECT j.job_role_name,
       COUNT(*) AS leavers_below_role_avg_income
FROM employees e
JOIN job_roles j          ON j.job_role_id = e.job_role_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
WHERE a.attrition = 'Yes'
  AND e.monthly_income < (SELECT AVG(e2.monthly_income)
                          FROM employees e2
                          WHERE e2.job_role_id = e.job_role_id)
GROUP BY j.job_role_name
ORDER BY leavers_below_role_avg_income DESC;

-- Q22: Business travel x overtime attrition matrix
SELECT e.business_travel,
       ROUND(100.0 * SUM(CASE WHEN e.overtime = 'Yes' THEN a.attrition_flag END)
                   / SUM(CASE WHEN e.overtime = 'Yes' THEN 1 END), 2) AS attrition_pct_with_overtime,
       ROUND(100.0 * SUM(CASE WHEN e.overtime = 'No'  THEN a.attrition_flag END)
                   / SUM(CASE WHEN e.overtime = 'No'  THEN 1 END), 2) AS attrition_pct_without_overtime
FROM employees e
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY e.business_travel
ORDER BY e.business_travel;

-- ---------------------------------------------------------------------
-- SECTION D : CTEs
-- ---------------------------------------------------------------------

-- Q23: CTE - department attrition compared with the company average
WITH dept_stats AS (
    SELECT d.department_name,
           COUNT(*)                                          AS employees,
           ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
    FROM employees e
    JOIN departments d        ON d.department_id = e.department_id
    JOIN attrition_analysis a ON a.employee_number = e.employee_number
    GROUP BY d.department_name
),
company AS (
    SELECT ROUND(100.0 * SUM(attrition_flag) / COUNT(*), 2) AS company_rate_pct
    FROM attrition_analysis
)
SELECT ds.department_name,
       ds.employees,
       ds.attrition_rate_pct,
       c.company_rate_pct,
       ROUND(ds.attrition_rate_pct - c.company_rate_pct, 2) AS gap_vs_company_pts,
       CASE WHEN ds.attrition_rate_pct > c.company_rate_pct THEN 'Above average'
            ELSE 'At / below average' END                    AS status
FROM dept_stats ds
CROSS JOIN company c
ORDER BY gap_vs_company_pts DESC;

-- Q24: Multi-step CTE - transparent rule-based "risk factor count" and observed attrition per count
--      (descriptive segmentation only; it is NOT a predictive model)
WITH risk_flags AS (
    SELECT e.employee_number,
           a.attrition_flag,
           (CASE WHEN e.overtime = 'Yes'                  THEN 1 ELSE 0 END) +
           (CASE WHEN s.job_satisfaction <= 2             THEN 1 ELSE 0 END) +
           (CASE WHEN e.monthly_income < 3000             THEN 1 ELSE 0 END) +
           (CASE WHEN e.years_at_company <= 2             THEN 1 ELSE 0 END) AS risk_factors
    FROM employees e
    JOIN employee_satisfaction s ON s.employee_number = e.employee_number
    JOIN attrition_analysis a    ON a.employee_number = e.employee_number
)
SELECT risk_factors,
       COUNT(*)                                          AS employees,
       SUM(attrition_flag)                               AS leavers,
       ROUND(100.0 * SUM(attrition_flag) / COUNT(*), 2)  AS attrition_rate_pct
FROM risk_flags
GROUP BY risk_factors
ORDER BY risk_factors;

-- Q25: CTE - top 3 job roles by leavers and their share of all leavers
WITH role_leavers AS (
    SELECT j.job_role_name, SUM(a.attrition_flag) AS leavers
    FROM employees e
    JOIN job_roles j          ON j.job_role_id = e.job_role_id
    JOIN attrition_analysis a ON a.employee_number = e.employee_number
    GROUP BY j.job_role_name
)
SELECT job_role_name,
       leavers,
       ROUND(100.0 * leavers / (SELECT SUM(leavers) FROM role_leavers), 2) AS pct_of_all_leavers
FROM role_leavers
ORDER BY leavers DESC
LIMIT 3;

-- ---------------------------------------------------------------------
-- SECTION E : WINDOW FUNCTIONS
-- ---------------------------------------------------------------------

-- Q26: RANK() - job roles ranked by attrition rate
SELECT j.job_role_name,
       COUNT(*)                                          AS employees,
       ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct,
       RANK() OVER (ORDER BY SUM(a.attrition_flag) * 1.0 / COUNT(*) DESC) AS attrition_rank
FROM employees e
JOIN job_roles j          ON j.job_role_id = e.job_role_id
JOIN attrition_analysis a ON a.employee_number = e.employee_number
GROUP BY j.job_role_name
ORDER BY attrition_rank;

-- Q27: ROW_NUMBER() PARTITION BY - 3 highest-paid employees in each department
SELECT department_name, employee_number, job_role_name, monthly_income, income_rank
FROM (
    SELECT d.department_name,
           e.employee_number,
           j.job_role_name,
           e.monthly_income,
           ROW_NUMBER() OVER (PARTITION BY d.department_name
                              ORDER BY e.monthly_income DESC, e.employee_number) AS income_rank
    FROM employees e
    JOIN departments d ON d.department_id = e.department_id
    JOIN job_roles j   ON j.job_role_id   = e.job_role_id
) ranked
WHERE income_rank <= 3
ORDER BY department_name, income_rank;

-- Q28: AVG() OVER (PARTITION BY) - leavers vs the average income of their department
SELECT department_name, employee_number, monthly_income, dept_avg_income,
       ROUND(monthly_income - dept_avg_income, 0) AS diff_from_dept_avg
FROM (
    SELECT d.department_name,
           e.employee_number,
           e.monthly_income,
           a.attrition,
           ROUND(AVG(e.monthly_income) OVER (PARTITION BY d.department_name), 0) AS dept_avg_income
    FROM employees e
    JOIN departments d        ON d.department_id = e.department_id
    JOIN attrition_analysis a ON a.employee_number = e.employee_number
) t
WHERE attrition = 'Yes'
ORDER BY diff_from_dept_avg ASC
LIMIT 10;

-- Q29: NTILE(4) - income quartiles and attrition per quartile
WITH quartiles AS (
    SELECT e.employee_number,
           e.monthly_income,
           a.attrition_flag,
           NTILE(4) OVER (ORDER BY e.monthly_income) AS income_quartile
    FROM employees e
    JOIN attrition_analysis a ON a.employee_number = e.employee_number
)
SELECT income_quartile,
       MIN(monthly_income)                               AS min_income,
       MAX(monthly_income)                               AS max_income,
       COUNT(*)                                          AS employees,
       ROUND(100.0 * SUM(attrition_flag) / COUNT(*), 2)  AS attrition_rate_pct
FROM quartiles
GROUP BY income_quartile
ORDER BY income_quartile;

-- Q30: SUM() OVER + LAG() - cumulative leavers and year-on-year change in attrition rate by tenure year
WITH by_tenure AS (
    SELECT e.years_at_company,
           COUNT(*)                                          AS employees,
           SUM(a.attrition_flag)                             AS leavers,
           ROUND(100.0 * SUM(a.attrition_flag) / COUNT(*), 2) AS attrition_rate_pct
    FROM employees e
    JOIN attrition_analysis a ON a.employee_number = e.employee_number
    WHERE e.years_at_company <= 10
    GROUP BY e.years_at_company
)
SELECT years_at_company,
       employees,
       leavers,
       attrition_rate_pct,
       SUM(leavers) OVER (ORDER BY years_at_company
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_leavers,
       ROUND(attrition_rate_pct - LAG(attrition_rate_pct) OVER (ORDER BY years_at_company), 2)
                                                                             AS change_vs_prev_year_pts
FROM by_tenure
ORDER BY years_at_company;
