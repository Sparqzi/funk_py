import math
import sys
from typing import (Any, List, Tuple, Set, Mapping, Dict, Iterable, Union, Literal, Sequence,
                    MutableMapping, AnyStr, Callable, Optional)

import pytest

from funk_py.modularity.type_matching import (TypeMatcher as TM, StrictTypeMatcher as STM,
                                              IterableNonString)


class TCL:
    def __init__(self):
        self.value = 0


STRINGS = ('a', 'b', 'c', 'd', 'e', 'f', 'g')
INTS = (3, 4, 5, 6, 7, 8, 9)
FLOATS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
BYTES = (b'a', b'b', b'c', b'd', b'e', b'f', b'g')
BOOLS = (True, False, True, False, True, False, True)
BAD_INTS = (0, 1)
COMPLEXES = tuple(complex(a, b) for a, b in zip(INTS, FLOATS))
OBJECTS = (object(), object(), object(), object(), object(), object(), object())

LIST_SETS = (STRINGS, INTS, FLOATS, BYTES, BOOLS, COMPLEXES, OBJECTS)

BASE_TYPES = (str, int, float, bytes, bool, complex, object)
BASE_VALS = ('llama', 53, 57.65, b'llama', True, complex(1, 5), object())
BASE_NAMES = ('string', 'integer', 'float', 'bytes', 'bool', 'complex', 'object')

STRICT = 'strict'
NORM = 'normal'
GOOD = 'good'
BAD = 'bad'
STM_NAME = 'StrictTypeMatcher'
TM_NAME = 'TypeMatcher'


# --------------------------------------------------------------------------------------------------
# Basic Typing Checks
# --------------------------------------------------------------------------------------------------
def test_generates_matcher_of_type_matcher(): TM(TM)


def test_generates_matcher_of_strict_type_matcher(): TM(STM)


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_handles_parametrized_type():
    TM[int]
    TM[str]
    TM[bool]
    TM[complex]
    TM[float]
    TM[str | float | int]


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason='Test is not needed for Python 3.10 or higher. Reserved for 3.9 and below.'
)
def test_handles_parametrized_type():
    TM[int]
    TM[str]
    TM[bool]
    TM[complex]
    TM[float]


def test_generates_strict_matcher_of_type_matcher(): STM(TM)


def test_generates_strict_matcher_of_strict_type_matcher(): STM(STM)


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_handles_strict_parameterized_type():
    STM[int]
    STM[str]
    STM[bool]
    STM[complex]
    STM[float]
    STM[str | float | int]


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason='Test is not needed for Python 3.10 or higher. Reserved for 3.9 and below.'
)
def test_handles_strict_parameterized_type():
    STM[int]
    STM[str]
    STM[bool]
    STM[complex]
    STM[float]


@pytest.fixture(params=(TM, STM), ids=('regular type matcher', 'strict type matcher'))
def matchers(request): return request.param


@pytest.fixture(
    params=(TM, STM), ids=('of regular type matcher', 'of strict type matcher')
)
def matchers_of_matchers(request, matchers): return request.param, matchers


# --------------------------------------------------------------------------------------------------
# Basic Value Tests
# --------------------------------------------------------------------------------------------------
@pytest.fixture(params=tuple(zip(BASE_TYPES, BASE_VALS)), ids=BASE_NAMES)
def basic_vals(request): return request.param


def test_generates_basic_matchers(basic_vals): TM(basic_vals[0])


def test_generates_matchers_of_basic_matchers(basic_vals, matchers_of_matchers):
    matchers_of_matchers[1](matchers_of_matchers[0][basic_vals[0]])


def generate_basic_matcher_from_spec(blueprint: tuple) -> TM:
    m1, m2, *t = blueprint
    if len(t) > 1:
        t_ = t[-1]
        for i in range(len(t) - 2, -1, -1):
            t_ = t[i][t_]

    else:
        t_ = t[0]

    if m2 is None:
        return m1(t_)

    return m1(m2[t_])


# generate_base_name_from_spec
def gbnfs(m1: type, m2: Optional[type], *n) -> str:
    """
    Generates the name for a matcher of a matcher.
    
    :param m1: The outer matcher type.
    :param m2: The inner matcher type. If omitted, that name will just be "``outer_matcher_type`` of
        ``inner_type``".
    :param n: The inner type of the matcher. If a single type is provided, the name will be
        "``outer_matcher_type`` of [``inner_matcher_type`` of ]``inner_type``". If two types -
        specifically a parameterizable type and another type - are provided, the name will be
        "``outer_matcher_type`` of [``inner_matcher_type`` of ]``inner_param_type`` of
        ``inner_type``".
    """
    builder = (TM_NAME if m1 is TM else STM_NAME) + ' of '
    if m2 is not None:
        builder += (TM_NAME if m2 is TM else STM_NAME) + ' of '

    for n_ in n[:-1]:
        builder += n_ + ' of '

    builder += n[-1]
    return builder


def basic_checker_map():
    builder1 = {}
    builder2 = set()
    b1 = False
    for t1 in BASE_TYPES:
        for t2, n2 in zip(BASE_TYPES, BASE_NAMES):
            if t1 is t2:
                builder1.update({
                    (STM, None, t2, t1): True,
                    (TM, STM, t2, t1): True,
                    (STM, STM, t2, t1): True,
                    (TM, None, t2, t1): True,
                    (TM, TM, t2, t1): True,
                    (STM, TM, t2, t1): True
                })

            elif issubclass(t1, t2) and not (t1 is bool and t2 is int):
                builder1.update({
                    (STM, None, t2, t1): False,
                    (TM, STM, t2, t1): False,
                    (STM, STM, t2, t1): False,
                    (TM, None, t2, t1): True,
                    (TM, TM, t2, t1): True,
                    (STM, TM, t2, t1): True
                })

            else:
                builder1.update({
                    (STM, None, t2, t1): False,
                    (TM, STM, t2, t1): False,
                    (STM, STM, t2, t1): False,
                    (TM, None, t2, t1): False,
                    (TM, TM, t2, t1): False,
                    (STM, TM, t2, t1): False
                })

            if not b1:
                builder2.update({
                    (STM, None, t2, gbnfs(STM, None, n2)),
                    (TM, STM, t2, gbnfs(TM, STM, n2)),
                    (STM, STM, t2, gbnfs(STM, STM, n2)),
                    (TM, None, t2, gbnfs(TM, None, n2)),
                    (TM, TM, t2, gbnfs(TM, TM, n2)),
                    (STM, TM, t2, gbnfs(STM, TM, n2))
                })

        # Building of checker defs should be done after first pass. Set this to make sure they don't
        # continue re-building.
        b1 = True

    return builder1, builder2


