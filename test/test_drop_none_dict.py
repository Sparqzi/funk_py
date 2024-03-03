from collections import namedtuple
from typing import Tuple, Any, Union

import pytest

from t_support import cov, cov_counter
from funk_py.super_dicts.drop_none_dict import DropNoneDict as DnD


# The following manages whether the generated coverage instance from t_support should report. This
# method of coverage is used so that coverage can be turned off to not interfere in timed tests.
@pytest.fixture(scope='session', autouse=True)
def c():
    if not cov_counter.value:
        # We don't want to start coverage more than once
        cov.start()

    cov_counter.value += 1

    yield cov

    cov_counter.value -= 1

    # We don't want to report till all test modules are completed...
    if not cov_counter.value:
        cov.stop()
        cov.save()
        cov.report()


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


# ------------------------------------------------------------------------------
# none_if tests
# ------------------------------------------------------------------------------

NoneIfTst = namedtuple('NoneIfTst',
                       {'value', 'none_val', 'plug_in', 'plug_out', 'output'})

GV = 19
LV = GV - 1
LLV = GV - 2
GENERAL_PLUG_IN = lambda x: x + 1  # noqa
DIFFERENT_PLUG_IN = lambda x: x < GV  # noqa
GENERAL_PLUG_OUT = 'same_type_plug_out'
DIFFERENT_PLUG_OUT = 'different_type_plug_out'


def none_if_dicts(tst: NoneIfTst, values_base: dict):
    # This test is a little overkill for none_if's that actually end up being
    # None, but so be it.
    m_key = K[len(V)]
    none_if = DnD.none_if(tst.value, tst.none_val, plug_in=tst.plug_in,
                          plug_out=tst.plug_out)

    # Test case to ensure if none_if is the first value, position is maintained.
    input1 = {m_key: none_if}
    input1.update(values_base)
    out1 = {m_key: tst.output} if tst.output is not None else {}
    out1.update(values_base)

    # Test case to ensure if none_if is neither the first nor last value,
    # position is maintained.
    bi = iter(values_base.items())
    k, v = next(bi)
    input2 = {k: v, m_key: none_if}
    out2 = {k: v}
    if tst.output is not None: out2[m_key] = tst.output  # noqa

    for k, v in bi:
        input2[k] = v
        out2[k] = v

    input3 = values_base.copy()
    input3[m_key] = none_if
    out3 = values_base.copy()
    if tst.output is not None: out3[m_key] = tst.output  # noqa

    return [(input1, out1), (input2, out2), (input3, out3)]


@pytest.fixture(params=[(LV, LV), (GV, None)],
                ids=['value != none_val', 'value == none_val'])
def simple_none_if_args(request):
    value, output = request.param
    return NoneIfTst(value=value, none_val=GV, plug_in=..., plug_out=...,
                     output=output)


@pytest.fixture(params=[
    (LLV, LV, GENERAL_PLUG_IN),
    (GV, None, GENERAL_PLUG_IN),
    (LV, GV, GENERAL_PLUG_IN),
    (LV, True, DIFFERENT_PLUG_IN),
    (GV, None, DIFFERENT_PLUG_IN)
], ids=['value != none_val',
        'value == none_val',
        "value != none_val (Doesn't Double Filter)",
        'value != none_val (Diff Type)',
        'value == none_val (Diff Type)'])
def plug_in_none_if_args(request):
    value, output, plug_in = request.param
    return NoneIfTst(value=value, none_val=GV, plug_in=plug_in, plug_out=...,
                     output=output)


