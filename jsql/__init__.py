import jinja2
import jinja2.ext
from jinja2.lexer import Token
from jinja2.utils import Markup
import re
import logging


def sql(engine, template, **params):
    tmpl = render(template, params)
    query, params = format_query_with_list_params(query, params)
    return SqlProxy(execute_sql(engine, query, params))

def render(template, params):
    return jenv.from_string(template).render(**params)

logger = logging.getLogger('jsql')

SAFE_RE = re.compile('^[A-Za-z0-9_]+$')
def assert_safe_filter(value):
    if isinstance(value, Markup):
        return value
    if not SAFE_RE.match(value):
        raise ValueError('unsafe sql param "{}"'.format(value))
    return value

class AssertSafeExtension(jinja2.ext.Extension):
    # based on https://github.com/pallets/jinja/issues/503
    def filter_stream(self, stream):
        for token in stream:
            if token.type == 'variable_end':
                yield Token(token.lineno, 'pipe', '|')
                yield Token(token.lineno, 'name', 'assert_safe')
            yield token

jenv = jinja2.Environment(autoescape=False,
            extensions=(AssertSafeExtension,))
jenv.filters["assert_safe"] = assert_safe_filter

def execute_sql(engine, query, params):
    from sqlalchemy.sql import text
    q = text(query)
    is_session = 'session' in repr(engine.__class__).lower()
    return engine.execute(q, params=params) if is_session else engine.execute(q, **params)

def get_param_keys(query):
    import re
    return set(re.findall("(?P<key>:[a-zA-Z_]+_list)", query))

def format_query_with_list_params(query, params):
    keys = get_param_keys(query)
    for key in keys:
        if key.endswith('_tuple_list'):
            query, params = _format_query_tuple_list_key(key, query, params)
        else:
            query, params = _format_query_list_key(key, query, params)
    return query, params

def _format_query_list_key(key, query, params):
    values = params.pop(key[1:])
    new_keys = []
    for i, value in enumerate(values):
        new_key = '{}_{}'.format(key, i)
        new_keys.append(new_key)
        params[new_key[1:]] = value
    new_keys_str = ", ".join(new_keys) or "null"
    query = query.replace(key, "({})".format(new_keys_str))
    return query, params

def _format_query_tuple_list_key(key, query, params):
    values = params.pop(key[1:])
    new_keys = []
    for i, value in enumerate(values):
        new_key = '{}_{}'.format(key, i)
        assert isinstance(value, tuple)
        new_keys2 = []
        for i, tuple_val in enumerate(value):
            new_key2 = '{}_{}'.format(new_key, i)
            new_keys2.append(new_key2)
            params[new_key2[1:]] = tuple_val
        new_keys.append("({})".format(", ".join(new_keys2)))
    new_keys_str = ", ".join(new_keys) or "null"
    query = query.replace(key, "({})".format(new_keys_str))
    return query, params

class ObjProxy(object):
    def __init__(self, proxied):
        self._proxied = proxied

    def __iter__(self):
        return self._proxied.__iter__()

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self._proxied, attr)

class SqlProxy(ObjProxy):
    def dicts_iter(self, dict=dict):
        result = self._proxied
        keys = result.keys()
        for r in result:
            yield dict((k, v) for k, v in zip(keys, r))

    def pk_map_iter(self, dict=dict):
        result = self._proxied
        keys = result.keys()
        for r in result:
            yield (r[0], dict((k, v) for k, v in zip(keys, r)))

    def kv_map_iter(self):
        result = self._proxied
        for r in result:
            yield (r[0], r[1])

    def scalars_iter(self):
        result = self._proxied
        for r in result:
            yield r[0]

    def pk_map(self, dict=dict):
        return dict(self.pk_map_iter())

    def kv_map(self, dict=dict):
        return dict(self.kv_map_iter())

    def dicts(self, dict=dict):
        return list(self.dicts_iter(dict=dict))

    def scalars(self):
        return list(self.scalars_iter())

    def scalar_set(self):
        return set(self.scalars_iter())

    def dict(self, dict=dict):
        try:
            return self.dicts(dict=dict)[0]
        except IndexError:
            return None

