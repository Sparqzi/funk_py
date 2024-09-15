import pytest

from test.t_support import build_nest
from funk_py.modularity.type_matching import check_dict_equality, strict_check_dict_equality

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

# Make sure each set is the same length, otherwise there'll be issues with running tests. Exceptions
# may be made in "B" sets.

S_SET1 = (G_STR1, G_STR2, G_STR3)
# used for to construct dict with same key-value pairs, just in different order. Assures
# order-agnostic dict checks behave correctly.
S_SET2 = (G_STR2, G_STR3, G_STR1)
B_S_SET1 = (G_STR1, G_STR2, B_STR1)
B_S_SET2 = (G_STR1, G_STR2)

I_SET1 = (G_INT1, G_INT2, G_INT3)
# used for to construct dict with same key-value pairs, just in different order. Assures
# order-agnostic dict checks behave correctly.
I_SET2 = (G_INT2, G_INT3, G_INT1)
B_I_SET1 = (G_INT1, G_INT2, B_INT1)
B_I_SET2 = (G_INT1, G_INT2)

F_SET1 = (G_FLT1, G_FLT2, G_FLT3)
# used for to construct dict with same key-value pairs, just in different order. Assures
# order-agnostic dict checks behave correctly.
F_SET2 = (G_FLT2, G_FLT3, G_FLT1)
B_F_SET1 = (G_FLT1, G_FLT2, B_FLT1)
B_F_SET2 = (G_FLT1, G_FLT2)


@pytest.fixture(params=(S_SET1, I_SET1, F_SET1), ids=('str', 'int', 'flt'))
def normal_pair_keys(request): return request.param


@pytest.fixture(params=(S_SET1, I_SET1, F_SET1), ids=('str', 'int', 'flt'))
def normal_dicts(request, normal_pair_keys):
    return dict(zip(normal_pair_keys, request.param)), dict(zip(normal_pair_keys, request.param))


@pytest.mark.benchmark
def test_normal_equal_dicts_benchmark(normal_dicts, benchmark):
    benchmark(check_dict_equality, *normal_dicts)
    benchmark(strict_check_dict_equality, *normal_dicts)


SFT = {False: 'a', True: 'a'}
VSFT = {'a': False, 'b': True}


SET1 = tuple(zip(S_SET1, I_SET1))
B_SET1 = tuple(zip(B_S_SET1, B_I_SET1))
SET2 = tuple(zip(S_SET2, I_SET2))
B_SET2 = tuple(zip(B_S_SET2, B_I_SET2))
SET3 = tuple(zip(F_SET1, S_SET1))
B_SET3 = tuple(zip(B_F_SET1, B_S_SET1))

TOP_NESTED_DICTS = (
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2)),
     'D1->(*,D2)', 100000, 0.5),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2),
          key2=IKI1,
          instruction2=dict(base=SET3)),
     'D1->(*,D2,D3)', 10000, 0.1),
    (dict(base=SET1,
          key1=IKF1,
          instruction1=dict(base=SET1)),
     'D1_1->(*,D1_2)', 10000, 0.3),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET1),
          key2=IKF1,
          instruction2=dict(base=SET1)),
     'D1_1->(*,D1_2,D1_3)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKI1,
          instruction1=dict(base=SET1),
          key2=IKI2,
          instruction2=dict(base=SET2)),
     'D1_1->(*,D1_2,D2)', 10000, 0.35)
)
BAD_TOP_NESTED_DICTS = (
    ((dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1)),
      dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=B_SET1))),
     'D1->(*,D2_1)!=D1->(*,D2_2)'),
    ((dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1)),
      dict(base=B_SET1,
           key1=IKS1,
           instruction1=dict(base=SET1))),
     'D1_1->(*,D2,*)!=D1_2->(*,D2,*)'),
    ((dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1),
           key2=IKI1,
           instruction2=dict(base=SET1)),
      dict(base=B_SET1,
           key1=IKS1,
           instruction1=dict(base=SET1),
           key2=IKI1,
           instruction2=dict(base=SET1))),
     'D1_1->(*,D2,D3)!=D1_2->(*,D2,D3)'),
    ((dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1),
           key2=IKI1,
           instruction2=dict(base=SET1)),
      dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1),
           key2=IKI1,
           instruction2=dict(base=B_SET1))),
     'D1->(*,D2,D3_1)!=L1->(*,D2,D3_2)'),
    ((dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=SET1),
           key2=IKI1,
           instruction2=dict(base=SET1)),
      dict(base=SET1,
           key1=IKS1,
           instruction1=dict(base=B_SET1),
           key2=IKI1,
           instruction2=dict(base=SET1))),
     'D1->(*,D2_1,D3)!=D1->(*,D2_2,D3)')
)

