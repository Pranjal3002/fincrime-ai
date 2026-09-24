# Build Financial Crime Investigation Explorer

1. Run `python scripts/run_all.py`. Connect Tableau Public/Desktop to
   `data/curated/transaction_explorer_sample.csv` for an explicitly labeled 5000-row preview,
   or connect to the full fact/dimension files for complete volume analysis.
2. For the full model, use relationships at the logical layer as documented in
   SOURCE_MAPPING.md. Avoid physical joins that duplicate fact rows. Parse UTC timestamp
   as Date & Time, amount/risk/probability as Number, and alert flag as Boolean.
3. Create the fields in CALCULATED_FIELDS.md. Build the six sheets described in
   DASHBOARD_SPECIFICATION.md and place them on a 1440×1000 dashboard.
4. Use date, channel, destination, rule and alert-status filters only on sheets with those
   fields at the correct grain. Add highlight actions between geography and scatterplot,
   and a transaction detail tooltip showing reason codes and reference similarity.
5. Import model_comparison.csv separately for held-out evaluation; keep its filters separate
   from the operations dashboard. Join no benchmark metric to repeated transaction rows.
6. Save locally using the desktop application's supported workflow. Reopen the result and
   check row counts, sums, filters and labels. Only then record workbook completion and
   capture genuine Tableau screenshots. Public publishing is not required or performed.
