# Statistical analysis methodology

Implementation: `src/fincrime_ai/statistics.py`. Measured outputs:
`reports/statistics.json` and `reports/EXECUTIVE_FINCRIME_ANALYTICS_REPORT.md`.

1. Describe amounts (median, mean, dispersion and tail quantiles), rule risk scores,
   alert rates and country/channel distributions. Use distribution plots, not means alone.
2. Test the exploratory null that fictional risk geography and alert flag are independent
   using a 2×2 chi-square test. Record minimum expected frequency; counts ≥5 support the
   asymptotic approximation. Cramer's V reports association magnitude.
3. Compare alerted/nonalerted value distributions using two-sided Mann-Whitney U. Positive
   skew and extreme values motivate a rank-based test. Rank-biserial correlation supplies
   effect size. Without equal distribution shapes, this is not simply a median test.
4. Use a Wilson 95% interval for the observed alert proportion and Spearman correlation
   between amount and rule score for monotone association.

These are descriptive simulation analyses. Payments repeat customers and beneficiaries,
violating independent-observation assumptions; nominal p-values and Wilson intervals
understate uncertainty under clustering. Geography and amount also help define alerts, so
tests partially reflect designed rules. A future analysis should bootstrap customers,
adjust for multiple hypotheses and validate on independently labeled future data.

Do not equate a small p-value with material business benefit or causality. Floating-point
underflow can serialize a tiny p-value as zero. Interpret effect size and queue workload
alongside significance. No claim is made about real-world financial crime prevalence.
