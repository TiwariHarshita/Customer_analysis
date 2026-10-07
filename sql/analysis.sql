-- Run against results/customers.sqlite after running analysis.py.
SELECT COUNT(*) AS customers, SUM(ChurnFlag) AS churned,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct
FROM customers;

SELECT Contract, COUNT(*) AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct,
       ROUND(AVG(MonthlyCharges), 2) AS average_monthly_charge
FROM customers GROUP BY Contract ORDER BY churn_rate_pct DESC;

SELECT TenureGroup, Contract, COUNT(*) AS customers,
       ROUND(100.0 * AVG(ChurnFlag), 2) AS churn_rate_pct
FROM customers GROUP BY TenureGroup, Contract
HAVING COUNT(*) >= 30 ORDER BY churn_rate_pct DESC;
