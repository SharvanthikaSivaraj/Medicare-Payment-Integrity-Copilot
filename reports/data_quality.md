# Data quality report

## Billing files

| file | rows | cols | invalid NPI | duplicate NPI | missing type | missing state |
| --- | --- | --- | --- | --- | --- | --- |
| partb_provider_2022 | 1,230,293 | 81 | 0 (0.00%) | 0 | 0 | 0 |
| partb_provider_2023 | 1,259,343 | 81 | 0 (0.00%) | 0 | 0 | 0 |
| partb_provider_2024 | 1,296,739 | 81 | 0 (0.00%) | 0 | 0 | 0 |
| partd_provider_2022 | 1,332,309 | 84 | 0 (0.00%) | 0 | 4 | 0 |
| partd_provider_2023 | 1,380,665 | 84 | 0 (0.00%) | 0 | 3 | 0 |
| partd_provider_2024 | 1,416,883 | 84 | 0 (0.00%) | 0 | 2 | 0 |

## Numeric column problems

Columns with negative values or text that is not a number:

_none_

## LEIE exclusion list

- Total exclusion records: 84,093
- Records with an NPI: 8,924 (10.61%)
- Records with a valid NPI: 8,924
- Unique excluded NPIs: 8,743
- Excluded NPIs found in billing data (any year): 865
- **Usable labels** (billed before exclusion year): 802

Usable labels by exclusion year:

| exclusion year | providers |
| --- | --- |
| 2023 | 116 |
| 2024 | 232 |
| 2025 | 220 |
| 2026 | 234 |

Most common exclusion types among usable labels:

| exclusion type | records |
| --- | --- |
| 1128b4 | 356 |
| 1128a1 | 235 |
| 1128a4 | 100 |
| 1128a3 | 58 |
| 1128a2 | 27 |
| 1128b7 | 16 |
| 1128b1 | 9 |
| 1128b3 | 3 |
