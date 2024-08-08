import jinja2
import jinja2.ext
from jinja2.lexer import Token
import re
import logging
import six
import itertools, collections

class UnsafeSqlException(Exception):
    pass

NOT_DANGEROUS_RE = re.compile('^[A-Za-z0-9_]*$')
def is_safe(value):
    return NOT_DANGEROUS_RE.match(value)

@six.python_2_unicode_compatible
class DangerouslyInjectedSql(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

def sql(engine, template, **params):
    return sql_inner(engine, template, params)

def sql_inner(engine, template, params):
    query = render(template, params)
    query, params = format_query_with_list_params(query, params)
    return SqlProxy(execute_sql(engine, query, params))

sql_inner_original = sql_inner

def render(template, params):
    params['bindparam'] = params.get('bindparam', gen_bindparam(params))
    return jenv.from_string(template).render(**params)

logger = logging.getLogger('jsql')

def assert_safe_filter(value):
    if value is None:
        return None
    if isinstance(value, DangerouslyInjectedSql):
        return value
    value = six.text_type(value)
    if not is_safe(value):
        raise UnsafeSqlException('unsafe sql param "{}"'.format(value))
    return value

class AssertSafeExtension(jinja2.ext.Extension):
    # based on https://github.com/pallets/jinja/issues/503
    def filter_stream(self, stream):
        for token in stream:
            if token.type == 'variable_end':
                yield Token(token.lineno, 'rparen', ')')
                yield Token(token.lineno, 'pipe', '|')
                yield Token(token.lineno, 'name', 'assert_safe')
            yield token
            if token.type == 'variable_begin':
                yield Token(token.lineno, 'lparen', '(')

jenv = jinja2.Environment(autoescape=False,
            extensions=(AssertSafeExtension,))

jenv.filters["assert_safe"] = assert_safe_filter

def dangerously_inject_sql(value):
    return DangerouslyInjectedSql(value)

jenv.filters["dangerously_inject_sql"] = dangerously_inject_sql
jenv.globals["comma"] = DangerouslyInjectedSql(",")


def execute_sql(engine, query, params):
    from sqlalchemy.sql import text
    q = text(query)
    is_session = 'session' in repr(engine.__class__).lower()
    return engine.execute(q, params=params) if is_session else engine.execute(q, **params)

BINDPARAM_PREFIX = 'bp'
def gen_bindparam(params):
    keygen = key_generator()
    def bindparam(val):
        key = keygen(BINDPARAM_PREFIX)
        while key in params:
            key = keygen(BINDPARAM_PREFIX)
        params[key] = val
        return key
    return bindparam

def key_generator():
    keycnt = collections.defaultdict(itertools.count)
    def gen_key(key):
        return key + str(next(keycnt[key]))
    return gen_key

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
    new_keys_str = ", ".join(new_keys) or "null"  # NOTE: ("SELECT 'xyz' WHERE 'abc' NOT IN :i_list", i_list=[]) -> expected: 'xyz' | output: None
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
    new_keys_str = ", ".join(new_keys) or "null"  # NOTE: ("SELECT 'xyz' WHERE ('abc', '') NOT IN :i_tuple_list", i_tuple_list=[]) -> expected: 'xyz' | output: None
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

    def pk_map_many_iter(self, *keys, n:int=None, dict=dict, tuple=tuple):
        result = self._proxied
        all_keys = result.keys()
        for r in result:
            d = dict((k, v) for k, v in zip(all_keys, r))
            if len(keys) == 1:
                yield d[keys[0]], d
            elif len(keys) > 1:
                yield tuple(d[k] for k in keys), d
            elif n == 1:
                yield r[0], d
            elif n and n > 1:
                yield tuple(r[k] for k in range(n)), d
            else:
                raise ValueError('Expected either `n` as int >= 1 OR `keys` as a list of str arguments')

    def kv_map_iter(self):
        result = self._proxied
        for r in result:
            yield (r[0], r[1])

    def scalars_iter(self):
        result = self._proxied
        for r in result:
            yield r[0]

    def tuples_iter(self, tuple=tuple):
        result = self._proxied
        for r in result:
            yield tuple(r)

    def pk_map(self, dict=dict):
        return dict(self.pk_map_iter())

    def pk_map_many(self, *keys, n=None, dict=dict, tuple=tuple):
        return dict(self.pk_map_many_iter(*keys, n=n, dict=dict, tuple=tuple))

    def kv_map(self, dict=dict):
        return dict(self.kv_map_iter())

    def dicts(self, dict=dict):
        return list(self.dicts_iter(dict=dict))

    def scalars(self):
        return list(self.scalars_iter())

    def tuples(self, tuple=tuple):
        # although supported natively since version 2.0
        # https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.CursorResult.tuples
        # same as `scalars()` which was supported since version 1.4
        # https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.CursorResult.scalars
        return list(self.tuples_iter(tuple=tuple))
        
    def scalar_set(self):
        return set(self.scalars_iter())

    def tuple_set(self):
        return set(self.tuples_iter(tuple=tuple))

    def dict(self, dict=dict):
        try:
            return self.dicts(dict=dict)[0]
        except IndexError:
            return None

    def tuple(self, tuple=tuple):
        try:
            return self.tuples(tuple=tuple)[0]
        except IndexError:
            return tuple(None for _ in range(len(self._proxied.keys())))
