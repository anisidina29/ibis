SELECT sum(t0.`d`) OVER (ORDER BY t0.`f` ASC ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) AS `foo`
FROM alltypes t0