BASIC_CHECKER_MAP, BASIC_CHECKER_DEFS = basic_checker_map()


@pytest.fixture(
    params=tuple(t[:-1] for t in BASIC_CHECKER_DEFS),
    ids=tuple(t[-1] for t in BASIC_CHECKER_DEFS)
)
def basic_type_matchers(request):
    return generate_basic_matcher_from_spec(request.param), *request.param


SHOULDA_PASSED = "A value didn't pass a TypeMatcher when it was expected to.\n"
SHOULDNA_PASSED = 'A value passed a TypeMatcher when it was expected not to.\n'


def test_basic_types(basic_vals, basic_type_matchers):
    t1, val = basic_vals
    matcher, *def_ = basic_type_matchers
    def_ = (*def_, t1)
    assert matcher(val) == BASIC_CHECKER_MAP[def_]


# --------------------------------------------------------------------------------------------------
# List and Set Tests
# --------------------------------------------------------------------------------------------------
LIST_TYPES = (list, List, set, Set)
LIST_TYPES_NOT_FOR_3_8 = (list, set)
LIST_BUILDERS = (list, list, set, set)
LIST_NAMES = ('list', 'major-list', 'set', 'major-set')
LIST_NAMES_3_8 = ('major-list', 'major-set')
S_LIST_BUILDERS = (list, set)
S_LIST_NAMES = ('list', 'set')


@pytest.fixture(params=tuple(zip(LIST_TYPES, LIST_BUILDERS)), ids=LIST_NAMES)
def basic_list_types_all(request): return request.param


@pytest.fixture(params=tuple(zip(LIST_TYPES, LIST_BUILDERS)), ids=LIST_NAMES)
def basic_list_types(request):
    if sys.version_info < (3, 9) and request.param[0] in LIST_TYPES_NOT_FOR_3_8:
        pytest.skip('This list type cannot be parameterized in the current Python version.')

    return request.param


def test_generates_simple_list_types(basic_list_types_all, matchers):
    matchers(basic_list_types_all[0])


def test_generates_matchers_of_simple_list_type_matchers(
        basic_list_types_all,
        matchers_of_matchers
):
    m2, m1 = matchers_of_matchers
    m1(m2[basic_list_types_all[0]])


@pytest.fixture(params=tuple(zip(BASE_TYPES, LIST_SETS)), ids=BASE_NAMES)
def basic_list_vals(request): return request.param


@pytest.fixture(params=S_LIST_BUILDERS, ids=S_LIST_NAMES)
def basic_lists(request, basic_list_vals):
    conv = request.param
    return conv, basic_list_vals[0], conv(basic_list_vals[1])


def basic_list_checkers():
    builder1 = {}
    builder2 = set()
    for lt, lb, ln in zip(LIST_TYPES, LIST_BUILDERS, LIST_NAMES):
        builder1.update({
            (TM, None, lt): lb,
            (TM, TM, lt): lb,
            (TM, STM, lt): lb,
            (STM, None, lt): lb,
            (STM, TM, lt): lb,
            (STM, STM, lt): lb
        })
        builder2.update({
            (TM, None, lt, gbnfs(TM, None, ln)),
            (TM, TM, lt, gbnfs(TM, TM, ln)),
            (TM, STM, lt, gbnfs(TM, STM, ln)),
            (STM, None, lt, gbnfs(STM, None, ln)),
            (STM, TM, lt, gbnfs(STM, TM, ln)),
            (STM, STM, lt, gbnfs(STM, STM, ln))
        })

    return builder1, builder2


BASIC_LIST_CHECKER_MAP, BASIC_LIST_CHECKER_DEFS = basic_list_checkers()


@pytest.fixture(
    params=tuple(t[:-1] for t in BASIC_LIST_CHECKER_DEFS),
    ids=tuple(t[-1] for t in BASIC_LIST_CHECKER_DEFS)
)
def basic_list_type_matchers(request):
    return generate_basic_matcher_from_spec(request.param), *request.param


def test_simple_list_types(basic_lists, basic_list_type_matchers):
    lb, _, val = basic_lists
    matcher, *def_ = basic_list_type_matchers
    assert matcher(val) == (BASIC_LIST_CHECKER_MAP[tuple(def_)] is lb)


@pytest.fixture
def spec_list_types(basic_list_types, basic_list_vals):
    return (basic_list_types[0], basic_list_vals[0], basic_list_types[1],
            basic_list_types[1](basic_list_vals[1]))


def test_generates_spec_list_types(spec_list_types, matchers):
    matchers(spec_list_types[0][spec_list_types[1]])


def test_generates_matchers_of_spec_list_type_matchers(spec_list_types, matchers_of_matchers):
    m2, m1 = matchers_of_matchers
    m1(m2[spec_list_types[0][spec_list_types[1]]])


def spec_list_checkers():
    # This function generates a list of special list checkers following appropriate rules.
    builder1 = {}
    builder2 = set()
    type1_done = False
    for type1 in BASE_TYPES:
        for type2, num2 in zip(BASE_TYPES, BASE_NAMES):
            for list_builder1 in S_LIST_BUILDERS:
                for list_builder2, list_type, list_name \
                        in zip(LIST_BUILDERS, LIST_TYPES, LIST_NAMES):
                    if not type1_done:
                        # Only run this section for the first BASE_TYPE.
                        # The purpose of this section is to generate the actual TypeMatcher
                        # definitions.
                        builder2.update({
                            (TM, None, list_type, type2, gbnfs(TM, None, list_name, num2)),
                            (STM, None, list_type, type2, gbnfs(STM, None, list_name, num2))
                        })

                    # The rest is here to ensure that the right test definitions are added.
                    if list_builder1 is list_builder2:
                        if type1 is type2:
                            # When the builders match, the result of a comparison is generally going
                            # to be True.
                            builder1.update({
                                (TM, None, list_type, type2, type1, list_builder2): True,
                                (STM, None, list_type, type2, type1, list_builder2): True
                            })
                            continue

                        elif issubclass(type1, type2) and not (type1 is bool and type2 is int):
                            # StrictTypeMatcher sees bool as a non-integer, so it will compare as
                            # false, though TypeMatcher will compare as True.
                            builder1.update({
                                (TM, None, list_type, type2, type1, list_builder2): True,
                                (STM, None, list_type, type2, type1, list_builder2): False
                            })
                            continue

                    # When the builders don't match, both TypeMatcher and StrictTypeMatcher will
                    # compare False.
                    builder1.update({
                        (TM, None, list_type, type2, type1, list_builder1): False,
                        (STM, None, list_type, type2, type1, list_builder1): False
                    })

        type1_done = True

    return builder1, builder2


