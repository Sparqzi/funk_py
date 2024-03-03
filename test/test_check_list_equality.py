import pytest

from t_support import build_nest, too_slow_func, cov, cov_counter
from funk_py.modularity.type_matching import check_list_equality, strict_check_list_equality


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


too_slow = too_slow_func('list')


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


def test_list_still_hates_true_and_false():
    assert [True] == [1]
    assert [False] == [0]

    assert (True,) == (1,)
    assert (False,) == (0,)


def test_non_strict_also_hates_true_and_false():
    assert check_list_equality([True], [1])
    assert check_list_equality([False], [0])

    assert check_list_equality((True,), (1,))
    assert check_list_equality((False,), (0,))


def test_strict_does_not_hate_true_and_false():
    assert not strict_check_list_equality([True], [1])
    assert not strict_check_list_equality([False], [0])

    assert not strict_check_list_equality((True,), (1,))
    assert not strict_check_list_equality((False,), (0,))


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


def test_un_nested_list_equality(regular_equal_lists):
    assert check_list_equality(*regular_equal_lists[:2])
    too_slow(1000000, 0.4, *regular_equal_lists[:2], check_list_equality)

    assert strict_check_list_equality(*regular_equal_lists[:2])
    too_slow(*regular_equal_lists[2:], *regular_equal_lists[:2], strict_check_list_equality)


def test_un_nested_list_inequality(regular_unequal_lists):
    assert not check_list_equality(*regular_unequal_lists)
    too_slow(1000000, 0.3, *regular_unequal_lists, check_list_equality)

    assert not strict_check_list_equality(*regular_unequal_lists)
    too_slow(1000000, 1.6, *regular_unequal_lists, strict_check_list_equality)


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


def test_nested_non_recursive_list_equality(nested_non_recursive_equal_lists):
    assert check_list_equality(*nested_non_recursive_equal_lists[:2])
    too_slow(1000000, 0.3, *nested_non_recursive_equal_lists[:2], check_list_equality)

    assert strict_check_list_equality(*nested_non_recursive_equal_lists[:2])
    too_slow(*nested_non_recursive_equal_lists[2:], *nested_non_recursive_equal_lists[:2],
             strict_check_list_equality)


def test_nested_non_recursive_list_inequality(nested_non_recursive_unequal_lists):
    assert not check_list_equality(*nested_non_recursive_unequal_lists)
    too_slow(1000000, 0.25, *nested_non_recursive_unequal_lists, check_list_equality)

    assert not strict_check_list_equality(*nested_non_recursive_unequal_lists)
    too_slow(1000000, 0.3, *nested_non_recursive_unequal_lists, strict_check_list_equality)


SHARING_LISTS = (
    (INSERT_POINT2_1, 'L1->(*,S1,*)'),
    (INSERT_POINT2_2, 'L1->(*,S1)')
)


@pytest.fixture(params=[v[0] for v in SHARING_LISTS], ids=[v[1] for v in SHARING_LISTS])
def nested_with_shared_equal_lists(request, types):
    point = request.param
    shared = types(INT_SET)
    if point == -1:
        l1 = list(INT_SET) + [shared]
        l2 = list(INT_SET) + [shared]

    else:
        l1 = list(INT_SET[:point]) + [shared] + list(INT_SET[point:])
        l2 = list(INT_SET[:point]) + [shared] + list(INT_SET[point:])

    return types(l1), types(l2)


@pytest.fixture(params=(
        (INSERT_POINT2_1, INSERT_POINT2_2),
        (INSERT_POINT2_2, INSERT_POINT2_1)
), ids=(
    'L1->(*,S1,*)!=L1->(*,S1)',
    'L1->(*,S1)!=L1->(*,S1,*)'
))
def nested_with_shared_unequal_lists(request, types):
    point1, point2 = request.param
    shared = types(INT_SET)
    l1 = list(INT_SET) + [shared] \
        if point1 == -1 \
        else list(INT_SET[:point1]) + [shared] + list(INT_SET[point1:])
    l2 = list(INT_SET) + [shared] \
        if point2 == -1 \
        else list(INT_SET[:point2]) + [shared] + list(INT_SET[point2:])

    return types(l1), types(l2)


def test_sharing_works(nested_with_shared_equal_lists):
    assert check_list_equality(*nested_with_shared_equal_lists)
    too_slow(1000000, 0.2, *nested_with_shared_equal_lists, check_list_equality)

    assert strict_check_list_equality(*nested_with_shared_equal_lists)
    too_slow(100000, 0.5, *nested_with_shared_equal_lists, strict_check_list_equality)


def test_no_false_pass_sharing(nested_with_shared_unequal_lists):
    assert not strict_check_list_equality(*nested_with_shared_unequal_lists)
    too_slow(1000000, 0.2, *nested_with_shared_unequal_lists, check_list_equality)

    assert not check_list_equality(*nested_with_shared_unequal_lists)
    too_slow(100000, 0.2, *nested_with_shared_unequal_lists, strict_check_list_equality)


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


