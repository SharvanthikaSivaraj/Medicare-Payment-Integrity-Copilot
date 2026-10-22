# Coverage checker vs human review (qwen7b)

120 blind-labeled questions across 56 notes.

## Agreement with the human reviewer

| what is compared | accuracy | Cohen's kappa |
| --- | --- | --- |
| Model's raw answer | 88.3% | 0.74 |
| Answer after the evidence guard | 88.3% | 0.72 |
| Criterion status (met / not_met / not_documented) | 93.3% | 0.86 |

Kappa: 0 = chance agreement, 0.4-0.6 moderate, 0.6-0.8 substantial, above 0.8 near perfect.

## Evidence guard

- The guard rejected 4 of the labeled answers; in 2 of them the model's answer was also wrong according to the human, so rejecting it was correct.

## Answers after the guard vs human (rows = human)

|  | yes | no | not_mentioned |
| --- | --- | --- | --- |
| human: yes | 15 | 3 | 2 |
| human: no | 2 | 7 | 5 |
| human: not_mentioned | 1 | 1 | 84 |

## Contradiction errors (the costliest mistakes)

- False contradictions (checker says the note contradicts coverage, human disagrees): **1**
- Missed contradictions (human found one, checker did not): **4**

| note | criterion | model evidence | human comment |
| --- | --- | --- | --- |
| EPI-043 | EPI-C15 | I then went up to the L4-5 level, and using a similar technique, injected the patient transforaminally at the L4-5 level |  |

## Accuracy per question (worst first)

| criterion_id | question | labeled | accuracy |
| --- | --- | --- | --- |
| EPI-C12 | Was moderate or deep sedation (including IV conscious sedation), general anesthesia or monitored anesthesia care (MAC) used? | 9 | 67% |
| EPI-C02 | Does the note document that the radicular pain or claudication significantly affects quality of life or function? | 3 | 67% |
| FAC-C07 | Does the note document another cause for the pain besides the facet joints (for example fracture, tumor, infection or significant deformity)? | 3 | 67% |
| CAT-C01 | Does the note document a cataract that impairs vision and limits daily activities (for example reading, driving, TV) despite glasses or contact lenses? | 5 | 80% |
| EPI-C04 | Was the injection performed under fluoroscopic or CT guidance with contrast? | 5 | 80% |
| EPI-C15 | Was more than one spinal region (cervical, thoracic, lumbar) injected in this session? | 7 | 86% |
| CAT-C05 | Does the note document that the cataract interferes with vitreoretinal surgery? | 16 | 100% |
| CAT-C03 | Does the note document lens-induced disease threatening vision or eye health (for example phacomorphic or phacolytic glaucoma)? | 11 | 100% |
| EPI-C03 | Does the note document pain for at least 4 weeks AND failure or intolerance of conservative care (for example physical therapy or medications)? | 7 | 100% |
| EPI-C08 | Does the note record a pain or disability score (for example 7/10, NRS, VAS or ODI)? | 7 | 100% |
| CAT-C02 | Does the note document another eye disease (for example diabetic retinopathy or an intraocular tumor) whose monitoring or treatment is prevented by the cataract? | 6 | 100% |
| CAT-C04 | Does the note document that another procedure or treatment (for example vitrectomy or radiation) is likely to speed up the cataract? | 6 | 100% |
| FAC-C18 | Was moderate or deep sedation (including IV conscious sedation), general anesthesia or monitored anesthesia care (MAC) used? | 5 | 100% |
| BLE-C10 | Does the note mention photographs documenting the eyelid findings? | 4 | 100% |
| EPI-C16 | Were transforaminal injections performed at more than 2 nerve root levels in this session? | 4 | 100% |
| BLE-C05 | Does the note document a functional problem caused by the eyelids or brows, such as blocked vision or visual field affecting daily activities (for example reading or driving)? | 3 | 100% |
| BLE-C06 | Does the note document ptosis with a margin reflex distance (MRD1) of 2.0 mm or less? | 3 | 100% |
| BLE-C07 | Does the note document excess upper eyelid skin hanging over the lid margin (pseudoptosis) to within 2.0 mm of the pupil center? | 3 | 100% |
| EPI-C01 | Does the note document radiculopathy, radicular pain or neurogenic claudication (for example from disc herniation or spinal stenosis), post-laminectomy syndrome, or acute herpes zoster pain? | 3 | 100% |
| FAC-C02 | Does the note document pain for at least 3 months AND failure of conservative care (for example physical therapy or medications)? | 3 | 100% |
| FAC-C03 | Does the note document untreated radiculopathy or neurogenic claudication? | 3 | 100% |
| BLE-C15 | Does the note document that the eyelid covers or obstructs the pupil? | 2 | 100% |
| BLE-C08 | Does the note document excess eyelid tissue that blocks the line of sight? | 1 | 100% |
| FAC-C17 | Was the procedure performed under fluoroscopic or CT guidance? | 1 | 100% |
