from dataclasses import dataclass
from typing import Union

import pytest

from t_support import cov, cov_counter
from funk_py.modularity.basic_structures import pass_
from funk_py.sorting.pieces import convert_tuplish_dict


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


NEWLINE = '\n'


@dataclass
class TuplishDictDef:
    data: Union[dict, list]
    result: dict
    pair_name: str = None
    key_name: str = None
    val_name: str = None


@dataclass
class InAndOut:
    data: Union[dict, list]
    result: dict


T_EXTENT = 100
PAIR_NAME = 'pair'
KEY_NAME = 'key'
VAL_NAME = 'value'


KEYS = ['k' + str(i) for i in range(T_EXTENT)]
VALS = ['v' + str(i) for i in range(T_EXTENT)]


@pytest.fixture
def general_output():
    return {KEYS[i]: VALS[i] for i in range(T_EXTENT)}


@pytest.fixture(params=(
        (lambda x: {PAIR_NAME: {KEY_NAME: x}}, False, False),
        (lambda x: {PAIR_NAME: {KEY_NAME: {KEYS[0]: x}}}, False, False),
        (pass_, True, False),
        (pass_, True, True),
        (lambda x: {KEY_NAME: x}, True, False),
        (lambda x: {KEY_NAME: x}, True, True),
), ids=(
        'pairs_in_list',
        'pairs+keys_in_list',
        'single_pair',
        'single_pair_in_list',
        'single_pair+keys',
        'single_pair+keys_in_list',
))
def simple_pairs_in_out(request, general_output):
    func, single_pair_case, in_list_case = request.param
    in_builder = []
    if single_pair_case:
        for i in range(T_EXTENT):
            in_builder.append(func([KEYS[i], VALS[i]]))

        in_builder = {PAIR_NAME: in_builder}

        if in_list_case:
            in_builder = [in_builder]

    else:
        for i in range(T_EXTENT):
            in_builder.append(func([KEYS[i], VALS[i]]))

    return InAndOut(in_builder, general_output)


@pytest.fixture(params=(
        (PAIR_NAME, None),
        (None, KEY_NAME),
        (PAIR_NAME, KEY_NAME),
        (None, None),
), ids=(
        'with_pair_name_only',
        'with_key_name_only',
        'with_pair_name_and_key_name',
        'without_pair_name_or_key_name',
))
def simple_pairs_in_list(request, simple_pairs_in_out):
    return TuplishDictDef(
        data=simple_pairs_in_out.data,
        pair_name=request.param[0],
        key_name=request.param[1],
        val_name=request.param[1],
        result=simple_pairs_in_out.result
    )


def test_simple_pairs_in_list(simple_pairs_in_list):
    """
    Test for forms:

    Form 1 (pairs_in_list):

    [{PAIR_NAME: [k0: v0]}, {PAIR_NAME: [k1: v1]}, {PAIR_NAME: [k2: v2]}, ...]

    Form 2 (pairs+keys_in_list):

    [{PAIR_NAME: {KEY: [k0: v0]}}, {PAIR_NAME: {KEY: [k1: v1]}}, {PAIR_NAME: {KEY: [k2: v2]}}, ...]

    Form 3 (single_pair):

    {PAIR_NAME: [[k0: v0], [k1: v1], [k2: v2], ...]}

    Form 4 (single_pair_in_list):

    [{PAIR_NAME: [[k0: v0], [k1: v1], [k2: v2], ...]}]

    These tests are run with both with pair_name specified and without pair_name specified.

    Expected result: {k0: v0, k1: v1, k2: v2, ...}
    """
    assert convert_tuplish_dict(simple_pairs_in_list.data,
                                simple_pairs_in_list.pair_name) == simple_pairs_in_list.result


@pytest.fixture
def simple_pairs_in_dict(simple_pairs_in_list):
    return TuplishDictDef(
        data={KEYS[0]: simple_pairs_in_list.data},
        pair_name=simple_pairs_in_list.pair_name,
        key_name=simple_pairs_in_list.key_name,
        val_name=simple_pairs_in_list.val_name,
        result=simple_pairs_in_list.result
    )


