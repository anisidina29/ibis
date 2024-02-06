SELECT
  CAST(FROM_UNIXTIME(CAST(CAST(`t0`.`c` / 1000000 AS INT) AS INT)) AS TIMESTAMP) AS `TimestampFromUNIX(c, MICROSECOND)`
FROM `alltypes` AS `t0`