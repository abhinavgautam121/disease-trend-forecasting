# Data card

## Source and meaning

CDC, **Weekly United States COVID-19 Cases and Deaths by State — ARCHIVED**, dataset `pwn4-m3yp`. [Source](https://data.cdc.gov/d/pwn4-m3yp). The download script queries one state, `CA`, orders by `end_date`, and preserves the exact JSON response bytes. The target is `new_cases`, not changes reconstructed from cumulative totals.

The included snapshot contains 173 California observations, January 22, 2020–May 10, 2023. Each row covers Thursday through Wednesday. The counts are cases reported during the period, including probable cases where available. They are not onset-date incidence and exclude unreported infections.

See `data/raw/metadata.json` for the actual retrieval timestamp, source query, SHA-256, source-update metadata, and the publisher's full methodological notes. The dataset is a public government aggregate; no individual records or personal identifiers are used.

## Quality policy

- The pipeline checks jurisdiction, required columns, unique week endings, Wednesday alignment, seven-day inclusive reporting periods, regular weekly spacing, integer case counts, finiteness, and nonnegativity.
- This snapshot has no missing reporting weeks, negative counts, or duplicate weeks. No values are imputed, no outliers are removed, and no synthetic rows are added. Source-reported zero counts remain zero.
- Missing reports cause an error; they are never silently converted to zero.
- The final source period is complete by calendar coverage. That does not prove all infections were reported or eliminate retrospective revisions.
- Historical backlog counts are distinct source fields. They are not added to `new_cases`, avoiding a different target definition. Summed weekly new cases need not reconcile exactly with published cumulative totals.

## Reporting changes and limitations

The source describes county-aggregate compilation, reconciliation, inclusion of confirmed/probable cases where reported, and changes relative to the earlier daily state-level series. Testing practices, at-home testing, public policy, and reporting cadence affect comparability. Counts may be retrospectively revised. These data reflect one later extract; original historical vintages are not included.

CDC discontinued new aggregate reporting on May 11, 2023 and described a final reconciliation through May 10. [CDC surveillance transition](https://www.cdc.gov/mmwr/volumes/72/wr/mm7219e1.htm). Consequently, there are fewer than five years of observations and no current forecast is supported. California was selected for a single geographically consistent demonstration, not after searching for favorable forecasting scores. It must not be generalized to every disease or jurisdiction.

## Reuse and attribution

Source metadata lists **Public Domain U.S. Government** and links to [government works guidance](https://www.usa.gov/government-works). Attribute the CDC and preserve the provenance metadata. The repository's MIT license covers original code and documentation; it does not change the data publisher's terms. CDC does not endorse this project.

