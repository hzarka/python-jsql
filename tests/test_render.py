import jsql
import pytest

def test_simple_bind():
    tmpl = jsql.render('table_{{lang}}', dict(lang='en'))
    assert tmpl == 'table_en'

def test_unsafe_bind():
    with pytest.raises(ValueError):
        tmpl = jsql.render('table_{{lang}}', dict(lang='unsafe"'))

def test_safe_bind():
    tmpl = jsql.render('`{{table | dangerous }}`', dict(table='this is potentially dangerous'))
    assert tmpl == '`this is potentially dangerous`'

def test_missing_param():
    tmpl = jsql.render('{% if xyz %}AND xyz=:xyz{% endif %}', dict())
    assert tmpl == ''

