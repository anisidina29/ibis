SELECT `key`, sum(((`value` + 1) + 2) + 3) AS `abc`
FROM t0
WHERE `value` = 42
GROUP BY 1