def test_simple_pairs_in_dict(simple_pairs_in_dict):
    """
    Test for forms:

    Form 1 (pairs_in_list):

    {k0: [{PAIR_NAME: {KEY_NAME: [k0: v0]}}, {PAIR_NAME: {KEY_NAME: [k1: v1]}},
          {PAIR_NAME: {KEY_NAME: [k2: v2]}}, ...]}

    Form 2 (pairs+keys_in_list):

    {k0: [{PAIR_NAME: {KEY_NAME: {k0: [k0: v0]}}}, {PAIR_NAME: {KEY_NAME: {k0: [k1: v1]}}},
          {PAIR_NAME: {KEY_NAME: {k0: [k2: v2]}}}, ...]}

    Form 3 (single_pair):

    {k0: {PAIR_NAME: [{KEY_NAME: [k0: v0]}, {KEY_NAME: [k1: v1]}, {KEY_NAME: [k2: v2]}, ...]}}

    Form 4 (single_pair_in_list):

    {k0: [{PAIR_NAME: [{KEY_NAME: [k0: v0]}, {KEY_NAME: [k1: v1]}, {KEY_NAME: [k2: v2]}, ...]}]}

    Form 5 (single_pair+keys):

    {k0: {PAIR_NAME: [{KEY_NAME: {k0: [k0: v0]}}, {KEY_NAME: {k0: [k1: v1]}},
                      {KEY_NAME: {k0: [k2: v2]}}, ...]}}

    Form 6 (single_pair+keys_in_list):

    {k0: [{PAIR_NAME: [{KEY_NAME: {k0: [k0: v0]}}, {KEY_NAME: {k0: [k1: v1]}},
                       {KEY_NAME: {k0: [k2: v2]}}, ...]}]}

    These tests are run with both with pair_name specified and without pair_name specified.

    Expected result: {k0: v0, k1: v1, k2: v2, ...}
    """
    assert convert_tuplish_dict(simple_pairs_in_dict.data,
                                simple_pairs_in_dict.pair_name) == simple_pairs_in_dict.result


@pytest.fixture
def simple_pairs_in_dict_with_more_than_one_key(simple_pairs_in_list):
    return TuplishDictDef(
        data={KEYS[0]: VALS[0], KEYS[1]: simple_pairs_in_list.data},
        result={}
    )


def test_simple_pairs_in_dict_with_more_than_one_need_pair_or_key_and_val_name(
        simple_pairs_in_dict_with_more_than_one_key
):
    """
    Test for forms:

    Form 1 (pairs_in_list):

    {k0: v0, k1: [{PAIR_NAME: {KEY_NAME: [k0: v0]}}, {PAIR_NAME: {KEY_NAME: [k1: v1]}},
                  {PAIR_NAME: {KEY_NAME: [k2: v2]}}, ...]}

    Form 2 (pairs+keys_in_list):

    {k0: v0, k1: [{PAIR_NAME: {KEY_NAME: {k0: [k0: v0]}}}, {PAIR_NAME: {KEY_NAME: {k0: [k1: v1]}}},
                  {PAIR_NAME: {KEY_NAME: {k0: [k2: v2]}}}, ...]}

    Form 3 (single_pair):

    {k0: v0, k1: {PAIR_NAME: [{KEY_NAME: [k0: v0]}, {KEY_NAME: [k1: v1]},
                              {KEY_NAME: [k2: v2]}, ...]}}

    Form 4 (single_pair_in_list):

    {k0: v0, k1: [{PAIR_NAME: [{KEY_NAME: [k0: v0]}, {KEY_NAME: [k1: v1]},
                               {KEY_NAME: [k2: v2]}, ...]}]}

    Form 5 (single_pair+keys):

    {k0: v0, k1: {PAIR_NAME: [{KEY_NAME: {k0: [k0: v0]}}, {KEY_NAME: {k0: [k1: v1]}},
                              {KEY_NAME: {k0: [k2: v2]}}, ...]}}}

    Form 6 (single_pair+keys_in_list):

    {k0: v0, k1: [{PAIR_NAME: [{KEY_NAME: {k0: [k0: v0]}}, {KEY_NAME: {k0: [k1: v1]}},
                               {KEY_NAME: {k0: [k2: v2]}}, ...]}]}

    These tests are run with both with pair_name specified and without pair_name specified.

    Expected result: {}
    """
    assert (convert_tuplish_dict(simple_pairs_in_dict_with_more_than_one_key.data,
                                 simple_pairs_in_dict_with_more_than_one_key.pair_name)
            == simple_pairs_in_dict_with_more_than_one_key.result)


