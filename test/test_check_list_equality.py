from typing import Union, Dict, List, Set

import pytest

from funk_py.modularity.type_matching import check_list_equality


G_STR1 = 'a'
G_STR2 = 'Gerd'
G_STR3 = 'Jerb'
B_STR1 = 'lorem'

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

CONFUSED_SET1 = (False, True, C_FALSISH, C_TRUEISH,
                 C_FALSY1, C_FALSY2, C_FALSY3, C_FALSY4, C_FALSY5, C_FALSY6,
                 C_TRUEY, None, ...)
CONFUSED_SET2 = (False, True, C_FALSISH, C_TRUEISH,
                 False, False, False, False, False, False,
                 C_TRUEY, False, False)
CONFUSED_SET3 = (False, True, C_FALSISH, True,
                 C_FALSY1, C_FALSY2, C_FALSY3, C_FALSY4, C_FALSY5, C_FALSY6,
                 True, None, ...)


GOOD_LISTS = (
    (STR_SET, 'only strings'),
    (INT_SET, 'only integers'),
    (FLT_SET, 'only floats'),
    (BOOL_SET, 'only booleans'),
    (GEN_SET, 'regular values'),
    (CONFUSED_SET1, 'iffy values')
)
BAD_LISTS = (
    ((STR_SET, B_STR_SET1), 'only strings|val diff'),
    ((INT_SET, B_INT_SET1), 'only integers|val diff'),
    ((FLT_SET, B_FLT_SET1), 'only floats|val diff'),
    ((STR_SET, B_STR_SET2), 'only strings|len diff'),
    ((INT_SET, B_INT_SET2), 'only integers|len diff'),
    ((FLT_SET, B_FLT_SET2), 'only floats|len diff')
)


@pytest.fixture(params=[v[0] for v in GOOD_LISTS],
                ids=[v[1] for v in GOOD_LISTS])
def regular_equal_lists(request):
    s = request.param
    # It is important that the lists returned are not the same exact list
    # despite having same values.
    l1 = list(s)
    l2 = list(s)
    return l1, l2


@pytest.fixture(params=[v[0] for v in BAD_LISTS],
                ids=[v[1] for v in BAD_LISTS])
def regular_unequal_lists(request):
    return request.param


def test_un_nested_list_equality(regular_equal_lists):
    assert check_list_equality(*regular_equal_lists)


def test_un_nested_list_inequality(regular_unequal_lists):
    assert not check_list_equality(*regular_unequal_lists)


# -1 Means Append
# Indexes in GEN_SET:
INSERT_POINT1_1 = 5
INSERT_POINT1_2 = 7

# Indexes in INT_SET:
INSERT_POINT2_1 = 2
INSERT_POINT2_2 = -1


TOP_NESTED_LISTS = (
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET)), 'L1->(*,L2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=STR_SET)), 'L1->(*,L2,*,L3,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET)), 'L1_1->(*,L1_2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=GEN_SET)), 'L1_1->(*,L1_2,*,L1_3,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET),
          point2=INSERT_POINT1_2,
          instruction2=dict(base=INT_SET)), 'L1_1->(*,L1_2,*,L2,*)')
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
     'L1->(*,L2->(*,L3,*),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET))),
     'L1->(*,L2->(*,L3),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET))),
     'L1->(*,L2_1->(*,L2_2,*),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=GEN_SET))),
     'L1_1->(*,L2->(*,L1_2,*),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET,
                            point1=INSERT_POINT1_1,
                            instruction1=dict(base=STR_SET))),
     'L1_1->(*,L1_2->(*,L3,*),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=GEN_SET,
                            point1=INSERT_POINT1_1,
                            instruction1=dict(base=GEN_SET))),
     'L1_1->(*,L1_2->(*,L1_3,*),*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=STR_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=STR_SET)),
     'L1->(*,L2->(*,L3_1,*),*,L3_2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=STR_SET)),
     'L1->(*,L2->(*,L3_1),*,L3_2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=STR_SET)),
     'L1->(*,L2_1->(*,L2_2,*),*,L3,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=STR_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L3,*),*,L2_2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_2,
                            instruction1=dict(base=STR_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L3),*,L2_2,*)'),
    (dict(base=GEN_SET,
          point1=INSERT_POINT1_1,
          instruction1=dict(base=INT_SET,
                            point1=INSERT_POINT2_1,
                            instruction1=dict(base=INT_SET)),
                            point2=INSERT_POINT2_2,
                            instruction2=dict(base=INT_SET)),
     'L1->(*,L2_1->(*,L2_2,*),*,L2_3,*)')
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


def build_nested_sequence(type_: type,
                          callbacks: Dict[int, Union[tuple, list]] = None,
                          inner_callbacks: Set[int] = None,
                          *, base: Union[tuple, int],
                          callback: int = None,
                          point1: int = None,
                          instruction1: dict = None,
                          point2: int = None,
                          instruction2: dict = None):
    if callbacks is None:
        callbacks = {}
        inner_callbacks = set()

    if type(base) is int:
        inner_callbacks.add(base)
        return callbacks[base]

    if point1:
        builder = list(base[:point1])
        if callback is not None:
            callbacks[callback] = builder

        builder.append(
            build_nested_sequence(type_, callbacks, inner_callbacks,
                                  **instruction1))
        if point2:
            if point2 == -1:
                builder.extend(base[point1:])
                builder.append(
                    build_nested_sequence(type_, callbacks, inner_callbacks,
                                          **instruction2))

            else:
                builder.extend(base[point1:point2])
                builder.append(
                    build_nested_sequence(type_, callbacks, inner_callbacks,
                                          **instruction2))
                builder.extend(base[point2:])

        else:
            builder.extend(base[point1:])

        if callback is not None and callback in inner_callbacks:
            return builder

        return type_(builder)

    if callback is not None:
        callbacks[callback] = type_(base)

    return type_(base)


