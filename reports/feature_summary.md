# Feature summary

- Years: [2022, 2023, 2024]; train = [2022, 2023], test = 2024
- Peer group: specialty + state if >= 30 providers, else specialty nationally
- Rows dropped because the provider was already excluded: 160
- Columns in features.parquet: 90

## Rows and labels per year

| year | split | providers | label_any | label_fraud | label_rx | fraud % | peer groups |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | train | 1,684,269 | 340 | 158 | 53 | 0.0094 | 3,065 |
| 2023 | train | 1,741,835 | 322 | 127 | 42 | 0.0073 | 3,085 |
| 2024 | test | 1,791,280 | 287 | 95 | 26 | 0.0053 | 3,146 |

## Feature dictionary

Each feature also has `pct_` (peer percentile) and `z_` (peer robust z-score) versions.

| feature | description | missing % |
| --- | --- | --- |
| b_benes | Part B: Medicare patients seen | 31.0 |
| b_hcpcs_codes | Part B: distinct procedure codes billed | 31.0 |
| b_srvcs_per_bene | Part B: services per patient | 31.0 |
| b_pay_per_bene | Part B: Medicare payment per patient ($) | 31.0 |
| b_stdzd_per_bene | Part B: geography-standardized payment per patient ($) | 31.0 |
| b_charge_to_allowed | Part B: submitted charges / allowed amount | 31.0 |
| b_srvcs_per_code | Part B: services per distinct code (repetitive billing) | 31.0 |
| b_drug_pay_share | Part B: share of payment from drugs | 39.4 |
| b_dual_share | Part B: share of patients dual-eligible (Medicare + Medicaid) | 54.1 |
| b_under65_share | Part B: share of patients under 65 | 65.6 |
| b_risk_score | Part B: average patient risk score | 31.0 |
| d_claims | Part D: prescription claims | 20.8 |
| d_benes | Part D: patients with prescriptions | 29.1 |
| d_claims_per_bene | Part D: claims per patient | 29.1 |
| d_cost_per_claim | Part D: drug cost per claim ($) | 20.8 |
| d_cost_per_bene | Part D: drug cost per patient ($) | 29.1 |
| d_supply_per_claim | Part D: days supplied per claim | 20.8 |
| d_brand_share | Part D: share of brand-name claims | 56.4 |
| d_lis_share | Part D: share of low-income-subsidy claims | 36.8 |
| d_opioid_share | Part D: share of opioid claims | 40.8 |
| d_opioid_la_share | Part D: long-acting share of opioid claims | 79.1 |
| d_opioid_supply_per_claim | Part D: days supplied per opioid claim | 74.1 |
| d_antipsych_65_share | Part D: antipsychotic share of 65+ claims | 51.3 |
| g_b_pay_per_bene | Growth in Part B payment per patient vs last year | 58.2 |
| g_b_benes | Growth in Part B patients vs last year | 58.2 |
| g_d_cost_per_bene | Growth in Part D cost per patient vs last year | 56.8 |