@pytest.fixture
def general_nesting_output():
    return {KEYS[i]: {KEYS[i + 1]: VALS[i]} for i in range(0, T_EXTENT, 2)}


NESTED = 'nested'


@pytest.fixture(params=(
        ({KEYS[0]: VALS[0], PAIR_NAME: [[KEYS[i], VALS[i]] for i in range(T_EXTENT)]}, None),
        ([{KEYS[0]: VALS[0], PAIR_NAME: [KEYS[i], VALS[i]]} for i in range(T_EXTENT)], None),
        (
            {
                KEYS[0]: VALS[0],
                PAIR_NAME: [[KEYS[i], KEYS[i + 1], VALS[i]] for i in range(0, T_EXTENT, 2)],
            },
            NESTED
        ),
        (
            [
                {
                    KEYS[0]: VALS[0],
                    PAIR_NAME: [KEYS[i], KEYS[i + 1], VALS[i]],
                } for i in range(0, T_EXTENT, 2)
            ],
            NESTED
        ),
), ids=('direct_dict', 'dicts_in_list', 'nesting_direct_dict', 'nesting_dicts_in_list'))
def pair_name_needed(request, general_output, general_nesting_output):
    data, output = request.param
    output = output or general_output
    output = general_nesting_output if output == NESTED else output
    return TuplishDictDef(
        data=data,
        pair_name=PAIR_NAME,
        result=output
    )


def test_pair_name_fixes_pair_name_needed(pair_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, PAIR_NAME: [[k0, v0], [k1, v1], [k2, v2], ...]}

    Form 1 expected result: {k0: v0, k1: v1, k2: v2, ...}

    Form 2 (dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, v0]}, {k0: v0, PAIR_NAME: [k1, v1]},
     {k0: v0, PAIR_NAME: [k2, v2]}, ...]

    Form 2 expected result: {k0: v0, k1: v1, k2: v2, ...}

    Form 3 (nesting_direct_dict):

    {k0: v0, PAIR_NAME: [[k0, k1, v0], [k2, k3, v2], [k4, k5, v4], ...]}

    Form 3 expected result: {k0: {k1: v0}, k2: {k3: v2}, k4: {k5: v4}, ...}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, k1, v0]}, {k0: v0, PAIR_NAME: [k2, k3, v2]},
     {k0: v0, PAIR_NAME: [k4, k5, v4]}, ...]

    Form 4 expected result: {k0: {k1: v0}, k2: {k3: v2}, k4: {k5: v4}, ...}

    These tests are only run with pair_name specified.
    """
    assert (convert_tuplish_dict(pair_name_needed.data,
                                 pair_name_needed.pair_name) == pair_name_needed.result)


def test_nothing_with_key_val_same_name_when_pair_name_needed(pair_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, PAIR_NAME: [[k0, v0], [k1, v1], [k2, v2], ...]}

    Form 2 (dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, v0]}, {k0: v0, PAIR_NAME: [k1, v1]},
     {k0: v0, PAIR_NAME: [k2, v2]}, ...]

    Form 3 (nesting_direct_dict):

    {k0: v0, PAIR_NAME: [[k0, k1, v0], [k2, k3, v2], [k4, k5, v4], ...]}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, k1, v0]}, {k0: v0, PAIR_NAME: [k2, k3, v2]},
     {k0: v0, PAIR_NAME: [k4, k5, v4]}, ...]

    These tests are only run with key_name and val_name specified as the same value.

    Expected result: {}
    """
    assert convert_tuplish_dict(pair_name_needed.data, key_name=KEY_NAME, val_name=KEY_NAME) == {}


