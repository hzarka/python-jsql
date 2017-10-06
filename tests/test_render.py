import jsql
import pytest
import logging

logging.basicConfig(level=logging.DEBUG)

PARAMS = {
    'safe': 'safe',
    'unsafe': '" unsafe',
}


def test_simple_bind():
    tmpl = jsql.render('table_{{safe}}', PARAMS)
    assert tmpl == 'table_safe'

def test_unsafe_bind():
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('table_{{unsafe}}', PARAMS)

def test_dangerous_bind():
    tmpl = jsql.render('`{{unsafe | dangerously_inject_sql }}`', PARAMS)
    assert tmpl == '`" unsafe`'

def test_missing_param():
    tmpl = jsql.render('{% if xyz %}AND xyz=:xyz{% endif %}', PARAMS)
    assert tmpl == ''

def test_raw_comma_bind():
    tmpl = jsql.render('{{ "," if False }}', {})
    assert tmpl == ''
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ "," if True }}', {})

def test_safe_comma_bind():
    tmpl = jsql.render('{{ comma if False }}', {})
    assert tmpl == ''
    tmpl = jsql.render('{{ comma if True }}', {})
    assert tmpl == ','

def test_comma_loop():
    tmpl = jsql.render('{% for i in range(3) %} SQL {{ i + 1 }}{{ comma if not loop.last }}{% endfor %}', {})
    assert tmpl == ' SQL 1, SQL 2, SQL 3'

def test_check_if_else_if():
    tmpl = jsql.render('{{ safe if True else unsafe }}', PARAMS)
    assert tmpl == 'safe'
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ safe if False else unsafe }}', PARAMS)

def test_check_if_else_else():
    tmpl = jsql.render('{{ unsafe if False else safe }}', PARAMS)
    assert tmpl == 'safe'
    with pytest.raises(jsql.UnsafeSqlException):
        tmpl = jsql.render('{{ unsafe if True else safe }}', PARAMS)