DOUBLE_NESTED_DICTS = (
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET3))),
     'D1->(*,D2->(*,D3))', 10000, 0.1),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI2,
                            instruction1=dict(base=SET3))),
     'D1->(*,D2->(*,D3))', 10000, 0.1),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET2))),
     'D1->(*,D2_1->(*,D2_2))', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET1))),
     'D1_1->(*,D2->(*,D1_2))', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET1,
                            key1=IKS1,
                            instruction1=dict(base=SET3))),
     'D1_1->(*,D1_2->(*,D3))', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET1,
                            key1=IKS1,
                            instruction1=dict(base=SET1))),
     'D1_1->(*,D1_2->(*,D1_3))', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET3)),
          key2=IKI2,
          instruction2=dict(base=SET3)),
     'D1->(*,D2->(*,D3_1),D3_2)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI2,
                            instruction1=dict(base=SET3)),
          key2=IKI2,
          instruction2=dict(base=SET3)),
     'D1->(*,D2->(*,D3_1),D3_2)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET2)),
          key2=IKI2,
          instruction2=dict(base=SET3)),
     'D1->(*,D2_1->(*,D2_2),D3)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET3)),
          key2=IKI2,
          instruction2=dict(base=SET2)),
     'D1->(*,D2_1->(*,D3),D2_2)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI2,
                            instruction1=dict(base=SET3)),
          key2=IKI2,
          instruction2=dict(base=SET2)),
     'D1->(*,D2_1->(*,D3),D2_2)', 10000, 0.15),
    (dict(base=SET1,
          key1=IKS1,
          instruction1=dict(base=SET2,
                            key1=IKI1,
                            instruction1=dict(base=SET2)),
          key2=IKI2,
          instruction2=dict(base=SET2)),
     'D1->(*,D2_1->(*,D2_2),D2_3)', 10000, 0.15)
)
BAD_DOUBLE_NESTED_DICTS = (
    ((dict(base=SET1,
           key1=IKI1,
           instruction1=dict(base=SET2,
                             key1=IKI1,
                             instruction1=dict(base=SET1))),
      dict(base=SET1,
           key1=IKI1,
           instruction1=dict(base=SET1,
                             key1=IKI1,
                             instruction1=dict(base=B_SET1)))),
     'D1->(*,D2->(*,D3_1))!=D1->(*,D2->(*,D3_2))'),
    ((dict(base=SET1,
           key1=IKI1,
           instruction1=dict(base=SET1,
                             key1=IKI1,
                             instruction1=dict(base=SET1))),
      dict(base=SET1,
           key1=IKI1,
           instruction1=dict(base=B_SET1,
                             key1=IKI1,
                             instruction1=dict(base=SET1)))),
     'D1->(*,D2_1->(*,D3))!=D1->(*,D2_2->(*,D3))'),
    ((dict(base=SET1,
           key1=IKI1,
           instruction1=dict(base=SET1,
                             key1=IKI1,
                             instruction1=dict(base=SET1))),
      dict(base=B_SET1,
           key1=IKI1,
           instruction1=dict(base=SET1,
                             key1=IKI1,
                             instruction1=dict(base=SET1)))),
     'D1_1->(*,D2->(*,D3))!=D1_2->(*,D2->(*,D3))')
)

NON_RECURSIVE_NESTED_DICTS = TOP_NESTED_DICTS + DOUBLE_NESTED_DICTS
BAD_NON_RECURSIVE_NESTED_DICTS = BAD_TOP_NESTED_DICTS + BAD_DOUBLE_NESTED_DICTS


@pytest.fixture(params=[(v[0], *v[2:]) for v in NON_RECURSIVE_NESTED_DICTS],
                ids=[v[1] for v in NON_RECURSIVE_NESTED_DICTS])
def nested_non_recursive_equal_dicts(request):
    # It is important that the lists returned are not the same exact list despite having same
    # values.
    return (build_nest(dict, **request.param[0]), build_nest(dict, **request.param[0]),
            *request.param[1:])


@pytest.fixture(params=[v[0] for v in BAD_NON_RECURSIVE_NESTED_DICTS],
                ids=[v[1] for v in BAD_NON_RECURSIVE_NESTED_DICTS])
def nested_non_recursive_unequal_dicts(request):
    d1, d2 = request.param
    return build_nest(dict, **d1), build_nest(dict, **d2)


@pytest.mark.benchmark
def test_nested_non_recursive_dict_equality_benchmark(nested_non_recursive_equal_dicts, benchmark):
    benchmark(check_dict_equality, *nested_non_recursive_equal_dicts[:2])
    benchmark(strict_check_dict_equality, *nested_non_recursive_equal_dicts[:2])


