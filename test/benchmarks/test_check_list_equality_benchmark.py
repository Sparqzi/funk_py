import pytest

from test.t_support import build_nest
from funk_py.modularity.type_matching import check_list_equality, strict_check_list_equality


G_STR1 = 'a'
G_STR2 = 'Gerd'
G_STR3 = 'Jerb'
B_STR1 = 'lorem'

C_FALSY1 = []  # sanity check
C_FALSY2 = {}  # sanity check
C_FALSY3 = set()  # sanity check
C_FALSY4 = ''  # sanity check
C_FALSY5 = 0  # actually necessary
C_FALSY6 = ()  # sanity check
C_FALSISH = '0'  # sanity check

FALSY_VALS = (C_FALSY1, C_FALSY2, C_FALSY3, C_FALSY4, C_FALSY6, C_FALSISH, None)

TRUTHY = 1  # actually necessary
C_TRUEISH = '1'  # sanity check

TRUTHY_VALS = (C_TRUEISH, ...)

G_INT1 = 80085
G_INT2 = 42
G_INT3 = 19
B_INT1 = 7

G_FLT1 = 19.5
G_FLT2 = 94.999
G_FLT3 = 72.5556
B_FLT1 = 18.5


STR_SET = (G_STR1, G_STR2, G_STR3)
B_STR_SET1 = (G_STR1, G_STR2, B_STR1)
B_STR_SET2 = (G_STR1, G_STR2)
INT_SET = (G_INT1, G_INT2, G_INT3)
B_INT_SET1 = (G_INT1, G_INT2, B_INT1)
B_INT_SET2 = (G_INT1, G_INT2)
FLT_SET = (G_FLT1, G_FLT2, G_FLT3)
B_FLT_SET1 = (G_FLT1, G_FLT2, B_FLT1)
B_FLT_SET2 = (G_FLT1, G_FLT2)

BOOL_SET = (False, True)
GEN_SET = (G_STR1, G_INT1, G_FLT1, True,
           G_STR2, G_INT2, G_FLT2, False,
           G_STR3, G_INT3, G_FLT3)

CONFUSED_SET1 = (False, True, C_FALSISH, C_TRUEISH, C_FALSY1, C_FALSY2, C_FALSY3, C_FALSY4,
                 C_FALSY5, C_FALSY6, TRUTHY, None, ...)
CONFUSED_SET2 = (False, True, C_FALSISH, C_TRUEISH, False, False, False, False, False, False,
                 TRUTHY, False, False)
CONFUSED_SET3 = (False, True, C_FALSISH, True, C_FALSY1, C_FALSY2, C_FALSY3, C_FALSY4, C_FALSY5,
                 C_FALSY6, True, None, ...)


GOOD_LISTS = (
    (STR_SET, 'only strings', 100000, 0.2),
    (INT_SET, 'only integers', 100000, 0.2),
    (FLT_SET, 'only floats', 100000, 0.15),
    (BOOL_SET, 'only booleans', 100000, 0.15),
    (GEN_SET, 'regular values', 10000, 0.15),
    (CONFUSED_SET1, 'iffy values', 100000, 0.5)
)
BAD_LISTS = (
    ((STR_SET, B_STR_SET1), 'only strings|val diff'),
    ((INT_SET, B_INT_SET1), 'only integers|val diff'),
    ((FLT_SET, B_FLT_SET1), 'only floats|val diff'),
    ((STR_SET, B_STR_SET2), 'only strings|len diff'),
    ((INT_SET, B_INT_SET2), 'only integers|len diff'),
    ((FLT_SET, B_FLT_SET2), 'only floats|len diff')
)


# -1 Means Append
# Indexes in GEN_SET:
INSERT_POINT1_1 = 5
INSERT_POINT1_2 = 7

# Indexes in INT_SET:
INSERT_POINT2_1 = 2
INSERT_POINT2_2 = -1

# Indexes in CONFUSED_SETs:
INSERT_POINT3_1 = 7
INSERT_POINT3_2 = 11


READ_IT = 'Did you read the comments above this test? You should have.'