SPEC_LIST_CHECKER_MAP, SPEC_LIST_CHECKER_DEFS = spec_list_checkers()


@pytest.fixture(
    params=tuple(t[:-1] for t in SPEC_LIST_CHECKER_DEFS),
    ids=tuple(t[-1] for t in SPEC_LIST_CHECKER_DEFS),
)
def spec_list_type_matchers(request):
    _, _, list_type, *_ = request.param
    if sys.version_info < (3, 9) and list_type in LIST_TYPES_NOT_FOR_3_8:
        pytest.skip('This list type cannot be parameterized in the current Python version.')

    return generate_basic_matcher_from_spec(request.param), *request.param


def test_spec_list_types(spec_list_types, spec_list_type_matchers):
    _, lt, lb, val = spec_list_types
    matcher, *def_ = spec_list_type_matchers
    def_ = (*def_, lt, lb)
    assert matcher(val) == SPEC_LIST_CHECKER_MAP[def_]


# --------------------------------------------------------------------------------------------------
# Dictionary Tests
# --------------------------------------------------------------------------------------------------
DICT_TYPES = (dict, Dict, Mapping, MutableMapping)
DICT_TYPES_NOT_FOR_3_8 = (dict,)
DICT_TYPES_3_8 = (Dict, Mapping, MutableMapping)
DICT_BUILDER = dict
DICT_NAMES = ('dictionary', 'major-dictionary', 'major-mapping', 'major-mutableMapping')
DICT_NAMES_3_8 = ('major-dictionary', 'major-mapping', 'major-mutableMapping')


@pytest.fixture(params=DICT_TYPES, ids=DICT_NAMES)
def basic_dict_types(request): return request.param


def test_generates_simple_dict_types(basic_dict_types, matchers): matchers(basic_dict_types)


def test_generates_matchers_of_simple_dict_type_matchers(basic_dict_types, matchers_of_matchers):
    m2, m1 = matchers_of_matchers
    m1(m2[basic_dict_types])


@pytest.fixture(params=tuple(zip(BASE_TYPES, LIST_SETS)), ids=tuple('key:' + k for k in BASE_NAMES))
def dict_keys(request): return request.param


@pytest.fixture(params=tuple(zip(BASE_TYPES, LIST_SETS)), ids=tuple('val:' + k for k in BASE_NAMES))
def dict_vals(request): return request.param


@pytest.fixture
def dicts(dict_keys, dict_vals):
    return (dict_keys[0], dict_vals[0], DICT_BUILDER(zip(dict_keys[1], dict_vals[1])))


def basic_dict_checkers():
    builder1 = {}
    builder2 = set()
    for d, n in zip(DICT_TYPES, DICT_NAMES):
        if d in (dict, Dict):
            builder1.update({
                (TM, None, d): True,
                (STM, None, d): True
            })

        else:
            builder1.update({
                (TM, None, d): True,
                (STM, None, d): False
            })

        builder2.update({
            (TM, None, d, gbnfs(TM, None, n)),
            (STM, None, d, gbnfs(STM, None, n))
        })

    return builder1, builder2


BASIC_DICT_CHECKER_MAP, BASIC_DICT_CHECKER_DEFS = basic_dict_checkers()


@pytest.fixture(
    params=tuple(t[:-1] for t in BASIC_DICT_CHECKER_DEFS),
    ids=tuple(t[-1] for t in BASIC_DICT_CHECKER_DEFS)
)
def basic_dict_type_matchers(request):
    return generate_basic_matcher_from_spec(request.param), *request.param


def test_simple_dict_types(dicts, basic_dict_type_matchers):
    matcher, *def_  = basic_dict_type_matchers
    assert matcher(dicts[-1]) == BASIC_DICT_CHECKER_MAP[tuple(def_)]


def generate_dict_matcher(blueprint: tuple) -> TM:
    m, dt, mk, k, mv, v = blueprint
    if mk is not None:
        k = mk[k]

    if mv is not None:
        v = mv[v]

    return m(dt[k, v])


def gdnfs(m: type, dn: str, m1: Optional[str], k: str, m2: Optional[str], v: str) -> str:
    builder = (TM_NAME if m is TM else STM_NAME) + ' of '
    builder += dn + ' of keys ('
    if m1 is not None:
        builder += m1 + ' of '

    builder += k + ') and vals ('
    if m2 is not None:
        builder += m2 + ' of '

    builder += v + ')'
    return builder


def cd(dt, kt1, kt2, vt1, vt2):
    """
    Create a function which generates a small dictionary of test definitions based off of provided
    values.

    :param dt: The type of the dictionary.
    :param kt1: Key type that matcher should be testing.
    :param kt2: Key type that matcher should be for.
    :param vt1: Value type that matcher should be testing.
    :param vt2: Value type that matcher should be for.
    """
    def key(ptm, pstm, tmkstm, tmvstm, stmktm, stmvtm):
        """
        Generates a small dictionary of test definitions for dictionaries of specific typing
        with the given results.

        :param ptm: The expected result of using a plain ``TypeMatcher`` of a dictionary.
        :param pstm: The expected result of using a plain ``StrictTypeMatcher`` of a dictionary.
        :param tmkstm: The expected result of using a ``TypeMatcher`` of a dictionary having a key
            type of ``StrictTypeMatcher``.
        :param tmvstm: The expected result of using a ``TypeMatcher`` of a dictionary having a value
            type of ``StrictTypeMatcher``.
        :param stmktm: The expected result of using a ``StrictTypeMatcher`` of a dictionary having a
            key type of ``TypeMatcher``.
        :param stmvtm: he expected result of using a ``StrictTypeMatcher`` of a dictionary having a
            value type of ``TypeMatcher``.
        """
        return {
            (TM, dt, None, kt2, None, vt2, kt1, vt1): ptm,
            (STM, dt, None, kt2, None, vt2, kt1, vt1): pstm,
            (TM, dt, STM, kt2, None, vt2, kt1, vt1): tmkstm,
            (TM, dt, None, kt2, STM, vt2, kt1, vt1): tmvstm,
            (STM, dt, TM, kt2, None, vt2, kt1, vt1): stmktm,
            (STM, dt, None, kt2, TM, vt2, kt1, vt1): stmvtm
        }

    return key


