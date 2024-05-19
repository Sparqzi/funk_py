from copy import deepcopy

import pytest

from t_support import cov, cov_counter
from funk_py.sorting.dict_manip import DictBuilder


# The following manages whether the generated coverage instance from t_support should report. This
# method of coverage is used so that coverage can be turned off to not interfere in timed tests.
@pytest.fixture(scope='session', autouse=True)
def c():
    cov_counter.value += 1

    yield cov

    cov_counter.value -= 1

    # We don't want to report till all test modules are completed...
    if not cov_counter.value:
        cov.stop()
        cov.save()
        cov.html_report()


T_KEY = 'g'
T_VAL = 42
K1 = 'k1'
K2 = 'k2'
K3 = 'k3'
K4 = 'k4'
K5 = 'k5'
K6 = 'k6'
K7 = 'k7'
K8 = 'k8'
KB = 'llama'
V1 = 95
V2 = 45
V3 = 3657
V4 = 3568
V5 = 32
V6 = 32105
V7 = 362
V8 = 21595187


@pytest.fixture(params=(
        (False, False),
        (True, False),
        (False, True),
        (True, True),
), ids=(
        'Neither map nor kwargs.',
        'Map only.',
        'Kwargs only.',
        'Map and kwargs.',
))
def instantiation_pattern(request):
    has_map, has_kwargs = request.param
    result = {}
    if has_map:
        _map = {'a': 1, 'b': 2, 'c': 3}
        result.update(_map)

    else:
        _map = ...

    if has_kwargs:
        kwargs = {'d': 4, 'e': 5, 'f': 6}
        result.update(kwargs)

    else:
        kwargs = {}

    return _map, kwargs, result


@pytest.fixture
def base_dict1():
    return {K1: V1, K2: V2}


@pytest.fixture
def base_dict2():
    return {K3: V3, K4: V4}


@pytest.fixture
def high_dict1(base_dict1):
    return {K3: V3, K4: base_dict1.copy()}


@pytest.fixture
def high_dict2(base_dict2):
    return {K5: V5, K6: base_dict2.copy()}


@pytest.fixture
def higher_dict1():
    return {K5: V5, K6: {K3: V3, K4: {K1: V1, K2: V2}}}


@pytest.fixture
def higher_dict2():
    return {K7: V7, K8: {K5: V5, K6: {K3: V3, K4: V4}}}


def instantiate(_map, kwargs) -> DictBuilder:
    if _map is ...:
        return DictBuilder(**kwargs)

    return DictBuilder(_map, **kwargs)


def test_can_instantiate(instantiation_pattern):
    testy = instantiate(*instantiation_pattern[:2])


def test_can_setitem(instantiation_pattern):
    testy = instantiate(*instantiation_pattern[:2])
    testy[T_KEY] = T_VAL
    result = instantiation_pattern[2]
    result[T_KEY] = T_VAL

    assert testy.build() == result


def test_can_getitem(base_dict1):
    testy = DictBuilder(base_dict1)
    assert testy[K1] == V1
    assert testy[K2] == V2


def test_can_get(base_dict1):
    testy = DictBuilder(base_dict1)
    assert testy.get(K1) == V1
    assert testy.get(K2) == V2


def test_can_get_missing(base_dict1):
    testy = DictBuilder(base_dict1)
    assert testy.get(KB) is None


def test_can_update(instantiation_pattern, base_dict1):
    testy = instantiate(*instantiation_pattern[:2])
    testy.update(base_dict1)
    result = instantiation_pattern[2]
    result.update(base_dict1)
    assert testy.build() == result


def test_can_update_from_other(instantiation_pattern, base_dict1):
    testy = instantiate(*instantiation_pattern[:2])
    testy.update_from_other(base_dict1)
    result = instantiation_pattern[2]
    result.update(base_dict1)
    assert testy.build() == result


def test_nested_can_update_from_nested_other(higher_dict1, higher_dict2):
    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1))
    result = deepcopy(higher_dict2)
    result.update(deepcopy(higher_dict1))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), K6)
    result = deepcopy(higher_dict2)
    result.update(deepcopy(higher_dict1[K6]))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), [K6, K4])
    result = deepcopy(higher_dict2)
    result.update(deepcopy(higher_dict1[K6][K4]))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), _as=K8)
    result = deepcopy(higher_dict2)
    result[K8].update(deepcopy(higher_dict1))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), K6, K8)
    result = deepcopy(higher_dict2)
    result[K8].update(deepcopy(higher_dict1[K6]))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), [K6, K4], K8)
    result = deepcopy(higher_dict2)
    result[K8].update(deepcopy(higher_dict1[K6][K4]))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), _as=[K8, K6])
    result = deepcopy(higher_dict2)
    result[K8][K6].update(deepcopy(higher_dict1))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), K6, [K8, K6])
    result = deepcopy(higher_dict2)
    result[K8][K6].update(deepcopy(higher_dict1[K6]))
    assert testy.build() == result

    testy = DictBuilder(deepcopy(higher_dict2))
    testy.update_from_other(deepcopy(higher_dict1), [K6, K4], [K8, K6])
    result = deepcopy(higher_dict2)
    result[K8][K6].update(deepcopy(higher_dict1[K6][K4]))
    assert testy.build() == result