@pytest.fixture(params=((True, 1), (False, 0)), ids=('True==1', 'False==0'))
def screwy_tests(request, types):
    v1, v2 = request.param
    l1 = [v1, [v1]]
    l1[1].append(l1[1])
    l2 = [v1, [v2]]
    l2[1].append(l2[1])
    return types(l1), types(l2)


# If for some reason Python makes it so that comparing recursive lists does not raise exceptions,
# then the function being tested here is useless.
def test_still_has_purpose(recursive_equal_lists):
    l1, l2, timeout = recursive_equal_lists
    with pytest.raises(RecursionError):
        # Your linter may dislike this line because "it has no side effects" It absolutely has
        # effects. It should always raise an exception.
        l1 == l2  # noqa


def test_recursive_equality(recursive_equal_lists):
    assert check_list_equality(*recursive_equal_lists[:2])
    too_slow(10000, recursive_equal_lists[2], *recursive_equal_lists[:2], check_list_equality)

    assert strict_check_list_equality(*recursive_equal_lists[:2])
    too_slow(10000, recursive_equal_lists[2], *recursive_equal_lists[:2],
             strict_check_list_equality)


def test_follows_rules_for_true_and_false(screwy_tests):
    assert check_list_equality(*screwy_tests)


def test_strict_not_follows_rules_for_true_and_false(screwy_tests):
    assert not strict_check_list_equality(*screwy_tests)


def test_recursive_inequality(recursive_unequal_lists):
    assert not check_list_equality(*recursive_unequal_lists)
    too_slow(10000, 0.6, *recursive_unequal_lists, check_list_equality)

    assert not strict_check_list_equality(*recursive_unequal_lists)
    too_slow(10000, 0.7, *recursive_unequal_lists, strict_check_list_equality)


@pytest.fixture(params=(1, 2), ids=('base as outer', 'base as inner'))
def confused_recursive_list_positions(request):
    return request.param


@pytest.fixture(params=FALSY_VALS)
def confused_unequal_falsy_recursive_lists(request, types, confused_recursive_list_positions):
    s1 = (True, False, request.param)
    s2 = (True, False, False)
    ip = 1

    l1 = build_nest(types,
                    base=s1,
                    point1=ip,
                    instruction1=dict(base=s1,
                                      callback=1,
                                      point1=ip,
                                      instruction1=dict(base=1)))
    if confused_recursive_list_positions == 1:
        l2 = build_nest(types,
                        base=s1,
                        point1=ip,
                        instruction1=dict(base=s2,
                                          callback=1,
                                          point1=ip,
                                          instruction1=dict(base=1)))

    else:
        l2 = build_nest(types,
                        base=s2,
                        point1=ip,
                        instruction1=dict(base=s1,
                                          callback=1,
                                          point1=ip,
                                          instruction1=dict(base=1)))

    return l1, l2


@pytest.fixture(params=TRUTHY_VALS)
def confused_unequal_truthy_recursive_lists(request, types, confused_recursive_list_positions):
    s1 = (True, False, request.param)
    s2 = (True, False, True)
    ip = 1

    l1 = build_nest(types,
                    base=s1,
                    point1=ip,
                    instruction1=dict(base=s1,
                                      callback=1,
                                      point1=ip,
                                      instruction1=dict(base=1)))
    if confused_recursive_list_positions == 1:
        l2 = build_nest(types,
                        base=s1,
                        point1=ip,
                        instruction1=dict(base=s2,
                                          callback=1,
                                          point1=ip,
                                          instruction1=dict(base=1)))

    else:
        l2 = build_nest(types,
                        base=s2,
                        point1=ip,
                        instruction1=dict(base=s1,
                                          callback=1,
                                          point1=ip,
                                          instruction1=dict(base=1)))

    return l1, l2


@pytest.mark.timeout(2)
def test_confused_falsy_recursive_inequality(confused_unequal_falsy_recursive_lists):
    assert not check_list_equality(*confused_unequal_falsy_recursive_lists)
    too_slow(10000, 0.6, *confused_unequal_falsy_recursive_lists, check_list_equality)

    assert not strict_check_list_equality(*confused_unequal_falsy_recursive_lists)
    too_slow(10000, 0.7, *confused_unequal_falsy_recursive_lists, strict_check_list_equality)


@pytest.mark.timeout(2)
def test_confused_truthy_recursive_inequality(confused_unequal_truthy_recursive_lists):
    assert not check_list_equality(*confused_unequal_truthy_recursive_lists)
    too_slow(10000, 0.6, *confused_unequal_truthy_recursive_lists, check_list_equality)

    assert not strict_check_list_equality(*confused_unequal_truthy_recursive_lists)
    too_slow(10000, 0.7, *confused_unequal_truthy_recursive_lists, strict_check_list_equality)
