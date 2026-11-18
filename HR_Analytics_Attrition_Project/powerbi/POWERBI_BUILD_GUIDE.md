# Power BI Build Guide

> **Status: the `.pbix` file is NOT included in this project.**
> Power BI Desktop is a Windows application and cannot be run or scripted in the environment where this
> project was generated, so no `HR_Analytics_Dashboard.pbix` exists. Everything needed to build it in
> about 30-45 minutes is provided here: a cleaned dataset, tested DAX measures, a dark-navy theme and the
> exact visual-by-visual layout. After you build it, save it as `powerbi/HR_Analytics_Dashboard.pbix`
> and add screenshots to `docs/screenshots/`.

## 1. Load the data
1. Power BI Desktop -> **Get data -> Text/CSV** -> `data/processed/hr_attrition_cleaned.csv` -> **Transform data**.
2. Rename the query to **`employees`** (the DAX file depends on this name).
3. Confirm types: all `Years*`, `Age`, `MonthlyIncome`, `JobLevel`, satisfaction columns = Whole number; `AttritionFlag` = Whole number; the rest Text. **Close & Apply**.
4. Model view: set **Sort by column** `SalarySlab` -> `SalarySlabOrder`, `TenureBand` -> `TenureBandOrder`.

## 2. Theme and measures
- **View -> Themes -> Browse for themes** -> `powerbi/HR_Analytics_Theme.json`.
- Create the measures from `powerbi/DAX_Measures.dax` (Modeling -> New measure). Format `Attrition Rate` as Percentage (1 decimal).
- Canvas: 16:9, page background `#F4F6FA`; header band `#0B1F3A` with white title text **HR ANALYTICS & EMPLOYEE ATTRITION INSIGHTS**.

## 3. Pages
Slicers on every page (sync across pages via View -> Sync slicers): **Department**, **JobRole**, **Gender**, **AgeGroup**.

### Page 1 - HR Overview
| Visual | Fields |
|---|---|
| 6 Card visuals | `[Total Employees]`, `[Active Employees]`, `[Attrition Count]`, `[Attrition Rate]`, `[Average Age]`, `[Average Salary]` |
| Clustered bar - Attrition by Department | Axis `Department`; Values `[Attrition Count]` (tooltip `[Attrition Rate]`) |
| Clustered column - Attrition by Gender | Axis `Gender`; Values `[Attrition Count]` |
| Clustered column - Attrition by Age Group | Axis `AgeGroup`; Values `[Attrition Rate]` |
| Donut - Active vs Attrition | Legend `Attrition`; Values `[Total Employees]` (colours: No `#2E6FBA`, Yes `#D64545`) |

### Page 2 - Attrition Analysis
| Visual | Fields |
|---|---|
| Bar - by Job Role | Axis `JobRole`; Values `[Attrition Rate]`; sort descending |
| Column - by Job Level | Axis `JobLevel`; Values `[Attrition Rate]` |
| Column - by Overtime | Axis `OverTime`; Values `[Attrition Rate]` |
| Column - by Salary Slab | Axis `SalarySlab`; Values `[Attrition Rate]` |
| Column - by Years at Company | Axis `TenureBand`; Values `[Attrition Rate]` |
| Column - by Business Travel | Axis `BusinessTravel`; Values `[Attrition Rate]` |

Add a constant line on each rate chart: Analytics pane -> Constant line / use `[Company Attrition Rate]` as a second series. Conditional-format bar colour with `[Above Company Rate Flag]` (red when 1).

### Page 3 - Employee Satisfaction
Five column charts with Axis = `JobSatisfaction`, `EnvironmentSatisfaction`, `WorkLifeBalance`, `RelationshipSatisfaction` and Values = `[Attrition Rate]`; plus a 100% stacked column (Axis `JobSatisfaction`, Legend `Attrition`, Values `[Total Employees]`) for "Employee Attrition by Satisfaction Level". Scale reminder: 1 = Low ... 4 = Very High (WorkLifeBalance 1 = Bad ... 4 = Best).

### Page 4 - Department Performance
| Visual | Fields |
|---|---|
| Column - employee count | Axis `Department`; Values `[Total Employees]` |
| Column - attrition rate | Axis `Department`; Values `[Attrition Rate]` |
| Column - average salary | Axis `Department`; Values `[Average Salary]` |
| Column - average experience | Axis `Department`; Values `[Average Experience (Years)]` |
| Treemap - job role distribution | Group `JobRole`; Values `[Total Employees]` |

## 4. Quick validation (compare with this project's numbers)
With no slicers selected the cards must read: **Total 1,470 - Active 1,233 - Attrition 237 - Rate 16.1% - Avg age 36.9 - Avg salary 6,503**. If they differ, the wrong file or column types were loaded.

## 5. Publish
Save as `powerbi/HR_Analytics_Dashboard.pbix`, export page screenshots to `docs/screenshots/`, and reference them in the README.
