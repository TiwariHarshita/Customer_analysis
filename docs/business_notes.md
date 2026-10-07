# Business analysis notes

## Intended users and decisions

A retention analyst compares customer groups; a support lead investigates service issues; a commercial lead decides whether a targeted pilot is worth running.

## KPI definitions

- Customers: unique customer IDs in the selected population.
- Churned customers: count where Churn = Yes.
- Observed churn rate: churned customers / customers × 100.
- Average monthly charge: arithmetic mean across the selected customers.
- Churned-customer monthly charges: sum of MonthlyCharges for records labeled Yes. This is a snapshot exposure measure, not revenue loss.

The dashboard recomputes all metrics after filters. No monthly denominator or observation interval is inferred from this snapshot.

## Data decisions

Exact duplicates are removed. Duplicate IDs with different records cause validation failure. Missing TotalCharges remain missing because zero and unknown are different. Missing categorical values become Unknown. Invalid churn labels and missing core numeric fields stop the analysis. Lifecycle boundaries are inclusive: 12 is early tenure, 13 is middle tenure, 36 is middle tenure and 37 is long tenure.

## Proposed retention experiment

Use the descriptive segments to decide where to conduct interviews or examine support histories. For a future dataset of active customers, define eligibility before assignment, randomize an onboarding/support intervention against business as usual, and specify a fixed follow-up window. Measure retention difference, intervention cost, complaints and opt-outs. Decide sample size using the expected baseline and minimum effect worth detecting. Do not claim this historical dataset establishes the campaign's effectiveness.

## Acceptance criteria

Every customer belongs to exactly one tenure segment. Group totals reconcile with population totals. Dashboard filters affect all displayed KPIs. Charts label churn as a percentage and display sample sizes. Findings are regenerated from input data. SQL totals match Python totals.
