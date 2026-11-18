"""
Central configuration: paths, label mappings, bins and colour palette.

Every other module imports from here so that nothing is hard-coded twice.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
REPORTS_DIR = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"
EXCEL_DIR = PROJECT_ROOT / "excel"

RAW_CSV = RAW_DIR / "WA_Fn-UseC_-HR-Employee-Attrition.csv"
CLEAN_CSV = PROCESSED_DIR / "hr_attrition_cleaned.csv"
QUALITY_REPORT_JSON = REPORTS_DIR / "data_quality_report.json"

# ------------------------------------------------- data dictionary pieces
# Columns that hold a single constant value in the IBM dataset (no analytical value)
CONSTANT_COLUMNS = ["EmployeeCount", "Over18", "StandardHours"]

# Expected values for categorical columns (used for validation)
CATEGORICAL_DOMAINS = {
    "Attrition": {"Yes", "No"},
    "OverTime": {"Yes", "No"},
    "Gender": {"Male", "Female"},
    "BusinessTravel": {"Non-Travel", "Travel_Rarely", "Travel_Frequently"},
    "Department": {"Sales", "Research & Development", "Human Resources"},
    "MaritalStatus": {"Single", "Married", "Divorced"},
    "EducationField": {"Life Sciences", "Medical", "Marketing", "Technical Degree",
                       "Human Resources", "Other"},
}

# Ordinal columns and their valid numeric range (inclusive)
ORDINAL_RANGES = {
    "Education": (1, 5),
    "EnvironmentSatisfaction": (1, 4),
    "JobInvolvement": (1, 4),
    "JobLevel": (1, 5),
    "JobSatisfaction": (1, 4),
    "PerformanceRating": (1, 4),
    "RelationshipSatisfaction": (1, 4),
    "StockOptionLevel": (0, 3),
    "WorkLifeBalance": (1, 4),
}

# Human-readable labels for ordinal codes (from the IBM data dictionary)
SATISFACTION_LABELS = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}
WLB_LABELS = {1: "Bad", 2: "Good", 3: "Better", 4: "Best"}
EDUCATION_LABELS = {1: "Below College", 2: "College", 3: "Bachelor",
                    4: "Master", 5: "Doctor"}

# ------------------------------------------------------ derived-feature bins
AGE_BINS = [17, 25, 35, 45, 55, 100]
AGE_LABELS = ["18-25", "26-35", "36-45", "46-55", "56+"]

# Salary slabs on MonthlyIncome (currency units exactly as in the source data)
SALARY_BINS = [0, 2999, 5999, 9999, float("inf")]
SALARY_LABELS = ["Low (<3K)", "Medium (3K-6K)", "High (6K-10K)", "Very High (10K+)"]

TENURE_BINS = [-1, 2, 5, 10, 20, 100]
TENURE_LABELS = ["0-2 yrs", "3-5 yrs", "6-10 yrs", "11-20 yrs", "20+ yrs"]

PROMO_BINS = [-1, 1, 4, 100]
PROMO_LABELS = ["0-1 yrs", "2-4 yrs", "5+ yrs"]

# --------------------------------------------------------------- palette
NAVY = "#0B1F3A"
NAVY_MID = "#1F3C66"
BLUE = "#2E6FBA"
SKY = "#8FB8E8"
RED = "#D64545"
GREY = "#8A94A6"
LIGHT = "#F4F6FA"
PALETTE_STATUS = {"No": BLUE, "Yes": RED}