def test_user_listened_to_comments():
    assert len(GEN_SET) > INSERT_POINT1_1 >= -1, READ_IT
    assert len(GEN_SET) > INSERT_POINT1_2 >= -1, READ_IT
    assert len(INT_SET) > INSERT_POINT2_1 >= -1, READ_IT
    assert len(INT_SET) > INSERT_POINT2_2 >= -1, READ_IT
    assert len(CONFUSED_SET1) > INSERT_POINT3_1 >= -1, READ_IT
    assert len(CONFUSED_SET1) > INSERT_POINT3_2 >= -1, READ_IT


@pytest.fixture(params=[(v[0], *v[2:]) for v in GOOD_LISTS], ids=[v[1] for v in GOOD_LISTS])
def regular_equal_lists(request):
    s = request.param
    # It is important that the lists returned are not the same exact list despite having same
    # values.
    l1 = list(s[0])
    l2 = list(s[0])
    return l1, l2, s[1], s[2]


@pytest.fixture(params=[v[0] for v in BAD_LISTS], ids=[v[1] for v in BAD_LISTS])
def regular_unequal_lists(request): return request.param


@pytest.mark.benchmark
def test_un_nested_list_equality_benchmark(regular_equal_lists, benchmark):
    benchmark(check_list_equality, *regular_equal_lists[:2])
    benchmark(strict_check_list_equality, *regular_equal_lists[:2])


@pytest.mark.benchmark
def test_un_nested_list_inequality_benchmark(regular_unequal_lists, benchmark):
    benchmark(check_list_equality, *regular_unequal_lists)
    benchmark(strict_check_list_equality, *regular_unequal_lists)


TOP_NESTED_LISTS = (
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET)),
     'L1->(*,L2,*)', 100000, 0.6),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=STR_SET)),
     'L1->(*,L2,*,L3,*)', 10000, 0.2),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET)),
     'L1_1->(*,L1_2,*)', 10000, 0.4),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=GEN_SET)),
     'L1_1->(*,L1_2,*,L1_3,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=INT_SET)),
     'L1_1->(*,L1_2,*,L2,*)', 10000, 0.45)
)
BAD_TOP_NESTED_LISTS = (
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET)),
      dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=B_INT_SET1))),
     'L1->(*,L2_1,*)!=L1->(*,L2_2,*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET)),
      dict(base=B_INT_SET1,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET))),
     'L1_1->(*,L2,*)!=L1_2->(*,L2,*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=INT_SET)),
      dict(base=B_INT_SET1,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=INT_SET))),
     'L1_1->(*,L2,*,L3,*)!=L1_2->(*,L2,*,L3,*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=INT_SET)),
      dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=B_INT_SET1))),
     'L1->(*,L2,*,L3_1,*)!=L1->(*,L2,*,L3_2,*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=INT_SET)),
      dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=B_INT_SET1),
           point2=INSERT_POINT2_2,
           instruction2=dict(base=INT_SET))),
     'L1->(*,L2_1,*,L3,*)!=L1->(*,L2_2,*,L3,*)')
)

DOUBLE_NESTED_LISTS = (
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=STR_SET))),
     'L1->(*,L2->(*,L3,*),*)', 10000, 0.2),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET))),
     'L1->(*,L2->(*,L3),*)', 10000, 0.2),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET))),
     'L1->(*,L2_1->(*,L2_2,*),*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=GEN_SET))),
     'L1_1->(*,L2->(*,L1_2,*),*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET,
                            point1=INSERT_POINT1_1,
                            instruction1=dict(base=STR_SET))),
     'L1_1->(*,L1_2->(*,L3,*),*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET,
                            point1=INSERT_POINT1_1,
                            instruction1=dict(base=GEN_SET))),
     'L1_1->(*,L1_2->(*,L1_3,*),*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=STR_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=STR_SET)),
     'L1->(*,L2->(*,L3_1,*),*,L3_2,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=STR_SET)),
     'L1->(*,L2->(*,L3_1),*,L3_2,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=STR_SET)),
     'L1->(*,L2_1->(*,L2_2,*),*,L3,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=STR_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L3,*),*,L2_2,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L3),*,L2_2,*)', 10000, 0.25),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET)),
          point2=INSERT_POINT2_2,
          instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L2_2,*),*,L2_3,*)', 10000, 0.25)
)
BAD_DOUBLE_NESTED_LISTS = (
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=INT_SET))),
      dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=B_INT_SET1)))),
     'L1->(*,L2->(*,L3_1,*),*)!=L1->(*,L2->(*,L3_2,*),*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=INT_SET))),
      dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=B_INT_SET1,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=INT_SET)))),
     'L1->(*,L2_1->(*,L3,*),*)!=L1->(*,L2_2->(*,L3,*),*)'),
    ((dict(base=INT_SET,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=INT_SET))),
      dict(base=B_INT_SET1,
           point1=INSERT_POINT2_1,
           instruction1=dict(base=INT_SET,
                             point1=INSERT_POINT2_1,
                             instruction1=dict(base=INT_SET)))),
     'L1_1->(*,L2->(*,L3,*),*)!=L1_2->(*,L2->(*,L3,*),*)')
)

