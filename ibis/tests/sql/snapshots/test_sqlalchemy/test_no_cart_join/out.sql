SELECT
  t1.ancestor_node_sort_order,
  1 AS n
FROM facts AS t0
JOIN (
  SELECT
    t2.ancestor_level_name AS ancestor_level_name,
    t2.ancestor_level_number AS ancestor_level_number,
    t2.ancestor_node_sort_order AS ancestor_node_sort_order,
    t2.descendant_node_natural_key AS descendant_node_natural_key,
    CONCAT(LPAD('-', (
      t2.ancestor_level_number - 1
    ) * 7, '-'), t2.ancestor_level_name) AS product_level_name
  FROM products AS t2
) AS t1
  ON t0.product_id = t1.descendant_node_natural_key
GROUP BY
  1
ORDER BY
  t1.ancestor_node_sort_order