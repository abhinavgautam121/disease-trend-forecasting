# Data directory

`raw/cdc_ca_weekly.json` is the exact public CDC API response for California, ordered by week end. `raw/metadata.json` records provenance, source notes, retrieval time, license metadata, and SHA-256. `processed/weekly_cases.csv` contains only `date` (Wednesday week end) and `cases` (`new_cases`).

Regenerate using `disease-forecast download` followed by `disease-forecast run`. No private data or credentials are needed. See the [data card](../reports/data_card.md) for limitations and reuse terms. The publisher identifies the source as Public Domain U.S. Government; the repository's code license does not replace those terms.

