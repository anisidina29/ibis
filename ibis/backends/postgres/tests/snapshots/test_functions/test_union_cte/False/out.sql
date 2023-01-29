WITH anon_1 AS (SELECT t0.string_col AS string_col, sum(t0.double_col) AS metric FROM functional_alltypes AS t0 GROUP BY 1), anon_2 AS (SELECT t0.string_col AS string_col, sum(t0.double_col) AS metric FROM functional_alltypes AS t0 GROUP BY 1), anon_3 AS (SELECT t0.string_col AS string_col, sum(t0.double_col) AS metric FROM functional_alltypes AS t0 GROUP BY 1) SELECT anon_1.string_col, anon_1.metric FROM anon_1 UNION ALL SELECT anon_2.string_col, anon_2.metric FROM anon_2 UNION ALL SELECT anon_3.string_col, anon_3.metric FROM anon_3