NON_RECURSIVE_NESTED_LISTS = TOP_NESTED_LISTS + DOUBLE_NESTED_LISTS
BAD_NON_RECURSIVE_NESTED_LISTS = BAD_TOP_NESTED_LISTS + BAD_DOUBLE_NESTED_LISTS


@pytest.fixture(params=(tuple, list))
def types(request): return request.param


@pytest.fixture(params=[(v[0], *v[2:]) for v in NON_RECURSIVE_NESTED_LISTS],
                ids=[v[1] for v in NON_RECURSIVE_NESTED_LISTS])
def nested_non_recursive_equal_lists(request, types):
    # It is important that the lists returned are not the same exact list despite having same
    # values.
    return (build_nest(types, **request.param[0]), build_nest(types, **request.param[0]),
            *request.param[1:])


@pytest.fixture(params=[v[0] for v in BAD_NON_RECURSIVE_NESTED_LISTS],
                ids=[v[1] for v in BAD_NON_RECURSIVE_NESTED_LISTS])
def nested_non_recursive_unequal_lists(request, types):
    d1, d2 = request.param
    return build_nest(types, **d1), build_nest(types, **d2)


@pytest.mark.benchmark
def test_nested_non_recursive_list_equality_benchmark(nested_non_recursive_equal_lists, benchmark):
    benchmark(check_list_equality, *nested_non_recursive_equal_lists[:2])
    benchmark(strict_check_list_equality, *nested_non_recursive_equal_lists[:2])


@pytest.mark.benchmark
def test_nested_non_recursive_list_inequality_benchmark(
        nested_non_recursive_unequal_lists,
        benchmark
):
    benchmark(check_list_equality, *nested_non_recursive_unequal_lists)
    benchmark(strict_check_list_equality, *nested_non_recursive_unequal_lists)


NASTY_RECURSIVE_LIST = (
    dict(base=CONFUSED_SET1,
         callback=1,
         point1=INSERT_POINT3_1,
         instruction1=dict(base=1)),
    'L1->(*,L1,*)-nasty', 0.8
)
COPIED_NASTY_RECURSIVE_LIST = (
    dict(base=CONFUSED_SET1,
         point1=INSERT_POINT3_1,
         instruction1=dict(base=CONFUSED_SET1,
                           callback=1,
                           point1=INSERT_POINT3_1,
                           instruction1=dict(base=1))),
    'L1_1->(*,L1_2->(*,L1_2,*),*)-nasty', 1
)

SIMPLE_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1)),
    'L1->(*,L1,*)', 0.4
)
COPIED_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=GEN_SET,
                           callback=1,
                           point1=INSERT_POINT1_1,
                           instruction1=dict(base=1))),
    'L1_1->(*,L1_2->(*,L1_2,*),*)', 1
)

DOUBLE_TOP_LEVEL_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1),
         point2=INSERT_POINT1_2,
         instruction2=dict(base=1)),
    'L1->(*,L1,*,L1,*)', 0.85
)
COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1),
         point2=INSERT_POINT1_2,
         instruction2=dict(base=GEN_SET,
                           callback=2,
                           point1=INSERT_POINT1_1,
                           instruction1=dict(base=2),
                           point2=INSERT_POINT2_2,
                           instruction2=dict(base=2))),
    'L1_1->(*,L1_1,*,L1_2->(*,L1_2,*,L1_2,*),*)', 1.2
)

