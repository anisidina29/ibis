SELECT
  `t0`.*
FROM TABLE(TUMBLE(TABLE `table`, DESCRIPTOR(`i`), INTERVAL '15' MINUTE)) AS `t0`