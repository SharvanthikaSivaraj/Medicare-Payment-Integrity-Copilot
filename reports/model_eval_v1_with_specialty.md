# Model evaluation

Test year: 2024 (every provider scored). Train: earlier years, 10% of negatives sampled, all positives kept.

## Target: label_fraud

Test set: 1,791,280 providers, 95 positives (1 in 18,855). Random ranking would find about 0.05 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0001 | 0.535 | 0 | 0 | 0 | 1 | 2 | 0.0x | 2.1% |
| Isolation Forest (unsupervised) | 0.0001 | 0.600 | 0 | 0 | 0 | 2 | 2 | 0.0x | 2.1% |
| LightGBM (label_fraud) | 0.0021 | 0.828 | 3 | 5 | 5 | 7 | 14 | 94.3x | 14.7% |

## Target: label_any

Test set: 1,791,280 providers, 287 positives (1 in 6,241). Random ranking would find about 0.16 positives in the top 1,000.

| model | PR-AUC | ROC-AUC | hits@100 | hits@500 | hits@1000 | hits@5000 | hits@10000 | lift@1000 | recall@10000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule baseline (top-1% count) | 0.0002 | 0.529 | 0 | 0 | 0 | 3 | 5 | 0.0x | 1.7% |
| Isolation Forest (unsupervised) | 0.0003 | 0.587 | 0 | 1 | 1 | 3 | 5 | 6.2x | 1.7% |
| LightGBM (label_any) | 0.0088 | 0.810 | 9 | 13 | 18 | 32 | 43 | 112.3x | 15.0% |

## What drives the label_fraud model (mean |SHAP|, top 15)

| feature | importance |
| --- | --- |
| specialty | 0.9008 |
| d_supply_per_claim | 0.4223 |
| b_srvcs_per_bene | 0.3791 |
| d_lis_share | 0.3289 |
| d_claims_per_bene | 0.3011 |
| b_charge_to_allowed | 0.2900 |
| b_risk_score | 0.2630 |
| d_cost_per_claim | 0.2325 |
| b_dual_share | 0.2309 |
| b_benes | 0.2272 |
| b_srvcs_per_code | 0.2071 |
| d_cost_per_bene | 0.1981 |
| d_benes | 0.1933 |
| d_claims | 0.1874 |
| peer_group_size | 0.1874 |

## Top 10 providers (test year)

| rank | specialty | state | later excluded (fraud) | top reason |
| --- | --- | --- | --- | --- |
| 1 | Psychiatry & Neurology | OH | no | specialty = Psychiatry & Neurology |
| 2 | Internal Medicine | MN | no | specialty = Internal Medicine |
| 3 | Internal Medicine | PA | no | specialty = Internal Medicine |
| 4 | Internal Medicine | NY | no | specialty = Internal Medicine |
| 5 | Internal Medicine | CA | no | specialty = Internal Medicine |
| 6 | Podiatry | MI | no | specialty = Podiatry |
| 7 | Otolaryngology | SC | no | specialty = Otolaryngology |
| 8 | Family Practice | PA | no | specialty = Family Practice |
| 9 | Chiropractic | KS | no | specialty = Chiropractic |
| 10 | Pain Management | CA | no | specialty = Pain Management |

NPIs are kept out of this report on purpose; they are in the risk-score file.