def test_nothing_with_key_val_diff_name_when_pair_name_needed(pair_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, PAIR_NAME: [[k0, v0], [k1, v1], [k2, v2], ...]}

    Form 2 (dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, v0]}, {k0: v0, PAIR_NAME: [k1, v1]},
     {k0: v0, PAIR_NAME: [k2, v2]}, ...]

    Form 3 (nesting_direct_dict):

    {k0: v0, PAIR_NAME: [[k0, k1, v0], [k2, k3, v2], [k4, k5, v4], ...]}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, PAIR_NAME: [k0, k1, v0]}, {k0: v0, PAIR_NAME: [k2, k3, v2]},
     {k0: v0, PAIR_NAME: [k4, k5, v4]}, ...]

    These tests are only run with key_name and val_name specified as different values.

    Expected result: {}
    """
    assert convert_tuplish_dict(pair_name_needed.data, key_name=KEY_NAME, val_name=VAL_NAME) == {}


@pytest.fixture(params=(
        ({KEYS[0]: VALS[0], KEY_NAME: [KEYS[0], VALS[0]]}, {KEYS[0]: VALS[0]}),
        ([{KEYS[0]: VALS[0], KEY_NAME: [KEYS[i], VALS[i]]} for i in range(T_EXTENT)], None),
        ({KEYS[0]: VALS[0], KEY_NAME: [KEYS[0], KEYS[1], VALS[0]]}, {KEYS[0]: {KEYS[1]: VALS[0]}}),
        (
            [
                {
                    KEYS[0]: VALS[0],
                    KEY_NAME: [KEYS[i], KEYS[i + 1], VALS[i]]
                } for i in range(0, T_EXTENT, 2)
            ],
            NESTED
        ),
), ids=('direct_dict', 'dicts_in_list', 'nesting_direct_dict', 'nesting_dicts_in_list'))
def key_val_same_name_needed(request, general_output, general_nesting_output):
    data, output = request.param
    output = output or general_output
    output = general_nesting_output if output == NESTED else output
    return TuplishDictDef(
        data=data,
        key_name=KEY_NAME,
        val_name=KEY_NAME,
        result=output
    )


def test_key_val_same_name_fixes_key_val_same_name_needed(key_val_same_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, KEY_NAME: [k0, v0]}

    Form 1 expected result: {k0, v0}

    Form 2 (dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, v0]}, {k0: v0, KEY_NAME: [k1, v1]}, {k0: v0, KEY_NAME: [k2, v2]}, ...]

    Form 2 expected result: {k0: v0, k1: v1, k2: v2, ...}

    Form 3 (nesting_direct_dict):

    {k0: v0, KEY_NAME: [k0, k1, v0]}

    Form 3 expected result: {k0: {k1: v0}}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, k1, v0]}, {k0: v0, KEY_NAME: [k2, k3, v2]},
     {k0: v0, KEY_NAME: [k4, k5, v4]}, ...]

    Form 4 expected result: {k0: {k1: v0}, k2: {k3: v2}, k4: {k5: v4}, ...}

    These tests are only run with key_name and val_name specified as the same value.
    """
    assert (convert_tuplish_dict(key_val_same_name_needed.data,
                                 key_name=key_val_same_name_needed.key_name,
                                 val_name=key_val_same_name_needed.val_name)
            == key_val_same_name_needed.result)


def test_nothing_with_pair_name_when_key_val_same_name_needed(key_val_same_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, KEY_NAME: [k0, v0]}

    Form 2 (dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, v0]}, {k0: v0, KEY_NAME: [k1, v1]},
     {k0: v0, KEY_NAME: [k2, v2]}, ...]

    Form 3 (nesting_direct_dict):

    {k0: v0, KEY_NAME: [k0, k1, v0]}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, k1, v0]}, {k0: v0, KEY_NAME: [k2, k3, v2]},
     {k0: v0, KEY_NAME: [k4, k5, v4]}, ...]

    These tests are only run with pair_name specified.

    Expected result: {}
    """
    assert convert_tuplish_dict(key_val_same_name_needed.data, pair_name=PAIR_NAME) == {}


def test_nothing_with_key_val_diff_name_when_key_val_same_name_needed(key_val_same_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {k0: v0, KEY_NAME: [k0, v0]}

    Form 2 (dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, v0]}, {k0: v0, KEY_NAME: [k1, v1]},
     {k0: v0, KEY_NAME: [k2, v2]}, ...]

    Form 3 (nesting_direct_dict):

    {k0: v0, KEY_NAME: [k0, k1, v0]}

    Form 4 (nesting_dicts_in_list):

    [{k0: v0, KEY_NAME: [k0, k1, v0]}, {k0: v0, KEY_NAME: [k2, k3, v2]},
     {k0: v0, KEY_NAME: [k4, k5, v4]}, ...]

    These tests are only run with key_name and val_name specified as different values.

    Expected result: {}
    """
    assert convert_tuplish_dict(key_val_same_name_needed.data,
                                key_name=KEY_NAME,
                                val_name=VAL_NAME) == {}


KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT = {KEY_NAME: [KEYS[0], KEYS[1]], VAL_NAME: VALS[0]}
KEY_VAL_DIFF_NAME_NESTED_DICTS_IN_LIST = [
    {KEY_NAME: [KEYS[i], KEYS[i + 1]], VAL_NAME: VALS[i]} for i in range(0, T_EXTENT, 2)
]
KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT_EXTRA_KEY = {
    KEYS[0]: VALS[0], KEY_NAME: [KEYS[0], KEYS[1]], VAL_NAME: VALS[0]
}
KEY_VAL_DIFF_NAME_NESTED_DICTS_EXTRA_KEYS_IN_LIST = [
    {
        KEYS[0]: VALS[0],
        KEY_NAME: [KEYS[i], KEYS[i + 1]],
        VAL_NAME: VALS[i]
    } for i in range(0, T_EXTENT, 2)
]
KEY_VAL_DIFF_NAME_DIRECT_DICT_NESTED_RESULT = {KEYS[0]: {KEYS[1]: VALS[0]}}



@pytest.fixture(params=(
        ({KEY_NAME: KEYS[0], VAL_NAME: VALS[0]}, {KEYS[0]: VALS[0]}),
        ([{KEY_NAME: KEYS[i], VAL_NAME: VALS[i]} for i in range(T_EXTENT)], None),
        ({KEYS[0]: VALS[0], KEY_NAME: KEYS[0], VAL_NAME: VALS[0]}, {KEYS[0]: VALS[0]}),
        ([{KEYS[0]: VALS[0], KEY_NAME: KEYS[i], VAL_NAME: VALS[i]} for i in range(T_EXTENT)], None),
        (KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT, KEY_VAL_DIFF_NAME_DIRECT_DICT_NESTED_RESULT),
        (KEY_VAL_DIFF_NAME_NESTED_DICTS_IN_LIST, NESTED),
        (
            KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT_EXTRA_KEY,
            KEY_VAL_DIFF_NAME_DIRECT_DICT_NESTED_RESULT
        ),
        (KEY_VAL_DIFF_NAME_NESTED_DICTS_EXTRA_KEYS_IN_LIST, NESTED),
), ids=('direct_dict', 'dicts_in_list', 'direct_dict+extra_key', 'dicts+extra_keys_in_list',
        'nested_direct_dict', 'nested_dicts_in_list', 'nested_direct_dict+extra_key',
        'nested_dicts+extra_keys_in_list'))
def key_val_diff_name_needed(request, general_output, general_nesting_output):
    data, output = request.param
    output = output or general_output
    output = general_nesting_output if output == NESTED else output
    return TuplishDictDef(
        data=data,
        key_name=KEY_NAME,
        val_name=VAL_NAME,
        result=output
    )


