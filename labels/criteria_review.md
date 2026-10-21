# Coverage criteria review

The local SLM drafted the criteria; every quote was checked to exist in the policy text.
This file records the **review**: which criteria are kept for checking notes, how they combine, and why the rest were dropped.
Reviewer: reviewed by Sharvanthikha.

## What the review found

| problem | count | example |
| --- | --- | --- |
| Real quote, but taken from the definitions section and turned into a rule | 12 | FAC-C39 'patient must have radiculopathy' contradicts FAC-C03 |
| Quote is real but supports a different statement | 7 | EPI-C26 'performed by a physician', quoted from a sentence about the GRADE system |
| Needs a year of claims history, not checkable from one note | 6 | 'no more than 4 sessions per rolling 12 months' |

A verified quote proves the text exists, not that the model understood it.

## Cataract surgery (L34203)

**Decision rule:** AT LEAST ONE of CAT-C01, CAT-C02, CAT-C03, CAT-C04, CAT-C05. Policy: covered when one (or more) of the listed conditions is documented.

Kept 5 of 9.

| id | type | criterion | review |
| --- | --- | --- | --- |
| CAT-C01 | indication | Cataract causing symptomatic (i.e., causing the patient to seek medical attention) impairment of visual function not correctable with a tolerable change in glasses or contact lenses resulting in the patient's inability to function satisfactorily while performing Activities of Daily Life including, but not limited to reading, viewing television, driving, or meeting vocational or recreational needs. | kept as drafted |
| CAT-C02 | indication | Concomitant intraocular disease (e.g., diabetic retinopathy or intraocular tumor) requiring monitoring or treatment that is prevented by the presence of cataract. | kept as drafted |
| CAT-C03 | indication | Lens-induced disease threatening vision or ocular health (including, but not limited to, phacomorphic or phacolytic glaucoma). | kept as drafted |
| CAT-C04 | indication | High probability of accelerating cataract development as a result of a concomitant or subsequent procedure (e.g., pars plana vitrectomy, iridocyclectomy, procedure for ocular trauma) and treatments such as external beam irradiation. | kept as drafted |
| CAT-C05 | indication | Cataract interfering with the performance of vitreoretinal surgery. | kept as drafted |

<details><summary>Dropped items and reasons</summary>

| id | drafted criterion | reason |
| --- | --- | --- |
| CAT-C06 | Any circumstances not listed may be considered based on the standard of care and other fac | general statement about redetermination, not a criterion |
| CAT-C07 | results and indications of medical necessity properly documented | too vague or general to check |
| CAT-C08 | the need to restore binocular vision and resolve anisometropia | sentence fragment taken from a longer requirement |
| CAT-C09 | medical necessity for each procedure to be performed | applies only when both eyes are planned in advance; too vague or general to check |

</details>

## Facet joint injection / medial branch block / radiofrequency ablation (L33930)

**Decision rule:** ALL of FAC-C01, FAC-C02, FAC-C03, FAC-C07, FAC-C17, FAC-C18, FAC-C31. Policy indications are joined with AND; image guidance, no routine sedation and documented pain scales are also required.

Kept 7 of 42.

| id | type | criterion | review |
| --- | --- | --- | --- |
| FAC-C01 | indication | Moderate to severe chronic neck or low back pain, predominantly axial, that causes functional deficit measured on pain or disability scale 6 | kept as drafted |
| FAC-C02 | indication | Pain that has been present for a minimum of 3 months with documented failure to respond to noninvasive conservative care management (as tolerated) | kept as drafted |
| FAC-C03 | indication | Absence of untreated radiculopathy or neurogenic claudication (except for radiculopathy caused by facet joint synovial cyst) | kept as drafted |
| FAC-C07 | indication | No non-facet pathology per clinical assessment or radiology studies that could explain the source of the patient’s pain. | kept as drafted |
| FAC-C17 | limitation | The procedure was performed under CT or fluoroscopic guidance | reworded as a checkable statement |
| FAC-C18 | limitation | No moderate/deep sedation, general anesthesia or MAC was used during the facet injection | reworded as a checkable statement; quote replaced with the matching policy sentence |
| FAC-C31 | documentation | A pain and/or disability scale is documented | reworded as a checkable statement |

