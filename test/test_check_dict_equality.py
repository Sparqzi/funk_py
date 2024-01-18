from timeit import timeit
from typing import Union, Dict, List, Set, Tuple, Any

import pytest

from funk_py.modularity.type_matching import check_dict_equality


def too_slow(number: int, max_duration: float, l1, l2):
    duration = timeit(lambda: check_dict_equality(l1, l2), number=number)
    assert duration < max_duration, ('check_list_equality worked for two lists,'
                                     ' but did not perform adequately with'
                                     ' regards to speed. Lists compared'
                                     ' were:\n' + repr(l1) + '\n' + repr(l2)
                                     + '\n' + str(number) + ' iterations were'
                                     ' performed.')


G_STR1 = 'a'
G_STR2 = 'Gerd'
G_STR3 = 'Jerb'
B_STR1 = 'lorem'
IKS1 = 'ipsum'
IKS2 = 'dolor'

C_FALSY1 = []
C_FALSY2 = {}
C_FALSY3 = set()
C_FALSY4 = ''
C_FALSY5 = 0
C_FALSY6 = ()
C_FALSISH = '0'

C_TRUEY = 1
C_TRUEISH = '1'

G_INT1 = 80085
G_INT2 = 42
G_INT3 = 19
B_INT1 = 7
IKI1 = 432
IKI2 = 3025

G_FLT1 = 19.5
G_FLT2 = 94.999
G_FLT3 = 72.5556
B_FLT1 = 18.5
IKF1 = 13.2
IKF2 = 30.7777

# Make sure each set is the same length, otherwise there'll be issues with
# running tests. Exceptions may be made in "B" sets.

S_SET1 = (G_STR1, G_STR2, G_STR3)
# used for to construct dict with same key-value pairs, just in different order.
# Assures order-agnostic dict checks behave correctly.
S_SET2 = (G_STR2, G_STR3, G_STR1)
B_S_SET1 = (G_STR1, G_STR2, B_STR1)
B_S_SET2 = (G_STR1, G_STR2)

I_SET1 = (G_INT1, G_INT2, G_INT3)
# used for to construct dict with same key-value pairs, just in different order.
# Assures order-agnostic dict checks behave correctly.
I_SET2 = (G_INT2, G_INT3, G_INT1)
B_I_SET1 = (G_INT1, G_INT2, B_INT1)
B_I_SET2 = (G_INT1, G_INT2)

F_SET1 = (G_FLT1, G_FLT2, G_FLT3)
# used for to construct dict with same key-value pairs, just in different order.
# Assures order-agnostic dict checks behave correctly.
F_SET2 = (G_FLT2, G_FLT3, G_FLT1)
B_F_SET1 = (G_FLT1, G_FLT2, B_FLT1)
B_F_SET2 = (G_FLT1, G_FLT2)


@pytest.fixture(params=(S_SET1, I_SET1, F_SET1), ids=('str', 'int', 'flt'))
def normal_pair_keys(request):
    return request.param


@pytest.fixture(params=(S_SET1, I_SET1, F_SET1), ids=('str', 'int', 'flt'))
def normal_dicts(request, normal_pair_keys):
    return (dict(zip(normal_pair_keys, request.param)),
            dict(zip(normal_pair_keys, request.param)))


@pytest.fixture(params=((S_SET1, S_SET2), (I_SET1, I_SET2), (F_SET1, F_SET2)),
                ids=('str', 'int', 'flt'))
def same_but_diff_pair_keys(request):
    return request.param


@pytest.fixture(params=((S_SET1, S_SET2), (I_SET1, I_SET2), (F_SET1, F_SET2)),
                ids=('str', 'int', 'flt'))
def same_but_diff_dicts(request, same_but_diff_pair_keys):
    k1, k2 = same_but_diff_pair_keys
    v1, v2 = request.param
    return dict(zip(k1, v1)), dict(zip(k2, v2))


def test_normal_equal_dicts(normal_dicts):
    assert check_dict_equality(*normal_dicts)


def test_normal_diff_order_equal_dicts(same_but_diff_dicts):
    assert check_dict_equality(*same_but_diff_dicts)
    keys1, keys2 = (d.keys() for d in same_but_diff_dicts)

    # The following is meant to ensure that the dicts actually have different
    # orders of keys. If keys are in the same order, then the test is pointless.
    d_pos = False
    for i in range(len(keys1)):
        if keys1[i] != keys2[i]:
            d_pos = True
            break

    assert d_pos, ('The dicts compared in this test had all keys in the same'
                   ' order. This test cannot be trusted until the issue is'
                   ' rectified.')


SFT = {False: 'a', True: 'a'}
VSFT = {'a': False, 'b': True}


@pytest.fixture(params=((SFT, ((0, 'a'), (True, 'a')), False),
                        (SFT, ((False, 'a'), (1, 'a')), False),
                        (VSFT, (('a', 0), ('b', True)), True),
                        (VSFT, (('a', False), ('b', 1)), True)),
                ids=('key|0==False',
                     'key|1==True',
                     'val|0==False',
                     'val|1==True'))
def weird_aligned_dicts(request):
    return request.param[0], dict(request.param[1]), request.param[2]


def test_dict_equality_still_hates_true_and_false(weird_aligned_dicts):
    assert weird_aligned_dicts[0] == weird_aligned_dicts[1]
    if weird_aligned_dicts[2]:
        v1 = list(weird_aligned_dicts[0].values())
        v2 = list(weird_aligned_dicts[1].values())
        assert v1[0] is not v2[0] or v1[1] is not v2[1], \
            'Useless test detected, both keys are the same items in both dicts.'

    else:
        k1 = list(weird_aligned_dicts[0].keys())
        k2 = list(weird_aligned_dicts[1].keys())
        assert k1[0] is not k2[0] or k1[1] is not k2[1], \
            'Useless test detected, both keys are the same items in both dicts.'


def build_nested_dict(callbacks: Dict[int, dict] = None,
                      inner_callbacks: Set[int] = None,
                      *, base: Union[Tuple[tuple, ...], int],
                      callback: int = None,
                      key1: Any = None,
                      instruction1: dict = None,
                      key2: Any = None,
                      instruction2: dict = None):
    if callbacks is None:
        callbacks = {}
        inner_callbacks = set()

    if type(base) is int:
        inner_callbacks.add(base)
        return callbacks[base]

    builder = dict(base)
    if callback is not None:
        callbacks[callback] = builder

    if key1:
        builder[key1] = build_nested_dict(callbacks, inner_callbacks,
                                          **instruction1)

    if key2:
        builder[key2] = build_nested_dict(callbacks, inner_callbacks,
                                          **instruction2)

    return base