def spec_dict_checkers(dict_types: tuple, dict_names: tuple):
    # This function generates a list of special dictionary checkers following appropriate rules.
    builder1 = {}
    builder2 = set()
    key_type1_done = False
    for key_type1 in BASE_TYPES:
        for key_type2, key_name2 in zip(BASE_TYPES, BASE_NAMES):
            for value_type1 in BASE_TYPES:
                for value_type2, value_name2 in zip(BASE_TYPES, BASE_NAMES):
                    for dict_type, dict_name in zip(dict_types, dict_names):
                        if not key_type1_done:
                            # Only run this section for the first BASE_TYPE.
                            # The purpose of this section is to generate the actual TypeMatcher
                            # definitions.
                            builder2.update({
                                (TM, dict_type, None, key_type2, None, value_type2,
                                 gdnfs(TM, dict_name, None, key_name2, None, value_name2)),
                                (STM, dict_type, None, key_type2, None, value_type2,
                                 gdnfs(STM, dict_name, None, key_name2, None, value_name2)),
                                (TM, dict_type, STM, key_type2, None, value_type2,
                                 gdnfs(TM, dict_name, STM_NAME, key_name2, None, value_name2)),
                                (TM, dict_type, None, key_type2, STM, value_type2,
                                 gdnfs(TM, dict_name, None, key_name2, STM_NAME, value_name2)),
                                (STM, dict_type, TM, key_type2, None, value_type2,
                                 gdnfs(TM, dict_name, TM_NAME, key_name2, None, value_name2)),
                                (STM, dict_type, None, key_type2, TM, value_type2,
                                 gdnfs(TM, dict_name, None, key_name2, TM_NAME, value_name2))
                            })

                        # The rest is here to ensure that the right test definitions are added.
                        # _cd will be used to generate subsections of the dictionary test
                        # definitions.
                        _cd = cd(dict_type, key_type1, key_type2, value_type1, value_type2)
                        if dict_type in (dict, Dict):
                            # If type of the matcher is actually one of the dictionary types, tests
                            # are simpler to design.
                            if key_type1 is key_type2:
                                if value_type1 is value_type2:
                                    # When key types match and value types match, all cases should
                                    # generally pass.
                                    builder1.update(_cd(True, True, True, True, True, True))
                                    continue

                                elif (issubclass(value_type1, value_type2)
                                      and not (value_type1 is bool and value_type2 is int)):
                                    # When key types match, but the value type to test is boolean
                                    # and the value type of the matcher is integer, only tests not
                                    # involving a StrictTypeMatcher around the value type should
                                    # pass.
                                    builder1.update(_cd(True, False, True, False, False, True))
                                    continue

                            elif (issubclass(key_type1, key_type2)
                                  and not (key_type1 is bool and key_type2 is int)):
                                if value_type1 is value_type2:
                                    # When the key type to test is boolean and the key type of the
                                    # matcher is integer, and the value types match, only tests not
                                    # involving a StrictTypeMatcher around the key type should
                                    # pass.
                                    builder1.update(_cd(True, False, False, True, True, False))
                                    continue

                                elif (issubclass(value_type1, value_type2)
                                      and not (value_type1 is bool and value_type2 is int)):
                                    # When the key type to test is boolean and the key type of the
                                    # matcher is integer, and the value type to test is boolean and
                                    # the value type of the matcher is integer, only tests not
                                    # involving a StrictTypeMatcher at all should pass.
                                    builder1.update(_cd(True, False, False, False, False, False))
                                    continue

                        # The rest below this is to generate tests for Mapping as the TypeMatcher
                        # type.
                        elif key_type1 is key_type2:
                            if value_type1 is value_type2:
                                # When key types match and value types match, everything where
                                # StrictTypeMatcher is not the outermost should pass.
                                builder1.update(_cd(True, False, True, True, False, False))
                                continue

                            elif (issubclass(value_type1, value_type2)
                                  and not (value_type1 is bool and value_type2 is int)):
                                # When key types match, but the value type to test is boolean and
                                # the value type of the matcher is integer, everything involving a
                                # StrictTypeMatcher containing the value should pass.
                                builder1.update(_cd(True, False, True, False, False, False))
                                continue

                        elif (issubclass(key_type1, key_type2)
                              and not (key_type1 is bool and key_type2 is int)):
                            # When the key type to test is boolean and the key type of the
                            # matcher is integer, and the value types match, only tests not
                            # involving a StrictTypeMatcher around the key type should
                            # pass.
                            if value_type1 is value_type2:
                                builder1.update(_cd(True, False, False, True, False, False))
                                continue

                            elif (issubclass(value_type1, value_type2)
                                  and not (value_type1 is bool and value_type2 is int)):
                                # When the key type to test is boolean and the key type of the
                                # matcher is integer, and the value type to test is boolean and
                                # the value type of the matcher is integer, only tests not
                                # involving a StrictTypeMatcher at all should pass.
                                builder1.update(_cd(True, False, False, False, False, False))
                                continue

                        # When no previous conditions were met, every test should fail.
                        builder1.update(_cd(False, False, False, False, False, False))

        key_type1_done = True

    return builder1, builder2


SPEC_DICT_CHECKER_MAP, SPEC_DICT_CHECKER_DEFS = spec_dict_checkers(DICT_TYPES, DICT_NAMES)
SPEC_DICT_CHECKER_MAP_3_8, SPEC_DICT_CHECKER_DEFS_3_8 = \
    spec_dict_checkers(DICT_TYPES_3_8, DICT_NAMES_3_8)


@pytest.fixture(
    params=tuple(t[:-1] for t in SPEC_DICT_CHECKER_DEFS),
    ids=tuple(t[-1] for t in SPEC_DICT_CHECKER_DEFS)
)
def spec_dict_type_matchers(request):
    _, dict_type, *_ = request.param
    if sys.version_info < (3, 9) and dict_type in DICT_TYPES_NOT_FOR_3_8:
        pytest.skip('This dict type cannot be parameterized in the current Python version.')

    return generate_dict_matcher(request.param), *request.param


def test_spec_dict_types(dicts, spec_dict_type_matchers):
    kt, vt, val = dicts
    matcher, *def_ = spec_dict_type_matchers
    def_ = (*def_, kt, vt)
    assert matcher(val) == SPEC_DICT_CHECKER_MAP[def_]


