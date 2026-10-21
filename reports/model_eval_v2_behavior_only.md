# Model evaluation

Test year: 2024 (every provider scored). Train: earlier years, 10% of negatives sampled, all positives kept. Specialty used as a model input: no (behavior features only).

## Target: label_fraud

Test set: 1,791,280 providers, 95 positives (1 in 18,855). Random ranking would find about 0.05 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0001 | 0.535 | 0 | 0 | 0 | 1 | 2 | 0.0x | 2.1% |
| Isolation Forest (unsupervised) | 0.0001 | 0.600 | 0 | 0 | 0 | 2 | 2 | 0.0x | 2.1% |
| LightGBM (label_fraud) | 0.0036 | 0.808 | 3 | 3 | 4 | 6 | 8 | 75.4x | 8.4% |

## Target: label_any

Test set: 1,791,280 providers, 287 positives (1 in 6,241). Random ranking would find about 0.16 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0002 | 0.529 | 0 | 0 | 0 | 3 | 5 | 0.0x | 1.7% |
| Isolation Forest (unsupervised) | 0.0003 | 0.587 | 0 | 1 | 1 | 3 | 5 | 6.2x | 1.7% |
| LightGBM (label_any) | 0.0032 | 0.780 | 5 | 8 | 12 | 23 | 37 | 74.9x | 12.9% |

## What drives the label_fraud model (mean |SHAP|, top 15)

| feature | importance |
| --- | --- |
| d_lis_share | 0.5976 |
| d_supply_per_claim | 0.5596 |
| d_claims_per_bene | 0.4845 |
| d_cost_per_claim | 0.4482 |
| b_charge_to_allowed | 0.4139 |
| b_srvcs_per_bene | 0.3877 |
| b_risk_score | 0.3519 |
| d_claims | 0.3201 |
| b_srvcs_per_code | 0.3130 |
| b_dual_share | 0.2950 |
| d_brand_share | 0.2918 |
| b_benes | 0.2836 |
| g_b_pay_per_bene | 0.2480 |
| d_cost_per_bene | 0.2372 |
| b_hcpcs_codes | 0.2295 |

## Top 10 providers (test year)

| rank | specialty | state | later excluded (fraud) | top reason |
| --- | --- | --- | --- | --- |
| 1 | Family Practice | TX | no | g_b_benes = -73% vs last year (bottom 1% of peers) |
| 2 | Internal Medicine | OH | no | b_charge_to_allowed = 1.68 (bottom 24% of peers) |
| 3 | Family Practice | KY | no | g_d_cost_per_bene = -70% vs last year (bottom 4% of peers) |
| 4 | Internal Medicine | OH | no | g_b_benes = -49% vs last year (bottom 4% of peers) |
| 5 | Physician Assistant | MI | yes | d_lis_share = 92% (top 2% of peers) |
| 6 | Internal Medicine | NC | no | g_b_benes = -84% vs last year (bottom 1% of peers) |
| 7 | Family Practice | OH | no | g_d_cost_per_bene = -66% vs last year (bottom 6% of peers) |
| 8 | Internal Medicine | NC | no | g_d_cost_per_bene = -74% vs last year (bottom 5% of peers) |
| 9 | Internal Medicine | LA | no | b_benes = 17 (bottom 2% of peers) |
| 10 | Internal Medicine | IL | no | b_benes = 23 (bottom 4% of peers) |

NPIs are kept out of this report on purpose; they are in the risk-score file.