def test_key_val_diff_name_fixes_key_val_diff_name_needed(key_val_diff_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {KEY_NAME: k0, VAL_NAME: v0}

    Form 1 expected result: {k0, v0}

    Form 2 (dicts_in_list):

    [{KEY_NAME: k0, VAL_NAME: v0}, {KEY_NAME: k1, VAL_NAME: v1}, {KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 2 expected result: {k0: v0, k1: v1, k2: v2, ...}

    Form 3 (direct_dict+extra_key):

    {k0: v0, KEY_NAME: k0, VAL_NAME: v0}

    Form 3 expected result: {k0: v0}

    Form 4 (dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: k0, VAL_NAME: v0}, {k0: v0, KEY_NAME: k1, VAL_NAME: v1},
     {k0: v0, KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 4 expected result: {k0: v0, k1: v1, k2: v2, ...}

    Form 5 (nested_direct_dict):

    {KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 5 expected result: {k0, {k1: v0}}

    Form 6 (nested_dicts_in_list):

    [{KEY_NAME: [k0, k1], VAL_NAME: v0}, {KEY_NAME: [k2, k3], VAL_NAME: v2},
     {KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    Form 6 expected result: {k0: {k1: v0}, k2: {k3: v2}, k4: {k5: v4}, ...}

    Form 7 (nested_direct_dict+extra_key):

    {k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 7 expected result: {k0, {k1: v0}}

    Form 8 (nested_dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}, {k0: v0, KEY_NAME: [k2, k3], VAL_NAME: v2},
     {k0: v0, KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    Form 8 expected result: {k0: {k1: v0}, k2: {k3: v2}, k4: {k5: v4}, ...}

    These tests are only run with key_name and val_name specified as different values.
    """
    assert (convert_tuplish_dict(key_val_diff_name_needed.data,
                                 key_name=key_val_diff_name_needed.key_name,
                                 val_name=key_val_diff_name_needed.val_name)
            == key_val_diff_name_needed.result)


def test_nothing_with_pair_name_when_key_val_diff_name_needed(key_val_diff_name_needed):
    """
    Test for forms:

    Form 1 (direct_dict):

    {KEY_NAME: k0, VAL_NAME: v0}

    Form 2 (dicts_in_list):

    [{KEY_NAME: k0, VAL_NAME: v0}, {KEY_NAME: k1, VAL_NAME: v1}, {KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 3 (direct_dict+extra_key):

    {k0: v0, KEY_NAME: k0, VAL_NAME: v0}

    Form 4 (dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: k0, VAL_NAME: v0}, {k0: v0, KEY_NAME: k1, VAL_NAME: v1},
     {k0: v0, KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 5 (nested_direct_dict):

    {KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 6 (nested_dicts_in_list):

    [{KEY_NAME: [k0, k1], VAL_NAME: v0}, {KEY_NAME: [k2, k3], VAL_NAME: v2},
     {KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    Form 7 (nested_direct_dict+extra_key):

    {k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 8 (dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}, {k0: v0, KEY_NAME: [k2, k3], VAL_NAME: v2},
     {k0: v0, KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    These tests are only run with pair_name specified.

    Expected result: {}
    """
    assert convert_tuplish_dict(key_val_diff_name_needed.data, pair_name=PAIR_NAME) == {}


def test_nothing_with_key_val_same_name_when_key_val_diff_name_needed(
        key_val_diff_name_needed,
        general_nesting_output
):
    """
    Test for forms:

    Form 1 (direct_dict):

    {KEY_NAME: k0, VAL_NAME: v0}

    Form 2 (dicts_in_list):

    [{KEY_NAME: k0, VAL_NAME: v0}, {KEY_NAME: k1, VAL_NAME: v1}, {KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 3 (direct_dict+extra_key):

    {k0: v0, KEY_NAME: k0, VAL_NAME: v0}

    Form 4 (dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: k0, VAL_NAME: v0}, {k0: v0, KEY_NAME: k1, VAL_NAME: v1},
     {k0: v0, KEY_NAME: k2, VAL_NAME: v2}, ...]

    Form 5 (nested_direct_dict):

    {KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 5 expected result: {k0: k1}

    Form 6 (nested_dicts_in_list):

    [{KEY_NAME: [k0, k1], VAL_NAME: v0}, {KEY_NAME: [k2, k3], VAL_NAME: v2},
     {KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    Form 6 expected result: {k0: k1, k2: k3, k4: k5, ...}

    Form 7 (nested_direct_dict+extra_key):

    {k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}

    Form 7 expected result: {k0: k1}

    Form 8 (nested_dicts+extra_keys_in_list):

    [{k0: v0, KEY_NAME: [k0, k1], VAL_NAME: v0}, {k0: v0, KEY_NAME: [k2, k3], VAL_NAME: v2},
     {k0: v0, KEY_NAME: [k4, k5], VAL_NAME: v4}, ...]

    Form 8 expected result: {k0: k1, k2: k3, k4: k5, ...}

    These tests are only run with key_name and val_name specified as the same value.

    Forms 1-4 expected result: {}
    """
    test = convert_tuplish_dict(key_val_diff_name_needed.data, key_name=KEY_NAME, val_name=KEY_NAME)
    if key_val_diff_name_needed.data in (KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT,
                                         KEY_VAL_DIFF_NAME_NESTED_DIRECT_DICT_EXTRA_KEY):
        assert test == {KEYS[0]: KEYS[1]}

    elif key_val_diff_name_needed.data in (KEY_VAL_DIFF_NAME_NESTED_DICTS_IN_LIST,
                                           KEY_VAL_DIFF_NAME_NESTED_DICTS_EXTRA_KEYS_IN_LIST):
        assert test == {KEYS[i]: KEYS[i + 1] for i in range(0, T_EXTENT, 2)}

    else:
        assert test == {}