# --------------------------------------------------------------------------------------------------
# Tuple Tests
# --------------------------------------------------------------------------------------------------
TUPLE_TYPES = (tuple, Tuple)
TUPLE_TYPES_NOT_FOR_3_8 = (tuple,)  # These types are ones that break when parameterized in
                                    # Python 3.8.
TUPLE_TYPES_3_8 = (Tuple,)  # make a tuple both for interchangeability and for potential noticed
                            # missed edge cases.
TUPLE_NAMES = ('tuple', 'major-tuple')
TUPLE_NAMES_3_8 = ('major-tuple',)  # make a tuple both for interchangeability and for potential
                                    # noticed missed edge cases.
TUPLE_BUILDER = tuple


@pytest.fixture(params=TUPLE_TYPES, ids=TUPLE_NAMES)
def basic_tuple_types_all(request): return request.param


@pytest.fixture(params=TUPLE_TYPES, ids=TUPLE_NAMES)
def basic_tuple_types(request):
    if sys.version_info < (3, 9) and request.param in TUPLE_TYPES_NOT_FOR_3_8:
        pytest.skip('This tuple type cannot be parameterized in the current Python version.')

    return request.param


def test_generate_simple_tuple_types(basic_tuple_types_all): TM(basic_tuple_types_all)


def test_generate_matchers_of_simple_tuple_type_matchers(basic_tuple_types_all):
    TM(TM[basic_tuple_types_all])


@pytest.fixture(params=tuple(zip(BASE_TYPES, LIST_SETS)), ids=BASE_NAMES)
def tuples(request):
    t, val = request.param
    return t, TUPLE_BUILDER(val)


@pytest.fixture
def tuple_checkers(): return [TM(t) for t in TUPLE_TYPES] + [TM(TM[t]) for t in TUPLE_TYPES]


def test_simple_tuple_types(tuples, tuple_checkers):
    t, val = tuples
    for checker in tuple_checkers:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'type: {t}\n'
                              f'checker: {checker}\n'
                              f'value: {repr(val)}')


@pytest.fixture
def spec_tuple_types(tuples, basic_tuple_types): return basic_tuple_types, tuples[0], tuples[1]


def test_generate_spec_tuple_types(spec_tuple_types):
    tt, it, _ = spec_tuple_types
    TM(tt[it])
    TM(TM[tt[it]])
    TM(tt[it, ...])
    TM(TM[tt[it, ...]])
    # Cannot test form TM(tt[it, it, ...]) here since Tuple is tested, and Tuple is stricter about
    # ellipsis in tuple beyond index 1.
    TM(tt[it, it, it, it, it, it, it])
    TM(TM[tt[it, it, it, it, it, it, it]])


@pytest.fixture
def spec_tuple_checkers():
    builder = {}
    for t1 in BASE_TYPES:
        builder[t1] = _builder = {GOOD: [], BAD:[]}
        for t2 in BASE_TYPES:
            for tt in TUPLE_TYPES:
                if not (sys.version_info < (3, 9) and tt in TUPLE_TYPES_NOT_FOR_3_8):
                    if t1 is t2 or (issubclass(t1, t2) and not (t1 is bool and t2 is int)):
                        _builder[GOOD].extend([TM(tt[t2, ...]),
                                               TM(tt[t2, t2, t2, t2, t2, t2, t2]),
                                               TM(TM[tt[t2, ...]]),
                                               TM(TM[tt[t2, t2, t2, t2, t2, t2, t2]])])

                    else:
                        _builder[BAD].extend([TM(tt[t2, ...]),
                                              TM(tt[t2, t2, t2, t2, t2, t2, t2]),
                                              TM(TM[tt[t2, ...]]),
                                              TM(TM[tt[t2, t2, t2, t2, t2, t2, t2]])])

                    _builder[BAD].extend([TM(tt[t2]), TM(TM[tt[t2]])])

    return builder


def test_spec_tuple_types(spec_tuple_types, spec_tuple_checkers):
    tt, t, val = spec_tuple_types
    checkers = spec_tuple_checkers[t]
    for checker in checkers[GOOD]:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(val)}')

    for checker in checkers[BAD]:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(val)}')


@pytest.fixture
def newer_spec_tuple_checkers():
    builder = {}
    for t1 in BASE_TYPES:
        for t2 in BASE_TYPES:
            if t1 is t2 or issubclass(t1, t2):
                builder[t1] = [TM(TUPLE_BUILDER[t2, t2, ...]), TM(TM[TUPLE_BUILDER[t2, t2, ...]])]

    return builder


@pytest.mark.skipif(sys.version_info < (3, 9), reason='Test requires Python 3.9 or higher.')
def test_newer_spec_tuple_types(spec_tuple_types, newer_spec_tuple_checkers):
    tt, t, val = spec_tuple_types
    for checker in newer_spec_tuple_checkers[t]:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(val)}')


@pytest.fixture(params=(False, True), ids=('regular matcher', 'matcher of matcher'))
def match_types(request): return request.param


@pytest.fixture
def single_string_tuple(match_types):
    return TM(TM[Tuple[str]]) if match_types else TM(Tuple[str]), {
        GOOD: [
            (STRINGS[0],),
            (STRINGS[1],)
        ],
        BAD: [
            (INTS[0],),
            tuple(STRINGS[:2]),
        ]
    }


@pytest.fixture
def zero_element_tuple(match_types):
    return TM(TM[tuple[()]]) if match_types else TM(tuple[()]), {
        GOOD: [
            ()
        ],
        BAD: [
            (STRINGS[0],),
            (INTS[0],)
        ]
    }


@pytest.fixture
def one_type_any_length_tuple(match_types):
    builder = {GOOD: []}
    for i in range(1, len(STRINGS)):
        builder[GOOD].append(tuple(STRINGS[:i]))

    builder[GOOD].append(())

    builder[BAD] = [
        tuple(INTS),
        (INTS[0],)
    ]

    return TM(TM[Tuple[str, ...]]) if match_types else TM(Tuple[str, ...]), builder


@pytest.fixture
def even_count_string_only_tuple(match_types):
    return TM(TM[tuple[str, str, ...]]) if match_types else TM(tuple[str, str, ...]), {
        GOOD: [
            tuple(STRINGS[:2]),
            tuple(STRINGS[:4]),
            tuple(STRINGS[:6]),
            ()
        ],
        BAD: [
            (STRINGS[0],),
            tuple(STRINGS[:3]),
            tuple(STRINGS[:5])
        ]
    }