@pytest.fixture(params=(tuple, list))
def types(request):
    return request.param


@pytest.fixture(params=[v[0] for v in NON_RECURSIVE_NESTED_LISTS],
                ids=[v[1] for v in NON_RECURSIVE_NESTED_LISTS])
def nested_non_recursive_equal_lists(request, types):
    # It is important that the lists returned are not the same exact list
    # despite having same values.
    return (build_nested_sequence(types, **request.param),
            build_nested_sequence(types, **request.param))


@pytest.fixture(params=[v[0] for v in BAD_NON_RECURSIVE_NESTED_LISTS],
                ids=[v[1] for v in BAD_NON_RECURSIVE_NESTED_LISTS])
def nested_non_recursive_unequal_lists(request, types):
    d1, d2 = request.param
    return (build_nested_sequence(types, **d1),
            build_nested_sequence(types, **d2))


def test_nested_non_recursive_list_equality(nested_non_recursive_equal_lists):
    assert check_list_equality(*nested_non_recursive_equal_lists)


def test_nested_non_recursive_list_inequality(
        nested_non_recursive_unequal_lists):
    assert not check_list_equality(*nested_non_recursive_unequal_lists)


SHARING_LISTS = (
    (INSERT_POINT2_1, 'L1->(*,S1,*)'),
    (INSERT_POINT2_2, 'L1->(*,S1)')
)


@pytest.fixture(params=[v[0] for v in SHARING_LISTS],
                ids=[v[1] for v in SHARING_LISTS])
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
        (INSERT_POINT2_2, INSERT_POINT2_1)), ids=(
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


def test_no_false_pass_sharing(nested_with_shared_unequal_lists):
    assert not check_list_equality(*nested_with_shared_unequal_lists)


SIMPLE_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1)),
    'L1->(*,L1,*)'
)
COPIED_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=GEN_SET,
                           callback=1,
                           point1=INSERT_POINT1_1,
                           instruction1=dict(base=1))),
    'L1_1->(*,L1_2->(*,L1_2,*),*)'
)

DOUBLE_TOP_LEVEL_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=1),
         point2=INSERT_POINT1_2,
         instruction2=dict(base=1)),
    'L1->(*,L1,*,L1,*)'
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
    'L1_1->(*,L1_1,*,L1_2->(*,L1_2,*,L1_2,*),*)'
)

LOWER_LEVEL_RECURSIVE_LIST = (
    dict(base=GEN_SET,
         callback=1,
         point1=INSERT_POINT1_1,
         instruction1=dict(base=INT_SET,
                           point1=INSERT_POINT2_1,
                           instruction1=dict(base=1))),
    'L1->(*,L2->(*,L1,*),*)'
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
    'L1->(*,L1,*,L2->(*,L2,*),*)'
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
    'L1->(*,L2->(*,L1,*,L2),*)'
)

RECURSIVE_LISTS = (
    SIMPLE_RECURSIVE_LIST,
    DOUBLE_TOP_LEVEL_RECURSIVE_LIST,
    LOWER_LEVEL_RECURSIVE_LIST,
    DOUBLE_RECURSIVE_DIFF_LEVELS_LIST,
    DOUBLE_RECURSIVE_BOTTOM_LEVEL_LIST,
    COPIED_RECURSIVE_LIST,
    COPIED_DOUBLE_TOP_LEVEL_RECURSIVE_LIST
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


@pytest.fixture(params=[v[0] for v in RECURSIVE_LISTS],
                ids=[v[1] for v in RECURSIVE_LISTS])
def recursive_equal_lists(request, types):
    l1 = build_nested_sequence(types, **request.param)
    l2 = build_nested_sequence(types, **request.param)
    return l1, l2


@pytest.fixture(
    params=(DIFF_DOUBLE_RECURSIVE_LIST_SET[0],
            DIFF_SIMPLE_RECURSIVE_LIST_SET[0]),
    ids=(DIFF_DOUBLE_RECURSIVE_LIST_SET[1], DIFF_SIMPLE_RECURSIVE_LIST_SET[1]))
def recursive_unequal_lists(request, types):
    l1 = build_nested_sequence(types, **request.param[0])
    l2 = build_nested_sequence(types, **request.param[1])
    return l1, l2


# If for some reason Python makes it so that comparing recursive lists does not
# raise exceptions, then the function being tested here is useless.
def test_still_has_purpose(recursive_equal_lists):
    l1, l2 = recursive_equal_lists
    with pytest.raises(RecursionError) as info:
        # Your linter may dislike this line because "it has no side effects"
        # It absolutely has side effects. It should always raise an exception.
        if l1 == l2:
            print('Yay!')

    assert 'maximum recursion' in str(info.value), \
        ('A purpose check has failed. If all checks fail, Python may have'
         ' implemented recursion safety in list comparison.')


def test_recursive_equality(recursive_equal_lists):
    assert check_list_equality(*recursive_equal_lists)


def test_recursive_inequality(recursive_unequal_lists):
    assert not check_list_equality(*recursive_unequal_lists)