<details><summary>Dropped items and reasons</summary>

| id | drafted criterion | reason |
| --- | --- | --- |
| FAC-C04 | The patient must meet the criteria for the first diagnostic facet joint injection. | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C05 | The patient must have had 2 medically reasonable and necessary diagnostic facet joint proc | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C06 | Subsequent therapeutic facet joint procedures at the same anatomic site results in at leas | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C08 | No more than 4 diagnostic joint sessions per rolling 12 months. | needs claims history across visits; cannot be checked from a single procedure note |
| FAC-C09 | No more than 4 therapeutic facet joint injection sessions per rolling 12 months. | needs claims history across visits; cannot be checked from a single procedure note |
| FAC-C10 | Documentation of why the patient is not a candidate for radiofrequency ablation. | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C11 | After the patient has had at least 2 medically reasonable and necessary diagnostic MBBs, w | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C12 | Repeat 6 facet joint RFA at the same anatomic site is considered medically reasonable and  | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C13 | Advanced diagnostic imaging study (e.g., magnetic resonance imaging [MRI]/ computed tomogr | synovial cyst cases only |
| FAC-C14 | Clinical and physical symptoms related to synovial facet cyst are documented in the medica | synovial cyst cases only |
| FAC-C15 | No more than 2 radiofrequency sessions will be reimbursed per rolling 12 months. | needs claims history across visits; cannot be checked from a single procedure note |
| FAC-C16 | 50% or more consistent improvement in pain for at least 3 months. | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C19 | Routine use of Moderate Sedation or Monitored Anesthesia Care (MAC) or use of General Anes | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C20 | It is not routinely necessary for multiple blocks (e.g., epidural injections, sympathetic  | about other blocks on the same day; rare in these notes |
| FAC-C21 | If performed, the medical necessity of each injection (at the same or a different level[s] | too vague or general to check |
| FAC-C22 | Documentation of medical necessity such as a longstanding well-documented history of inabi | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C23 | Documentation of medical necessity for each injection (at the same or a different level[s] | quote does not support the criterion (quote is a different sentence) |
| FAC-C24 | Therapeutic facet injections are not covered unless there is justification in the medical  | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| FAC-C25 | Facet joint procedures in patients for the indication of generalized pain conditions (such | covered by FAC-C07 (no other explanation for the pain) |
| FAC-C26 | In patients with implanted electrical devices, providers must follow manufacturer instruct | device safety instruction, not a coverage criterion |
| FAC-C27 | Non-thermal modalities for facet joint denervation including chemical, low-grade thermal e | item from the list of non-covered techniques; not relevant to injection notes |
| FAC-C28 | Intra-facet implants | item from the list of non-covered techniques; not relevant to injection notes |
| FAC-C29 | Facet joint procedure performed after anterior lumbar interbody fusion or ALIF | item from the list of non-covered techniques; not relevant to injection notes |
| FAC-C30 | Definitive clinical and/or imaging findings pointing to a specific diagnosis other than fa | covered by FAC-C07 |
| FAC-C32 | The new onset of the spinal pain must be materially and significantly different in locatio | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C33 | The patient must have generalized allodynia which is causally related to the increased res | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C34 | The patient must have cervical facet pain, which may be characterized by chronic headaches | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C35 | The patient must have chronic pain persisting for greater than or equal to 12 weeks after  | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C36 | The patient must have chronic low back pain. | quote does not support the criterion (quote is a different sentence) |
| FAC-C37 | The patient must have non-radicular back pain that is not causally related to a spinal ner | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C38 | The patient must have peripheral neuropathic pain that is causally related to a lesion or  | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C39 | The patient must have radiculopathy, which is radiating neuropathic pain causally related  | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C40 | The patient must have a specific region of the back involved, defined as C1-C7/T1-T12 or L | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C41 | The patient must have subacute pain, which occurs during the 4-12-week time period. | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| FAC-C42 | The patient must have a specific type of injection, such as TFESI, performed via a paramed | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |

</details>

## Epidural steroid injection (L39240)

**Decision rule:** ALL of EPI-C01, EPI-C02, EPI-C03, EPI-C04, EPI-C08, EPI-C12, EPI-C13, EPI-C15, EPI-C16. Policy indications are joined with AND; image guidance, no routine sedation, a documented pain scale and the session limits are also required.

Kept 9 of 29.

| id | type | criterion | review |
| --- | --- | --- | --- |
| EPI-C01 | indication | History, exam and imaging support radiculopathy, radicular pain or neurogenic claudication (e.g., disc herniation or stenosis), post-laminectomy syndrome, or acute herpes zoster pain | reworded as a checkable statement |
| EPI-C02 | indication | Radiculopathy, radicular pain and/or neurogenic claudication is severe enough to greatly impact quality of life or function. | kept as drafted |
| EPI-C03 | indication | Pain duration of at least four (4) weeks, and the inability to tolerate noninvasive conservative care or medical documentation of failure to respond to four (4) weeks of noninvasive conservative care or acute herpes zoster refractory to conservative management where a four (4) week wait is not required. | kept as drafted |
| EPI-C04 | limitation | The injection was performed under CT or fluoroscopic guidance with contrast (unless contrast allergy is documented) | reworded as a checkable statement |
| EPI-C08 | documentation | A pain and/or disability scale is documented (e.g., NRS, VAS, ODI) | reworded as a checkable statement; quote replaced with the matching policy sentence |
| EPI-C12 | limitation | No moderate/deep sedation, general anesthesia or MAC was used | reworded as a checkable statement |
| EPI-C13 | limitation | The pain being treated is not non-specific low back pain or axial-only spine pain | reworded as a checkable statement |
| EPI-C15 | limitation | Only one spinal region was injected in the session | reworded as a checkable statement |
| EPI-C16 | limitation | Transforaminal injections were done at no more than 2 nerve root levels in the session | reworded as a checkable statement |

<details><summary>Dropped items and reasons</summary>

| id | drafted criterion | reason |
| --- | --- | --- |
| EPI-C05 | It is medically reasonable and necessary to perform TFESIs bilaterally only when clinicall | bilateral TFESI is allowed when clinically indicated; too vague or general to check |
| EPI-C06 | Repeat ESI when the first injection directly and significantly provided improvement of the | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| EPI-C07 | If a patient fails to respond well to the initial ESI, a repeat ESI after 14 days can be p | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| EPI-C09 | An initial injection of contrast is required to confirm epidural placement, unless the pat | covered by EPI-C04 (contrast use) |
| EPI-C10 | ESIs should be performed in conjunction with conservative treatments. | too vague or general to check |
| EPI-C11 | It is not considered medically reasonable and necessary to perform multiple blocks (ESI, s | about other blocks in the same session; rare in these notes |
| EPI-C14 | ESIs are limited to a maximum of four (4) sessions per spinal region in a rolling twelve ( | needs claims history across visits; cannot be checked from a single procedure note |
| EPI-C17 | It is not medically reasonable and necessary to perform CESIs or ILESIs bilaterally. | rare in these notes |
| EPI-C18 | It is not medically reasonable and necessary to prescribe a predetermined series of ESIs. | needs claims history across visits; cannot be checked from a single procedure note |
| EPI-C19 | Steroid dosing should be the lowest effective amount, it is recommended not to exceed 80 m | dosing guidance (recommended, not required) |
| EPI-C20 | It generally would not be considered medically reasonable and necessary for treatment with | needs claims history across visits; cannot be checked from a single procedure note |
| EPI-C21 | Pain is severe enough to cause a significant degree of functional disability or vocational | covered by EPI-C02 |
| EPI-C22 | ESI provides at least 50% sustained improvement of pain and/or 50% objective improvement i | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| EPI-C23 | The primary care provider must be notified regarding continuation of procedures and prolon | applies to repeat/therapeutic/RFA procedures, not a single procedure note in this evaluation |
| EPI-C24 | The patient must have radiculopathy | covered by EPI-C01 |
| EPI-C25 | The procedure must be performed under fluoroscopic guidance | quote does not support the criterion (quote is a different sentence) |
| EPI-C26 | The procedure must be performed by a physician | quote does not support the criterion (quote is a different sentence) |
| EPI-C27 | The procedure must be documented in the medical record | quote does not support the criterion (quote is a different sentence) |
| EPI-C28 | The temporal definition of pain occurring during the six to twelve-week time period. | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |
| EPI-C29 | The temporal definition of pain occurring 12 weeks after the onset of the pain. | misread from the policy's definitions/glossary section; it describes a term, not a coverage requirement |

</details>

## Blepharoplasty (eyelid surgery) (L34194)

**Decision rule:** ALL of BLE-C05, BLE-C10 AND AT LEAST ONE of BLE-C06, BLE-C07, BLE-C08, BLE-C15. A documented functional deficit and photographs are required, plus at least one physical sign (MRD of 2.0 mm or less, pseudoptosis, tissue obscuring the line of sight, or lid obstructing the pupil).

Kept 6 of 18.

| id | type | criterion | review |
| --- | --- | --- | --- |
| BLE-C05 | indication | A functional deficit or disturbance secondary to eyelid and/or brow abnormalities must be documented, such as interference with vision or visual field that impacts an activity of daily living (such as difficulty reading or driving). | kept as drafted |
| BLE-C06 | limitation | Ptosis with a margin reflex distance (MRD1) of 2.0 mm or less | reworded as a checkable statement |
| BLE-C07 | limitation | Redundant upper lid skin hanging over the lid margin with a pseudo-MRD of 2.0 mm or less | reworded as a checkable statement |
| BLE-C08 | limitation | Redundant lid tissue medially or laterally that obscures the line of sight | reworded as a checkable statement |
| BLE-C10 | documentation | Photographs documenting the eyelid findings are referenced in the record | reworded as a checkable statement |
| BLE-C15 | indication | If the eyelid obstructs the pupil, there is a clear-cut indication for surgery. | kept as drafted |

<details><summary>Dropped items and reasons</summary>

| id | drafted criterion | reason |
| --- | --- | --- |
| BLE-C01 | For the purposes of this policy, these surgeries (either individually or in the minimum co | background definition; the checkable parts are BLE-C05 to BLE-C08 |
| BLE-C02 | Published literature correlates this amount of field restriction with a Margin Reflex Dist | background on why 2.0 mm is used; covered by BLE-C06/C07 |
| BLE-C03 | When a noncovered cosmetic surgical procedure is performed in the same operative session a | billing rule, not a clinical criterion |
| BLE-C04 | Reasonably complete information fulfilling the criteria in Section A (Patient Complaints a | covered by BLE-C05 and BLE-C10 |
| BLE-C09 | When requested documentation does not meet the criteria for the service rendered or the do | general statement about denials |
| BLE-C11 | Unless medial/lateral gaze is required to demonstrate a specific deficit, photos should be | photo technical detail; not checkable from an operative note |
| BLE-C12 | Oblique photos are only necessary if needed to better demonstrate a finding not clearly sh | photo technical detail; not checkable from an operative note |
| BLE-C13 | Digital or film photographs are acceptable, and may be submitted electronically where poss | photo technical detail; not checkable from an operative note |
| BLE-C14 | Photographs must be identified with the beneficiary’s name and the date. | photo technical detail; not checkable from an operative note |
| BLE-C16 | For reference, the colored part of the eye is about 11 mm in diameter, so the distance bet | explanatory reference about eye size |
| BLE-C17 | Two photos are needed:One showing both eyes of the patient at rest demonstrating the above | photo technical detail; not checkable from an operative note |
| BLE-C18 | If both a blepharoplasty and a ptosis repair are planned, both must be individually docume | applies only when both procedures are planned |

</details>