LOWER_LEVEL_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=INT_SET,
                           point1=INSERT_POINT2_1,
                           instruction1=dict(base=1))),
    'L1->(*,L2->(*,L1,*),*)', 0.6
)

DOUBLE_RECURSIVE_DIFF_LEVELS_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1),
         point2=INSERT_POINT1_2,
         instruction2=dict(base=INT_SET,
                           callback=2,
                           point1=INSERT_POINT2_1,
                           instruction1=dict(base=2))),
    'L1->(*,L1,*,L2->(*,L2,*),*)', 0.85
)

DOUBLE_RECURSIVE_BOTTOM_LEVEL_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=INT_SET,
                           callback=2,
                           point1=INSERT_POINT2_1,
                           instruction1=dict(base=1),
                           point2=INSERT_POINT2_2,
                           instruction2=dict(base=2))),
    'L1->(*,L2->(*,L1,*,L2),*)', 0.8
)

RECURSIVE_LISTS = (
    SIMPLE_RECURSIVE_LIST,
    DOUBLE_TOP_LEVEL_RECURSIVE_LIST,
    LOWER_LEVEL_RECURSIVE_LIST,
    DOUBLE_RECURSIVE_DIFF_LEVELS_LIST,
    DOUBLE_RECURSIVE_BOTTOM_LEVEL_LIST,
    COPIED_RECURSIVE_LIST,
    COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_LIST,
    NASTY_RECURSIVE_LIST,
    COPIED_NASTY_RECURSIVE_LIST
)

DIFF_SIMPLE_RECURSIVE_LIST_SET = (
    (SIMPLE_RECURSIVE_LIST[0], COPIED_RECURSIVE_LIST[0]),
    'L1->(*,L1,*)!=L1_1->(*,L1_2->(*,L1_2,*),*)'
)
DIFF_DOUBLE_RECURSIVE_LIST_SET = (
    (DOUBLE_TOP_LEVEL_RECURSIVE_LIST[0],
     COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_LIST[0]),
    'L1->(*,L1,*,L1,*)!=L1_1->(*,L1_1,*,L1_2->(*,L1_2,*,L1_2,*),*)'
)
DIFF_NASTY_RECURSIVE_LIST_SET = (
    (NASTY_RECURSIVE_LIST[0], COPIED_NASTY_RECURSIVE_LIST[0]),
    'L1->(*,L1,*)!=L1_1->(*,L1_2->(*,L1_2,*),*)-nasty'
)


@pytest.fixture(params=[(v[0], v[2]) for v in RECURSIVE_LISTS],
                ids=[v[1] for v in RECURSIVE_LISTS])
def recursive_equal_lists(request, types):
    l1 = build_nest(types, **request.param[0])
    l2 = build_nest(types, **request.param[0])
    return l1, l2, request.param[1]


@pytest.fixture(
    params=(DIFF_DOUBLE_RECURSIVE_LIST_SET[0],
            DIFF_SIMPLE_RECURSIVE_LIST_SET[0],
            DIFF_NASTY_RECURSIVE_LIST_SET[0]),
    ids=(DIFF_DOUBLE_RECURSIVE_LIST_SET[1],
         DIFF_SIMPLE_RECURSIVE_LIST_SET[1],
         DIFF_NASTY_RECURSIVE_LIST_SET[1]))
def recursive_unequal_lists(request, types):
    l1 = build_nest(types, **request.param[0])
    l2 = build_nest(types, **request.param[1])
    return l1, l2


@pytest.mark.benchmark
def test_recursive_equality_benchmark(recursive_equal_lists, benchmark):
    benchmark(check_list_equality, *recursive_equal_lists[:2])
    benchmark(strict_check_list_equality, *recursive_equal_lists[:2])


@pytest.mark.benchmark
def test_recursive_inequality_benchmark(recursive_unequal_lists, benchmark):
    benchmark(check_list_equality, *recursive_unequal_lists)
    benchmark(strict_check_list_equality, *recursive_unequal_lists)
