import jsql
import pytest
import logging
import copy

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def params():
    return {
        'safe': 'safe',
        'unsafe': '" unsafe',
        'tbl': [{'a': 1, 'b': 2}, {'a': 1, 'c': 2}],
        'hex_list': ('abc123', 'deadbeef'),
    }


def test_simple_bind(params):
    tmpl = jsql.render('table_{{safe}}', params)
    assert tmpl == 'table_safe'

def test_unsafe_bind(params):
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('table_{{unsafe}}', params)

def test_dangerous_bind(params):
    tmpl = jsql.render('`{{unsafe | dangerously_inject_sql }}`', params)
    assert tmpl == '`" unsafe`'

def test_missing_param(params):
    tmpl = jsql.render('{% if xyz %}AND xyz=:xyz{% endif %}', params)
    assert tmpl == ''

def test_raw_comma_bind(params):
    tmpl = jsql.render('{{ "," if False }}', {})
    assert tmpl == ''
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ "," if True }}', {})

def test_safe_comma_bind(params):
    tmpl = jsql.render('{{ comma if False }}', {})
    assert tmpl == ''
    tmpl = jsql.render('{{ comma if True }}', {})
    assert tmpl == ','

def test_comma_loop(params):
    tmpl = jsql.render('{% for i in range(3) %} SQL {{ i + 1 }}{{ comma if not loop.last }}{% endfor %}', {})
    assert tmpl == ' SQL 1, SQL 2, SQL 3'

def test_check_if_else_if(params):
    tmpl = jsql.render('{{ safe if True else unsafe }}', params)
    assert tmpl == 'safe'
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ safe if False else unsafe }}', params)

def test_check_if_else_else(params):
    tmpl = jsql.render('{{ unsafe if False else safe }}', params)
    assert tmpl == 'safe'
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ unsafe if True else safe }}', params)

def test_bindparam_union(params):
    params = params
    tmpl = jsql.render('''
        SELECT * FROM (
            {%- for row in tbl -%}
            {% set outer_loop = loop %}
            ({%- for key in tbl[0].keys() -%}:{{ bindparam(row.get(key)) }}{% if outer_loop.first %} as {{ key }}{% endif %}{{ comma if not loop.last }} {% endfor %}) {% if not loop.last %}UNION ALL {%- endif -%}
            {%- endfor -%}
        )
    ''', params)
    assert tmpl == '''
        SELECT * FROM (
            (:bp0 as a, :bp1 as b ) UNION ALL
            (:bp2, :bp3 ) )
    '''
    assert (params['bp0'], params['bp1'], params['bp2'], params['bp3']) == (params['tbl'][0]['a'], params['tbl'][0]['b'], params['tbl'][1]['a'], params['tbl'][1].get('b'))

def test_bindparam_unhex(params):
    tmpl = jsql.render('''
        SELECT * FROM tbl WHERE binary IN
        ({% for hexval in hex_list %}UNHEX(:{{ bindparam(hexval) }}){{ comma if not loop.last }}{% endfor %})
    ''', params)
    assert tmpl == '''
        SELECT * FROM tbl WHERE binary IN
        (UNHEX(:bp0),UNHEX(:bp1))
    '''
    assert (params['bp0'], params['bp1']) == (params['hex_list'][0], params['hex_list'][1])

