# python-jsql

Lightweight wrapper around sqlalchemy + jinja2.

```
pip install jsql==0.6
```

## Usage

Check tests for examples. 

```python
from jsql import sql

engine = sqlalchemy.create_engine('...')

with engine.begin() as conn:
    ctx = {'lang': 'en', 'country': 'us'}
    ids = [1, 2, 3, 4, 5]
    limit = 100
    products = sql(conn, '''
      SELECT id, title_{{lang}} as title
      FROM product_{{country}}
      WHERE 1=1
      {% if price_min %}AND price > :price_min{% endif %}
      {% if id_list %}AND id IN :id_list{% endif %}
      LIMIT {{limit}}
      {% endif %}
    ''', limit=limit, id_list=ids, **ctx).dicts()

```

## Notes

1) Return value is a wrapper around sqlalchemy resultproxy with some helper methods (see `jsql.SqlProxy` and `test_sqlproxy`)
1) First parameter can be a sqlalchemy engine, connection, or session
1) Variables injected using `:var` will be escaped by SQL driver.
1) Variables injected as `:var_list` will expect a list value and will be escaped by SQL driver for use as eg `id IN :id_list` (see `test_list_param`)
1) Variables injected as `:var_tuple_list` will expect a list of tuples and will be escaped by SQL driver for use as eg `(id1, id2) IN :id_tuple_list` (see `test_list_param`)
1) Variables injected using `{{var}}` will be inserted directly into the query but will be checked against jsql.NOT_DANGEROUS_RE (default `[A-Za-z0-9_]+`). This is intended for templating table names, limits, etc where SQL query placeholders are not allowed. (see `test_render`)
1) Variables injected using `{{var | dangerously_inject_sql }}` will be inserted directly into the query without any checks (probably a bad idea) (see `test_render`)