@pytest.fixture
def one_int_and_one_string_tuple(match_types):
    return TM(TM[Tuple[int, str]]) if match_types else TM(Tuple[int, str]), {
        GOOD: [
            (INTS[0], STRINGS[0]),
            (INTS[1], STRINGS[1])
        ],
        BAD: [
            tuple(INTS[:2]),
            tuple(STRINGS[:2]),
            (STRINGS[0], INTS[0]),
            (INTS[0], STRINGS[0], INTS[1]),
            (INTS[0], STRINGS[0], STRINGS[1]),
            (INTS[0], STRINGS[0], INTS[1], STRINGS[1])
        ]
    }


@pytest.fixture
def int_string_pair_tuple(match_types):
    return TM(TM[tuple[int, str, ...]]) if match_types else TM(tuple[int, str, ...]), {
        GOOD: [
            (INTS[0], STRINGS[0]),
            (INTS[0], STRINGS[0], INTS[1], STRINGS[1])
        ],
        BAD: [
            tuple(INTS[:2]),
            tuple(STRINGS[:2]),
            (STRINGS[0], INTS[0]),
            (INTS[0], STRINGS[0], INTS[1]),
            (INTS[0], STRINGS[0], STRINGS[1])
        ]
    }


def t_vals(matcher, vals):
    for val in vals[GOOD]:
        assert matcher(val), (f'{SHOULDA_PASSED}'
                              f'checker: {matcher}\n'
                              f'value: {repr(val)}')

    for val in vals[BAD]:
        assert not matcher(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {matcher}\n'
                                  f'value: {repr(val)}')

def test_single_string_tuple_cases(single_string_tuple): t_vals(*single_string_tuple)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='Test requires Python 3.9 or higher.')
def test_zero_element_tuple_cases(zero_element_tuple): t_vals(*zero_element_tuple)


def test_one_type_any_length_tuple_cases(one_type_any_length_tuple):
    t_vals(*one_type_any_length_tuple)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='Test requires Python 3.9 or higher.')
def test_even_count_string_only_tuple_cases(even_count_string_only_tuple):
    t_vals(*even_count_string_only_tuple)


def test_one_int_and_one_string_tuple_cases(one_int_and_one_string_tuple):
    t_vals(*one_int_and_one_string_tuple)


@pytest.mark.skipif(sys.version_info < (3, 9), reason='Test requires Python 3.9 or higher.')
def test_int_string_pair_tuple_cases(int_string_pair_tuple): t_vals(*int_string_pair_tuple)


# --------------------------------------------------------------------------------------------------
# General Iterable Tests
# --------------------------------------------------------------------------------------------------
@pytest.fixture
def i_lists(basic_list_vals): return basic_list_vals[0], list(basic_list_vals[1])


@pytest.fixture
def i_dicts(dicts): return dicts[0], dicts[-1]


@pytest.fixture
def i_strs(): return str, ''.join(STRINGS)


@pytest.fixture
def i_tuples(tuples): return tuples


@pytest.fixture
def i_bytes(): return bytes, b''.join(BYTES)


@pytest.fixture
def i_sets(basic_list_vals): return basic_list_vals[0], set(basic_list_vals[1])


@pytest.fixture(params=BASE_TYPES, ids=BASE_NAMES)
def base_types(request): return request.param


def test_generate_simple_iterable_type(): TM(Iterable)


def test_generate_matcher_of_simple_iterable_type_matcher(): TM(TM[Iterable])


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_lists'), pytest.lazy_fixture('i_dicts'),
                          pytest.lazy_fixture('i_strs'), pytest.lazy_fixture('i_tuples'),
                          pytest.lazy_fixture('i_bytes'), pytest.lazy_fixture('i_sets')))
def test_simple_iterable_types(situation, match_types):
    checker = TM(TM[Iterable]) if match_types else TM(Iterable)
    assert checker((situation[1])), (f'{SHOULDA_PASSED}'
                                     f'checker: {checker}\n'
                                     f'value: {repr(situation[0])}')


def test_generate_iterable_non_string_type(): TM(IterableNonString)


def test_generate_matcher_of_iterable_non_string_type_matcher(): TM(TM[IterableNonString])


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_lists'), pytest.lazy_fixture('i_dicts'),
                          pytest.lazy_fixture('i_tuples'), pytest.lazy_fixture('i_sets')))
def test_valid_iter_non_string_types(situation, match_types):
    checker = TM(TM[IterableNonString]) if match_types else TM(IterableNonString)
    assert checker((situation[1])), (f'{SHOULDA_PASSED}'
                                     f'checker: {checker}\n'
                                     f'value: {repr(situation[1])}')


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_bytes'), pytest.lazy_fixture('i_strs')))
def test_invalid_iter_non_string_types(situation, match_types):
    checker = TM(TM[IterableNonString]) if match_types else TM(IterableNonString)
    assert not checker((situation[1])), (f'{SHOULDNA_PASSED}'
                                         f'checker: {checker}\n'
                                         f'value: {repr(situation[1])}')


def test_generate_spec_iterable_types(base_types): TM(Iterable[base_types])


def test_generate_matcher_of_spec_iterable_type_matchers(base_types): TM(TM[Iterable[base_types]])


ITERABLE_TYPE_ALIGNMENTS = {
    str: [str, object],
    int: [int, object],
    float: [float, object],
    bytes: [bytes, object],
    bool: [bool, object],
    complex: [complex, object],
    object: [object]
}


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_lists'), pytest.lazy_fixture('i_dicts'),
                          pytest.lazy_fixture('i_strs'), pytest.lazy_fixture('i_tuples'),
                          pytest.lazy_fixture('i_sets')))
def test_spec_iterable_type(situation, base_types, match_types):
    checker = TM(TM[Iterable[base_types]]) if match_types else TM(Iterable[base_types])
    t, val = situation
    if base_types in ITERABLE_TYPE_ALIGNMENTS[t]:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(situation[0])}')

    else:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(situation[0])}')


def test_spec_bytes_iterable_type(i_bytes, base_types, match_types):
    checker = TM(TM[Iterable[base_types]]) if match_types else TM(Iterable[base_types])
    t, val = i_bytes
    if base_types in (int, object):
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(i_bytes[0])}')

    else:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(i_bytes[0])}')


def test_generate_simple_sequence_type(): TM(Sequence)


def test_generate_matcher_of_simple_sequence_type_matcher(): TM(TM[Sequence])


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_lists'), pytest.lazy_fixture('i_strs'),
                          pytest.lazy_fixture('i_tuples'), pytest.lazy_fixture('i_bytes')))
