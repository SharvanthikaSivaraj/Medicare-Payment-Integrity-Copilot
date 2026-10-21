# Model evaluation

Test year: 2024 (every provider scored). Train: earlier years, 10% of negatives sampled, all positives kept. Specialty used as a model input: no (behavior features only). Graph / industry-payment features: yes.

## Target: label_fraud

Test set: 1,791,280 providers, 95 positives (1 in 18,855). Random ranking would find about 0.05 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0001 | 0.544 | 0 | 0 | 0 | 0 | 2 | 0.0x | 2.1% |
| Isolation Forest (unsupervised) | 0.0001 | 0.576 | 0 | 0 | 0 | 1 | 2 | 0.0x | 2.1% |
| LightGBM (label_fraud) | 0.0091 | 0.792 | 3 | 4 | 5 | 9 | 9 | 94.3x | 9.5% |

## Target: label_any

Test set: 1,791,280 providers, 287 positives (1 in 6,241). Random ranking would find about 0.16 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0002 | 0.523 | 0 | 1 | 1 | 1 | 5 | 6.2x | 1.7% |
| Isolation Forest (unsupervised) | 0.0002 | 0.560 | 0 | 0 | 0 | 2 | 4 | 0.0x | 1.4% |
| LightGBM (label_any) | 0.0067 | 0.791 | 7 | 12 | 18 | 30 | 38 | 112.3x | 13.2% |

## What drives the label_fraud model (mean |SHAP|, top 15)

| feature | importance |
| --- | --- |
| d_lis_share | 0.7232 |
| d_supply_per_claim | 0.6521 |
| d_cost_per_claim | 0.6082 |
| d_claims_per_bene | 0.5659 |
| b_charge_to_allowed | 0.4600 |
| b_srvcs_per_code | 0.4221 |
| b_benes | 0.4076 |
| b_risk_score | 0.3974 |
| b_srvcs_per_bene | 0.3764 |
| d_claims | 0.3575 |
| d_brand_share | 0.3365 |
| b_dual_share | 0.3187 |
| d_cost_per_bene | 0.2892 |
| d_benes | 0.2749 |
| g_b_benes | 0.2616 |

## Top 10 providers (test year)

| rank | specialty | state | later excluded (fraud) | top reason |
| --- | --- | --- | --- | --- |
| 1 | Psychiatry & Neurology | NY | no | d_supply_per_claim = 87 (top 1% of peers) |
| 2 | Internal Medicine | CA | no | d_cost_per_claim = 6.9 (bottom 1% of peers) |
| 3 | Physician Assistant | MI | yes | d_supply_per_claim = 34.4 (top 41% of peers) |
| 4 | Naturopath | OR | no | d_supply_per_claim = 20 (bottom 2% of peers) |
| 5 | Internal Medicine | PA | yes | b_benes = 16 (bottom 2% of peers) |
| 6 | Otolaryngology | PA | no | d_cost_per_claim = 3.28 (bottom 1% of peers) |
| 7 | Physical Medicine and Rehabilitation | CA | no | d_opioid_share = 59% (top 6% of peers) |
| 8 | Osteopathic Manipulative Medicine | CA | no | d_claims = 1.3e+04 (top 3% of peers) |
| 9 | Internal Medicine | FL | no | d_claims_per_bene = 1.93 (bottom 7% of peers) |
| 10 | Certified Registered Nurse Anesthetist (CRNA) | PA | no | b_benes = 15 (bottom 1% of peers) |

NPIs are kept out of this report on purpose; they are in the risk-score file.
