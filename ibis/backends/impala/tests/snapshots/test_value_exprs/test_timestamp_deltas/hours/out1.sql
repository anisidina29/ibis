SELECT
  CAST(CAST(`t0`.`i` AS TIMESTAMP) + INTERVAL '5' HOUR AS TIMESTAMP) AS `TimestampAdd(i, 5h)`
FROM `alltypes` AS `t0`