def test_simple_sequence_types(situation, match_types):
    checker = TM(TM[Sequence]) if match_types else TM(Sequence)
    assert checker((situation[1])), (f'{SHOULDA_PASSED}'
                                     f'checker: {checker}\n'
                                     f'value: {repr(situation[0])}')


def test_generate_spec_sequence_types(base_types): TM(Sequence[base_types])


def test_generate_matcher_of_spec_sequence_type_matchers(base_types): TM(TM[Sequence[base_types]])


@pytest.mark.parametrize('situation',
                         (pytest.lazy_fixture('i_lists'), pytest.lazy_fixture('i_strs'),
                          pytest.lazy_fixture('i_tuples')))
def test_spec_sequence_types(situation, base_types, match_types):
    checker = TM(TM[Iterable[base_types]]) if match_types else TM(Iterable[base_types])
    t, val = situation
    if base_types in ITERABLE_TYPE_ALIGNMENTS[t]:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(situation[0])}')

    else:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(situation[0])}')


def test_spec_bytes_sequence_types(i_bytes, base_types, match_types):
    checker = TM(TM[Iterable[base_types]]) if match_types else TM(Iterable[base_types])
    t, val = i_bytes
    if base_types in (int, object):
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(val)}')

    else:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(val)}')


@pytest.fixture(params=(
    (None, (None,), (..., (), True, False, 1, 0, 19.5)),
    (..., (...,), (None, (), True, False, 1, 0, 19.5)),
    (Ellipsis, (...,), (None, (), True, False, 1, 0, 19.5)),
    (bool, (True, False), (None, (), 1, 0, 19.5)),
    (int, (0, 1), (None, (), True, False, 19.5))
), ids=('None', 'Ellipsis (...)', 'Ellipsis', 'bool', 'int'))
def special_types3_10(request): return request.param


@pytest.fixture(params=(
    (None, (None,), (..., (), True, False, 1, 0, 19.5)),
    (bool, (True, False), (None, (), 1, 0, 19.5)),
    (int, (0, 1), (None, (), True, False, 19.5))
), ids=('None', 'bool', 'int'))
def special_types3_9(request): return request.param


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_generate_matchers_of_special_type_matchers_3_10(special_types3_10):
    TM(TM[special_types3_10[0]])


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason='Test is not needed for Python 3.10 or higher. Reserved for 3.9 or lower.'
)
def test_generate_matchers_of_special_type_matchers_3_8(special_types3_9):
    TM(TM[special_types3_9[0]])


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_special_types3_10(special_types3_10, match_types):
    t, good, bad = special_types3_10
    checker = TM(TM[t]) if match_types else TM(t)
    for val in good:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(val)}')

    for val in bad:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(val)}')


@pytest.mark.skipif(
    sys.version_info >= (3, 10),
    reason='Test is not needed for Python 3.10 or higher. Reserved for 3.9 and below.'
)
def test_special_types3_9(special_types3_9, match_types):
    t, good, bad = special_types3_9
    checker = TM(TM[t]) if match_types else TM(t)
    for val in good:
        assert checker(val), (f'{SHOULDA_PASSED}'
                              f'checker: {checker}\n'
                              f'value: {repr(val)}')

    for val in bad:
        assert not checker(val), (f'{SHOULDNA_PASSED}'
                                  f'checker: {checker}\n'
                                  f'value: {repr(val)}')


@pytest.mark.parametrize('situation', ('llama', b'horses'))
def test_any_str_for_strings(situation, match_types):
    checker = TM(TM[AnyStr]) if match_types else TM(AnyStr)
    assert checker(situation), (f'{SHOULDA_PASSED}'
                                f'checker: {checker}\n'
                                f'value: {repr(situation[0])}')


@pytest.mark.parametrize('situation', (47, 52.75, object()))
def test_any_str_for_non_strings(situation, match_types):
    checker = TM(TM[AnyStr]) if match_types else TM(AnyStr)
    assert not checker(situation), (f'{SHOULDNA_PASSED}'
                                    f'checker: {checker}\n'
                                    f'value: {repr(situation)}')


LITERAL_EXAMPLE = Literal['horse', 'llama', 'hare', 'giraffe']


@pytest.mark.parametrize(
    'value,expectation',
    (('horse', True), ('llama', True), ('hare', True), ('giraffe', True), ('F', False)),
    ids=('valid_val1', 'valid_val2', 'valid_val3', 'valid_val4', 'invalid_val'))
def test_literal(value, expectation, match_types):
    checker = TM(TM[LITERAL_EXAMPLE]) if match_types else TM(LITERAL_EXAMPLE)
    assert checker(value) == expectation, (f'{SHOULDA_PASSED if expectation else SHOULDNA_PASSED}'
                                           f'checker: {checker}\n'
                                           f'value: {repr(value)}')


UNION_TYPE = Union[int, str, None]


@pytest.fixture(params=(
    (INTS[0], True),
    (STRINGS[0], True),
    (None, True),
    (False, False),
    (FLOATS[0], False)
), ids=('int (valid)', 'str (valid)', 'None (valid)', 'bool (invalid)', 'float (invalid)'))
def union_vals(request): return request.param


def test_generate_union_type(): TM(UNION_TYPE)


def test_generate_matcher_of_union_type_matcher(): TM(TM[UNION_TYPE])


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_generate_uniony_type(): TM(int | str | None)


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_generate_matcher_of_uniony_type_matcher(): TM(TM[int | str | None])


def test_union_type(union_vals, match_types):
    checker = TM(TM[UNION_TYPE]) if match_types else TM(UNION_TYPE)
    val, expectation = union_vals
    assert checker(val) == expectation, (f'{SHOULDA_PASSED if expectation else SHOULDNA_PASSED}'
                                         f'checker: {checker}\n'
                                         f'value: {repr(val)}')


@pytest.mark.skipif(sys.version_info < (3, 10), reason='Test requires Python 3.10 or higher.')
def test_uniony_type(union_vals, match_types):
    checker = TM(TM[int | str | None]) if match_types else TM(int | str | None)
    val, expectation = union_vals
    assert checker(val) == expectation, (f'{SHOULDA_PASSED if expectation else SHOULDNA_PASSED}'
                                         f'checker: {checker}\n'
                                         f'value: {repr(val)}')


INT = 'integer'
STR = 'string'
FLT = 'float'
NTG = 'nothing'
WTVR =  'whatever'


def sig(consumes: str, produces: str) -> str:
    return f'signature | consumes {consumes}, produces {produces}'


