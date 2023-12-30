from typing import Tuple, Any

import pytest
from funk_py.super_dicts.drop_none_dict import DropNoneDict as DnD


NOT_CAUSE = 'Test failed to generate the expected start value. The issue is' \
            ' probably elsewhere.'

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

K = [char for char in ALPHABET] + ['a' + char for char in ALPHABET]

CV = [1, True, '1',
      0, False, '0', '', {}, [], (), set(), range(0),
      None, ...]
V = ['lorem', 25, b'ipsum', 57.56]
AV = ['dolor', 90, b'sit', 900.5]

CONTROL = 'control'


@pytest.fixture
def confused_values_base():
    output = {K[i]: CV[i] for i in range(len(CV))}
    output[CONTROL] = CONTROL
    return output


@pytest.fixture(params=[(CV[j], j) for j in range(len(CV))])
def confused_values(request, confused_values_base):
    none = request.param[0]
    pos = request.param[1]
    expected = {K[i]: CV[i] for i in range(len(CV)) if i != pos}
    expected[CONTROL] = CONTROL

    key_rem_prog = []
    holder = expected.copy()
    for key in expected:
        holder = {k: v for k, v in holder.items() if k != key}
        key_rem_prog.append((key, none, holder))

    key_add_prog = []
    holder = expected.copy()
    for i in range(len(CV)):
        if i != pos:
            key = K[i + len(CV)]
            val = CV[i]
            holder = holder.copy()
            holder[key] = val
            key_add_prog.append((key, val, holder))

    return none, expected, K[len(CV)], key_rem_prog, key_add_prog


@pytest.fixture
def regular_values_base():
    return {K[i]: V[i] for i in range(len(V))}


@pytest.fixture
def regular_values(regular_values_base):
    builder = regular_values_base
    v_len = len(V)

    add_inst = []
    for i in range(len(AV)):
        key = K[i + v_len]
        val = AV[i]
        builder = builder.copy()
        builder[key] = val
        add_inst.append((key, val, builder))

    return add_inst


def follow_and_assert_set_steps(input_: DnD, steps: Tuple[str, Any, dict]):
    for step in steps:
        key = step[0]
        val = step[1]
        result = step[2]
        input_[key] = val
        assert input_ == result


def test_confused_values(confused_values_base, confused_values):
    none = confused_values[0]
    expected = confused_values[1]

    dnd = DnD(confused_values_base, none_condition=none)
    assert dnd == expected


def test_not_add_none(confused_values):
    none = confused_values[0]
    expected = confused_values[1]
    key = confused_values[2]

    # Always test that we started out right. If this first assertion fails, then
    # it's unlikely that the root cause is directly related to what this test
    # should check.
    dnd = DnD(expected, none_condition=none)
    assert dnd == expected, NOT_CAUSE

    dnd[key] = none
    assert dnd == expected


def test_set_to_none(confused_values):
    none = confused_values[0]
    expected = confused_values[1]
    key_rem_prog = confused_values[3]

    # Always test that we started out right. If this first assertion fails, then
    # it's unlikely that the root cause is directly related to what this test
    # should check.
    dnd = DnD(expected, none_condition=none)
    assert dnd == expected, NOT_CAUSE

    follow_and_assert_set_steps(dnd, key_rem_prog)


def test_add_non_none_not_confused(confused_values):
    none = confused_values[0]
    expected = confused_values[1]
    key_add_prog = confused_values[4]

    # Always test that we started out right. If this first assertion fails, then
    # it's unlikely that the root cause is directly related to what this test
    # should check.
    dnd = DnD(expected, none_condition=none)
    assert dnd == expected, NOT_CAUSE

    follow_and_assert_set_steps(dnd, key_add_prog)


def test_add_non_none(regular_values_base, regular_values):
    # Always test that we started out right. If this first assertion fails, then
    # it's unlikely that the root cause is directly related to what this test
    # should check.
    dnd = DnD(regular_values_base)
    assert dnd == regular_values_base, NOT_CAUSE

    follow_and_assert_set_steps(dnd, regular_values)


def test_del_keys(regular_values_base):
    # Always test that we started out right. If this first assertion fails, then
    # it's unlikely that the root cause is directly related to what this test
    # should check.
    dnd = DnD(regular_values_base)
    assert dnd == regular_values_base, NOT_CAUSE

    copied = regular_values_base.copy()
    for key in regular_values_base.keys():
        # Essentially, just do the same operation on both a DropNoneDict and a
        # dict, they should do the same thing and still test equivalent.
        del dnd[key]
        del copied[key]
        assert dnd == copied
