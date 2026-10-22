# Coverage check

Model: qwen2.5:7b, 59 notes, 379 questions, 22 s per note on average.

## Evidence guard

- Yes/no answers from the model: 109
- Accepted with a verified quote: 84
- Rejected, no quote given: 3
- Rejected, quote not found in the note: 22
- Model errors (timeout or invalid output, treated as not mentioned): 0

## Verdicts per procedure

| topic | DOCUMENTATION_DEFICIT | MEETS_COVERAGE | UNSUPPORTED |
| --- | --- | --- | --- |
| blepharoplasty | 7 | 1 | 0 |
| cataract | 14 | 9 | 0 |
| epidural_steroid_injection | 14 | 0 | 6 |
| facet_joint | 3 | 0 | 5 |

## Criterion statuses per procedure

| topic | met | not_documented | not_met |
| --- | --- | --- | --- |
| blepharoplasty | 4 | 44 | 0 |
| cataract | 9 | 106 | 0 |
| epidural_steroid_injection | 71 | 81 | 8 |
| facet_joint | 19 | 32 | 5 |

## What most often caused a deficit or contradiction

| criterion_id | question | notes |
| --- | --- | --- |
| one of CAT-C01/CAT-C02/CAT-C03/CAT-C04/CAT-C05 | (group of alternatives) | 14 |
| EPI-C03 | Does the note document pain for at least 4 weeks AND failure or intolerance of conservative care (for example physical therapy or medications)? | 14 |
| EPI-C02 | Does the note document that the radicular pain or claudication significantly affects quality of life or function? | 13 |
| EPI-C08 | Does the note record a pain or disability score (for example 7/10, NRS, VAS or ODI)? | 13 |
| EPI-C01 | Does the note document radiculopathy, radicular pain or neurogenic claudication (for example from disc herniation or spinal stenosis), post-laminectomy syndrome, or acute herpes zoster pain? | 10 |
| EPI-C04 | Was the injection performed under fluoroscopic or CT guidance with contrast? | 8 |
| BLE-C05 | Does the note document a functional problem caused by the eyelids or brows, such as blocked vision or visual field affecting daily activities (for example reading or driving)? | 7 |
| BLE-C10 | Does the note mention photographs documenting the eyelid findings? | 7 |
| one of BLE-C06/BLE-C07/BLE-C08/BLE-C15 | (group of alternatives) | 6 |
| FAC-C18 | Was moderate or deep sedation (including IV conscious sedation), general anesthesia or monitored anesthesia care (MAC) used? | 5 |

These are checks by a small model to support, not replace, a human reviewer.
