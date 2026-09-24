# Financial Crime Investigation Explorer

| Sheet | Encoding | Interaction |
|---|---|---|
| Alert trend | UTC day × count of alerts | Date range; click day to filter payment details |
| Geographic risk | Destination × alerts, colored by mean rule score | Destination highlight; XZ/QZ labeled fictional |
| Counterparty risk | Top counterparties by alert count | Click beneficiary; tooltip similarity and name |
| Screening distribution | Similarity histogram | Score range slider; reference threshold at 88 |
| Payment risk scatter | Log amount × model probability | Channel/color, transaction tooltip |
| False-positive analysis | Combined policy FP and FN counts by channel | Benchmark-only label; separate from human dispositions |

Global filters: date, payment channel, destination and rule-score band. Case status applies
only to the investigation source. Model comparison uses model selector, not operational
filters. Provide reset filters, clear units and a persistent simulation/human-review banner.
Use navy headings, teal signals and amber review highlights; color never establishes guilt.