@pytest.mark.benchmark
def test_nested_non_recursive_dict_inequality_benchmark(
        nested_non_recursive_unequal_dicts,
        benchmark
):
    benchmark(check_dict_equality, *nested_non_recursive_unequal_dicts)
    benchmark(strict_check_dict_equality, *nested_non_recursive_unequal_dicts)


SIMPLE_RECURSIVE_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=1)),
    'D1->(*,D1)', 1
)
COPIED_RECURSIVE_DICT = (
    dict(base=SET1,
         key1=IKS1,
         instruction1=dict(base=SET1,
                           callback=1,
                           key1=IKS1,
                           instruction1=dict(base=1))),
    'D1_1->(*,D1_2->(*,D1_2))', 1
)

DOUBLE_TOP_LEVEL_RECURSIVE_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=1),
         key2=IKI1,
         instruction2=dict(base=1)),
    'D1->(*,D1,D1)', 1
)
COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=1),
         key2=IKI1,
         instruction2=dict(base=SET1,
                           callback=2,
                           key1=IKS1,
                           instruction1=dict(base=2),
                           key2=IKI1,
                           instruction2=dict(base=2))),
    'D1_1->(*,D1_1,D1_2->(*,D1_2,D1_2))', 1
)

LOWER_LEVEL_RECURSIVE_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=SET2,
                           key1=IKS2,
                           instruction1=dict(base=1))),
    'D1->(*,D2->(*,D1))', 1
)

DOUBLE_RECURSIVE_DIFF_LEVELS_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=1),
         key2=IKI1,
         instruction2=dict(base=SET2,
                           callback=2,
                           key1=IKS2,
                           instruction1=dict(base=2))),
    'D1->(*,D1,D2->(*,D2))', 1
)

DOUBLE_RECURSIVE_BOTTOM_LEVEL_DICT = (
    dict(base=SET1,
         callback=1,
         key1=IKS1,
         instruction1=dict(base=SET2,
                           callback=2,
                           key1=IKS2,
                           instruction1=dict(base=1),
                           key2=IKF1,
                           instruction2=dict(base=2))),
    'D1->(*,D2->(*,D1,D2))', 1
)

RECURSIVE_DICTS = (
    SIMPLE_RECURSIVE_DICT,
    DOUBLE_TOP_LEVEL_RECURSIVE_DICT,
    LOWER_LEVEL_RECURSIVE_DICT,
    DOUBLE_RECURSIVE_DIFF_LEVELS_DICT,
    DOUBLE_RECURSIVE_BOTTOM_LEVEL_DICT,
    COPIED_RECURSIVE_DICT,
    COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_DICT
)

DIFF_SIMPLE_RECURSIVE_DICT_SET = (
    (SIMPLE_RECURSIVE_DICT[0], COPIED_RECURSIVE_DICT[0]),
    'D1->(*,D1)!=D1_1->(*,D1_2->(*,D1_2))'
)
DIFF_DOUBLE_RECURSIVE_DICT_SET = (
    (DOUBLE_TOP_LEVEL_RECURSIVE_DICT[0],
     COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_DICT[0]),
    'D1->(*,D1,D1)!=D1_1->(*,D1_1,D1_2->(*,D1_2,D1_2))'
)


@pytest.fixture(params=[(v[0], v[2]) for v in RECURSIVE_DICTS],
                ids=[v[1] for v in RECURSIVE_DICTS])
def recursive_equal_dicts(request):
    d1 = build_nest(dict, **request.param[0])
    d2 = build_nest(dict, **request.param[0])
    return d1, d2, request.param[1]


@pytest.fixture(
    params=(DIFF_DOUBLE_RECURSIVE_DICT_SET[0],
            DIFF_SIMPLE_RECURSIVE_DICT_SET[0]),
    ids=(DIFF_DOUBLE_RECURSIVE_DICT_SET[1],
         DIFF_SIMPLE_RECURSIVE_DICT_SET[1]))
def recursive_unequal_dicts(request):
    l1 = build_nest(dict, **request.param[0])
    l2 = build_nest(dict, **request.param[1])
    return l1, l2


@pytest.mark.benchmark
def test_recursive_equality_benchmark(recursive_equal_dicts, benchmark):
    benchmark(check_dict_equality, *recursive_equal_dicts[:2])
    benchmark(strict_check_dict_equality, *recursive_equal_dicts[:2])


@pytest.mark.benchmark
def test_recursive_inequality_benchmark(recursive_unequal_dicts, benchmark):
    benchmark(check_dict_equality, *recursive_unequal_dicts)
    benchmark(strict_check_dict_equality, *recursive_unequal_dicts)
