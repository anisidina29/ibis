SELECT
  t0.ps_partkey,
  t0.value
FROM (
  SELECT
    t1.ps_partkey AS ps_partkey,
    t1.value AS value
  FROM (
    SELECT
      t2.ps_partkey AS ps_partkey,
      SUM(t2.ps_supplycost * t2.ps_availqty) AS value
    FROM partsupp AS t2
    JOIN supplier AS t3
      ON t2.ps_suppkey = t3.s_suppkey
    JOIN nation AS t4
      ON t4.n_nationkey = t3.s_nationkey
    WHERE
      t4.n_name = 'GERMANY'
    GROUP BY
      1
  ) AS t1
  WHERE
    t1.value > (
      SELECT
        anon_1.total
      FROM (
        SELECT
          SUM(t2.ps_supplycost * t2.ps_availqty) AS total
        FROM partsupp AS t2
        JOIN supplier AS t3
          ON t2.ps_suppkey = t3.s_suppkey
        JOIN nation AS t4
          ON t4.n_nationkey = t3.s_nationkey
        WHERE
          t4.n_name = 'GERMANY'
      ) AS anon_1
    ) * 0.0001
) AS t0
ORDER BY
  t0.value DESC