TOP_LVL = 'top level'
TOP_LVL_LST = 'top level (list)'
NEW_TOP_LVL = 'new top level'
NEW_TOP_LVL_LST = 'new top level (list)'
NEW_1ST_2ND_LVL = 'new first and second level'
NEW_2ND_LVL = 'new second level'
SCND_LVL = 'second level'
THRD_LVL = 'third level'
NEW_1ST_2ND_3RD_LVL = 'new first, second, and third level'
NEW_2ND_3RD_LVL = 'new second and third level'
NEW_3RD_LVL = 'new third level'
REG_VAL = 'regular val'
DICT = 'dict'


def from_desc(lvl, _type):
    return f'from {lvl} - {_type} '


@pytest.fixture(params=(
        (K5, 1),
        ([K5], '1l'),
        (K6, 1),
        ([K6], '1l'),
        ([K6, K3], 2),
        ([K6, K4], 2),
        ([K6, K4, K1], 3),
), ids=(
        from_desc(TOP_LVL, REG_VAL),
        from_desc(TOP_LVL_LST, REG_VAL),
        from_desc(TOP_LVL, DICT),
        from_desc(TOP_LVL_LST, DICT),
        from_desc(SCND_LVL, REG_VAL),
        from_desc(SCND_LVL, DICT),
        from_desc(THRD_LVL, REG_VAL),
))
def froms(request):
    return request.param


def to_desc(lvl, _type=None):
    builder = f' to {lvl}'
    if _type is not None:
        builder += f' - {_type}'

    return builder


@pytest.fixture(params=(
        (K7, 1),
        ([K7], '1l'),
        (K8, 1),
        ([K8], '1l'),
        (K4, 1),
        ([K4], '1l'),
        ([K8, K5], 2),
        ([K8, K6], 2),
        ([K8, K4], 2),
        ([K4, K3], '2n'),
        ([K8, K6, K3], 3),
        ([K8, K6, K4], 3),
        ([K8, K6, K5], 3),
        ([K8, K4, K3], '3en'),
        ([K4, K3, K2], '3nn'),
), ids=(
        to_desc(TOP_LVL, REG_VAL),
        to_desc(TOP_LVL_LST, REG_VAL),
        to_desc(TOP_LVL, DICT),
        to_desc(TOP_LVL_LST, DICT),
        to_desc(NEW_TOP_LVL),
        to_desc(NEW_TOP_LVL_LST),
        to_desc(SCND_LVL, REG_VAL),
        to_desc(SCND_LVL, DICT),
        to_desc(NEW_2ND_LVL),
        to_desc(NEW_1ST_2ND_LVL),
        to_desc(THRD_LVL, REG_VAL),
        to_desc(THRD_LVL, DICT),
        to_desc(NEW_3RD_LVL),
        to_desc(NEW_2ND_3RD_LVL),
        to_desc(NEW_1ST_2ND_3RD_LVL),
))
def tos(request):
    return request.param


@pytest.fixture
def get_from_other_params(froms, tos, higher_dict1, higher_dict2):
    def copies():
        return deepcopy(higher_dict1), deepcopy(higher_dict2)

    def to_val_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2] = _from(d1, k1)
        return d2

    def to_list1_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]] = _from(d1, k1)
        return d2

    def to_list2_e_en_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]][k2[1]] = _from(d1, k1)
        return d2

    def to_list2_n_n_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]] = {k2[1]: _from(d1, k1)}
        return d2

    def to_list3_e_e_en_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]][k2[1]][k2[2]] = _from(d1, k1)
        return d2

    def to_list3_e_n_n_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]][k2[1]] = {k2[2]: _from(d1, k1)}
        return d2

    def to_list3_n_n_n_tuple(k1, k2, _from):
        d1, d2 = copies()
        d2[k2[0]] = {k2[1]: {k2[2]: _from(d1, k1)}}
        return d2

    def from_val(d1, k1):
        return d1[k1]

    def from_list1(d1, k1):
        return d1[k1[0]]

    def from_list2(d1, k1):
        return d1[k1[0]][k1[1]]

    def from_list3(d1, k1):
        return d1[k1[0]][k1[1]][k1[2]]

    from_lookup = {
        1: from_val,
        '1l': from_list1,
        2: from_list2,
        3: from_list3,
    }
    to_lookup = {
        1: to_val_tuple,
        '1l': to_list1_tuple,
        2: to_list2_e_en_tuple,
        '2n': to_list2_n_n_tuple,
        3: to_list3_e_e_en_tuple,
        '3en': to_list3_e_n_n_tuple,
        '3nn': to_list3_n_n_n_tuple,
    }

    k1, _from = froms
    k2, to = tos
    result = to_lookup[to](k1, k2, from_lookup[_from])
    return k1, k2, result


def test_get_from_other(get_from_other_params, higher_dict1, higher_dict2):
    testy = DictBuilder(higher_dict2)
    testy.get_from_other(higher_dict1, get_from_other_params[0], get_from_other_params[1])
    assert testy.build() == get_from_other_params[2]


@pytest.fixture(params=(
        ((KB,),(K6,)),
        ((), (K6,)),
        (([K6, K5],), (K7,)),
        ((KB, [K6, K7], K8), ()),
), ids=(
        'bad key before, good key after',
        'no key before, good key after',
        'partly-good key before, bad key after',
        'bad keys and partly good key before, no key after',
))
def get_one_key_params(request, get_from_other_params):
    before, after = request.param
    return (*before, get_from_other_params[0], *after), *get_from_other_params[1:]


def test_get_one_key_from_other(get_one_key_params, higher_dict1, higher_dict2):
    testy = DictBuilder(higher_dict2)
    testy.get_one_of_keys_from_other(higher_dict1, get_one_key_params[1], *get_one_key_params[0])
    assert testy.build() == get_one_key_params[2]