# Sorry, not sorry.
VALID_FUNC_MAP = {
    (SC1 := callable): ((C1 := []), 'signature | any | `callable`'),
    (SC2 := Callable): ((C2 := []), 'signature | any | `Callable`'),
    (SN := Callable[[], None]): ((N := []), sig(NTG, NTG)),
    (SCA := Callable[..., None]): ((CA := []), sig(WTVR, NTG)),
    (SCI := Callable[[int], None]): ((CI := []), sig(INT, NTG)),
    (SPI := Callable[[], int]): ((PI := []), sig(NTG, INT)),
    (SCAPI := Callable[..., int]): ((CAPI := []), sig(WTVR, INT)),
    (SCFPI := Callable[[float], int]): ((CFPI := []), sig(FLT, INT)),
    (SCIASPF := Callable[[int, str], float]): ((CIASPF := []), sig(f'{INT} and {STR}', FLT)),
    (SPA := Callable[[], Any]): ((PA := []), sig(NTG, WTVR)),
    (SCAPA := Callable[..., Any]): ((CAPA := []), sig(WTVR, WTVR)),
    (SCIPA := Callable[[int], Any]): ((CIPA := []), sig(INT, WTVR)),
    (SCIASPA := Callable[[int, str], Any]): ((CIASPA := []), sig(f'{INT} and {STR}', WTVR))
}
FUNCS = []
FUNC_NAMES = []


@pytest.fixture(params=VALID_FUNC_MAP.keys(), ids=tuple(v[1] for v in VALID_FUNC_MAP.values()))
def callable_types(request): return request.param


def test_generate_callable_types(callable_types): TM(callable_types)


def test_generate_matchers_of_callable_type_matchers(callable_types): TM(TM[callable_types])


def at(func: callable, args: List[Union[type, str]], ret: type = None, *to: list):
    """Append To"""
    FUNCS.append(func)
    FUNC_NAMES.append(f'func signature | ({", ".join(str(v) for v in args)}) -> {ret}')

    # Blanket append. Every callable should pass the generic callables.
    C1.append(func)
    C2.append(func)
    CAPA.append(func)

    # append to any extras specified.
    for to_ in to:
        to_.append(func)


def sig_blah1(a: str) -> None: ...


at(sig_blah1, [str], None, CA)


def sig_blah2(a: int, b: str, c: float) -> float: return (a + int(b)) * c


at(sig_blah2, [int, str, float], float)


def sig_blah3() -> float: return math.pi


at(sig_blah3, [], float, PA)


def sig_null() -> None: ...


at(sig_null, [], None, N, CA, PA)


def sig_consumes_whatever1(a: float, b: str) -> None: ...


at(sig_consumes_whatever1, [float, str], None, CA)


def sig_consumes_whatever2(a: int, *b: str) -> None: ...


at(sig_consumes_whatever2, [int, '*str'], None, CA)


def sig_consumes_whatever3(a: int, /, b: int) -> None: ...


at(sig_consumes_whatever3, [int, '/', int], None, CA)


def sig_consumes_whatever4(a: int, /, b: int, **c) -> None: ...


at(sig_consumes_whatever4, [int, '/', int, '**Any'], None, CA)


def sig_consumes_int_norm(a: int) -> None: ...


at(sig_consumes_int_norm, [int], None, CA, CI, CIPA)


def sig_consumes_int_pos_only(a: int, /) -> None: ...


at(sig_consumes_int_pos_only, [int, '/'], None, CA, CI, CIPA)


def sig_consumes_nothing_produces_int() -> int: return 5


at(sig_consumes_nothing_produces_int, [], int, CAPI, PI, PA)


def sig_consumes_whatever_produces_int1(a: float, b: str) -> int: return int(a * len(b))


at(sig_consumes_whatever_produces_int1, [float, str], int, CAPI)


def sig_consumes_whatever_produces_int2(a: int, *b: str) -> int: return a * sum(len(c) for c in b)


at(sig_consumes_whatever_produces_int2, [int, '*str'], int, CAPI)


def sig_consumes_whatever_produces_int3(a: int, /, b: int) -> int: return a * b


at(sig_consumes_whatever_produces_int3, [int, '/', int], int, CAPI)


def sig_consumes_whatever_produces_int4(a: int, /, b: int, **c) -> int:
    return a // b + sum(len(d) * float(e) for d, e in c.items())


at(sig_consumes_whatever_produces_int4, [float, str], int, CAPI)


def sig_consumes_float_produces_int_norm(a: float) -> int: return int(a)


at(sig_consumes_float_produces_int_norm, [float], int, CAPI, CFPI)


def sig_consumes_float_produces_int_pos_only(a: float, /) -> int: return int(a)


at(sig_consumes_float_produces_int_pos_only, [float, '/'], int, CAPI, CFPI)


def sig_consumes_int_and_string_produces_float_norm(a: int, b: str) -> float: return a / len(b)


at(sig_consumes_int_and_string_produces_float_norm, [int, str], float, CIASPF, CIASPA)


def sig_consumes_int_and_string_produces_float_one_pos_only(a: int, /, b: str) -> float:
    return a / len(b)


at(sig_consumes_int_and_string_produces_float_one_pos_only, [int, '/', str], float, CIASPF, CIASPA)


def sig_consumes_int_and_string_produces_float_pos_only(a: int, b: str, /) -> float:
    return a / len(b)


at(sig_consumes_int_and_string_produces_float_pos_only, [int, str, '/'], float, CIASPF, CIASPA)


def sig_consumes_int_and_string_produces_int_norm(a: int, b: str) -> int: return a // len(b)


at(sig_consumes_int_and_string_produces_int_norm, [int, str], int, CAPI, CIASPA)


def sig_consumes_int_and_string_produces_int_one_pos_only(a: int, /, b: str) -> int: return a // len(b)


at(sig_consumes_int_and_string_produces_int_one_pos_only, [int, '/', str], int, CAPI, CIASPA)


def sig_consumes_int_and_string_produces_int_pos_only(a: int, b: str, /) -> int: return a // len(b)


at(sig_consumes_int_and_string_produces_int_pos_only, [int, str, '/'], int, CAPI, CIASPA)


@pytest.fixture(params=FUNCS, ids=FUNC_NAMES)
def funcs(request, callable_types):
    func = request.param
    return callable_types, func, any(func is func_ for func_ in VALID_FUNC_MAP[callable_types][0])


def test_funcs(funcs, match_types):
    t, func, expected = funcs
    checker = TM(TM[t]) if match_types else TM(t)
    assert checker(func) == expected