@pytest.fixture(params=[
    (LLV, LV, (..., int), GENERAL_PLUG_OUT),
    (GV, None, (..., int), GENERAL_PLUG_OUT),
    (LV, GV, (..., int), GENERAL_PLUG_OUT),
    (LV, GV, (..., ...), GENERAL_PLUG_OUT),
    (GV, None, (..., ...), GENERAL_PLUG_OUT),
    (LV, True, (..., int), DIFFERENT_PLUG_OUT),
    (GV, None, (..., int), DIFFERENT_PLUG_OUT),
    (LV, True, (..., ...), DIFFERENT_PLUG_OUT),
    (GV, None, (..., ...), DIFFERENT_PLUG_OUT)
], ids=[
    'value != none_val (ValidPlugOut/int)',
    'value == none_val (ValidPlugOut/int)',
    "value != none_val (ValidPlugOut/int) (Doesn't Double Filter)",
    'value != none_val (ValidPlugOut/ValidPlugOut)',
    'value == none_val (ValidPlugOut/ValidPlugOut)',
    'value != none_val (ValidPlugOut/int) (Diff Type)',
    'value == none_val (ValidPlugOut/int) (Diff Type)',
    'value != none_val (ValidPlugOut/ValidPlugOut) (Diff Type)',
    'value == none_val (ValidPlugOut/ValidPlugOut) (Diff Type)'
])
def plug_out_none_if_args(request):
    value, output, types, plug_out = request.param

    class HasValidPlugOut:
        def __init__(self, value: int):
            self.value = value

        def __eq__(self, other: Union['HasValidPlugOut', int]) -> bool:
            if type(other) is int:
                return self.value == other

            return self.value == other.value

        def same_type_plug_out(self) -> int:
            return self.value + 1

        def different_type_plug_out(self) -> bool:
            return self.value < GV

    none_val = GV if types[1] is int else HasValidPlugOut(GV)
    if types[0] is not int:
        value = HasValidPlugOut(value)

    return NoneIfTst(value=value, none_val=none_val, plug_in=...,
                     plug_out=plug_out, output=output)


def test_none_if_later_creates_outside_of_dict_simple(simple_none_if_args):
    testy = DnD.none_if(simple_none_if_args.value, simple_none_if_args.none_val)
    assert isinstance(testy, DnD._NoneIfLater)
    assert testy.none_val == simple_none_if_args.none_val
    assert testy.value == simple_none_if_args.value
    assert testy.plug_in is ..., 'plug_in was not empty!'
    assert testy.plug_out is ..., 'plug_out was not empty!'


def test_none_if_later_creates_outside_of_dict_plug_in(plug_in_none_if_args):
    testy = DnD.none_if(plug_in_none_if_args.value,
                        plug_in_none_if_args.none_val,
                        plug_in=plug_in_none_if_args.plug_in)
    assert isinstance(testy, DnD._NoneIfLater)
    assert testy.none_val == plug_in_none_if_args.none_val
    assert testy.value == plug_in_none_if_args.value
    assert testy.plug_in is plug_in_none_if_args.plug_in
    assert testy.plug_out is ..., 'plug_out was not empty!'


def test_none_if_later_creates_outside_of_dict_plug_out(plug_out_none_if_args):
    testy = DnD.none_if(plug_out_none_if_args.value,
                        plug_out_none_if_args.none_val,
                        plug_out=plug_out_none_if_args.plug_out)
    assert isinstance(testy, DnD._NoneIfLater)
    assert testy.none_val == plug_out_none_if_args.none_val
    assert testy.value == plug_out_none_if_args.value
    assert testy.plug_in is ..., 'plug_in was not empty!'
    assert testy.plug_out is plug_out_none_if_args.plug_out


VF1 = 'none_if as first value failed!'
VF2 = 'none_if as second value failed!'
VF3 = 'none_if as last value failed!'


def test_none_if_later_works_in_dict_simple(simple_none_if_args,
                                            regular_values_base):
    tests = none_if_dicts(simple_none_if_args, regular_values_base)

    testy = DnD(tests[0][0])
    assert testy == tests[0][1], VF1

    testy = DnD(tests[1][0])
    assert testy == tests[1][1], VF2

    testy = DnD(tests[2][0])
    assert testy == tests[2][1], VF3


def test_none_if_later_works_in_dict_plug_in(plug_in_none_if_args,
                                             regular_values_base):
    tests = none_if_dicts(plug_in_none_if_args, regular_values_base)

    testy = DnD(tests[0][0])
    assert testy == tests[0][1], VF1

    testy = DnD(tests[1][0])
    assert testy == tests[1][1], VF2

    testy = DnD(tests[2][0])
    assert testy == tests[2][1], VF3


def test_none_if_later_works_in_dict_plug_out(plug_out_none_if_args,
                                              regular_values_base):
    tests = none_if_dicts(plug_out_none_if_args, regular_values_base)

    testy = DnD(tests[0][0])
    assert testy == tests[0][1], VF1

    testy = DnD(tests[1][0])
    assert testy == tests[1][1], VF2

    testy = DnD(tests[2][0])
    assert testy == tests[2][1], VF3
