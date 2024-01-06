from warnings import warn
from typing import Any, Dict

from funk_py.modularity.type_matching import (check_function_equality,
                                              hash_function)

import pytest


# If this appears to be broken, please step through, reading the comments
# carefully. At the time this is written, this can only be replaced if EVERY
# equality is hard-coded in. This function seems safer than allowing that many
# opportunities to make mistakes, and does not rely on anything known to be on a
# deprecation path.
def parse_eq_dict(dict_: Dict[Any, list]) -> Dict[Any, list]:
    """
    Equality should always be two-way. This function constructs a lookup for
    equality checks from a much shorter input in order to lessen the amount that
    must be written.
    """
    user_is_monkey = []
    holder = []
    for key, vals1 in dict_.items():
        # This next part simply searches existing lists of equivalencies from
        # prior steps to verify if the key or any current values are already
        # equated to something. This is because the user is assumed to be
        # human/imperfect.
        if (not all(key not in vals2
                    for vals2 in holder)
                or not all(all(val not in vals2
                               for vals2 in holder)
                           for val in vals1)):
            # Constructs a list of any values already found elsewhere.
            copied_vals = [val
                           for val in vals1
                           if any(val in vals2
                                  for vals2 in holder)]
            if any(key in vals2
                      for vals2 in holder) and key not in copied_vals:
                copied_vals.append(key)

            # Save for later to tell the user an error is suspected in their
            # input. This should only be a warning in case someone actually
            # meant to do this.
            user_is_monkey.append((key, copied_vals))

            lists_to_combine = []
            for val in copied_vals:
                for vals2 in holder:
                    if vals2 not in lists_to_combine and val in vals2:
                        lists_to_combine.append(vals2)

            new_list = [key]
            # Do not assume the user has no duplicate values in the list.
            for val in vals1:
                if val not in new_list:
                    new_list.append(val)

            for vals2 in lists_to_combine:
                for val in vals2:
                    # There will definitely be duplicates in these...
                    if val not in new_list:
                        new_list.append(val)

            # We should delete the lists we found values in from the holder so
            # that they...
            # A: Do not cause more false positives.
            # B: Do not lead us to generate the end lookup incorrectly by
            #    overwriting equivalencies.
            # Iterate backwards using indexes to avoid errors/mistaken
            # deletions.
            for i in range(len(holder) - 1, -1, -1):
                if holder[i] in lists_to_combine:
                    del holder[i]

        else:
            new_list = [key]
            # Do not assume the user has no duplicate values in the list.
            for val in vals1:
                if val not in new_list:
                    new_list.append(val)

            holder.append(new_list)

        # The following simply checks if there are somehow competing lists. If
        # there ever are competing lists at this point, something in this
        # function is broken. A fail to pass meet this criteria means we cannot
        # guarantee the user that the correct tests are being run.
        for i1 in range(len(holder) - 1):
            vals2 = holder[i1]
            if any(val in vals3 for vals3 in holder[i1 + 1:] for val in vals2):
                assert False, ("I don't know how, but something is broken"
                               " within 'parse_eq_dict'. A value ended up in"
                               " multiple equivalence lists during processing.")

    if user_is_monkey:
        warn(f"You fool. You absolute buffoon. You think you're clever? I think"
             f" you don't realize the magnitude of your mistake...\n"
             f"The list you gave me has a value's equality defined after it was"
             f" already set equal to something else. In case you actually meant"
             f" to do this, I went back and applied the changes recursively to"
             f" all equated values. Still, I advise you look at your input in"
             f" case there's a typo.\n"
             f"Offending values were: {repr(user_is_monkey)}", UserWarning)

    # Now, we can create the lookup! It is done this way to speed lookup during
    # testing.
    builder = {}
    for vals in holder:
        for val in vals:
            builder[val] = vals

    return builder


# ==================================================================================================
# Functions For Testing When Arguments Have Different Types
# As Well As For Texting Different Types of Method Declarations
# ==================================================================================================
# We want to minimize use of the constant pool in ID-ing functions, do not
# define a function to get called by all the functions below.

def func_type1_1_1(arg1: str):
    return f'{arg1}-1'


def func_type1_1_2(arg1_: int):
    return f'{arg1_}-1'

# Lambda to make sure it is ID'd right
func_type1_1_3 = lambda x: f'{x}-1'  # noqa


def func_type1_2_1(arg1__: str):
    return arg1__ + arg1__


def func_type1_2_2(arg1___: int):
    return arg1___ + arg1___


# Lambda to make sure it is ID'd right
func_type1_2_3 = lambda x: x + x # noqa


# For verifying that static methods in classes get ID'd the same
class FuncType1ClassVersions:
    @staticmethod
    def func_type1_1_1(arg1: str):
        return f'{arg1}-1'

    @staticmethod
    def func_type1_1_2(arg1_: int):
        return f'{arg1_}-1'

    func_type1_1_3 = lambda x: f'{x}-1'  # noqa

    @staticmethod
    def func_type1_2_1(arg1__: str):
        return arg1__ + arg1__

    @staticmethod
    def func_type1_2_2(arg1___: int):
        return arg1___ + arg1___

    func_type1_2_3 = lambda x: x + x  # noqa


FUNC_TYPE1_1_1 = 'func-type1-1-1'
FUNC_TYPE1_1_2 = 'func-type1-1-2'
FUNC_TYPE1_1_3 = 'func-type1-1-3'
FUNC_TYPE1_2_1 = 'func-type1-2-1'
FUNC_TYPE1_2_2 = 'func-type1-2-2'
FUNC_TYPE1_2_3 = 'func-type1-2-3'


def func_type1_local_version(func: str):
    def _func_type1_1_1(arg1: str):
        return f'{arg1}-1'

    def _func_type1_1_2(arg1_: int):
        return f'{arg1_}-1'

    # Lambda to make sure it is ID'd right
    _func_type1_1_3 = lambda x: f'{x}-1'  # noqa

    def _func_type1_2_1(arg1__: str):
        return arg1__ + arg1__

    def _func_type1_2_2(arg1___: int):
        return arg1___ + arg1___

    # Lambda to make sure it is ID'd right
    _func_type1_2_3 = lambda x: x + x  # noqa

    return {
        FUNC_TYPE1_1_1: _func_type1_1_1,
        FUNC_TYPE1_1_2: _func_type1_1_2,
        FUNC_TYPE1_1_3: _func_type1_1_3,
        FUNC_TYPE1_2_1: _func_type1_2_1,
        FUNC_TYPE1_2_2: _func_type1_2_2,
        FUNC_TYPE1_2_3: _func_type1_2_3
    }[func]


REG = 'regular'
REG_LAMBDA = 'regular lambda'
LOCAL = 'local'
LOCAL_LAMBDA = 'local lambda'
STATIC_CLASS = 'static class method'
CLASS_LAMBDA = 'lambda defined in class'


def construct_func_type1_desc(type_: type, variant: Any, func_type: str):
    return (f'Param Type: {type_}, Code Variant: {variant},'
            f' Function Type: {func_type}')


FUNC_TYPE1_PAIRS = (
    (func_type1_1_1, construct_func_type1_desc(str, 1, REG), 1),
    (func_type1_1_2, construct_func_type1_desc(int, 1, REG), 1),
    (func_type1_1_3, construct_func_type1_desc(Any, 1, REG_LAMBDA), 1),
    (FuncType1ClassVersions.func_type1_1_1,
     construct_func_type1_desc(str, 1, STATIC_CLASS), 1),
    (FuncType1ClassVersions.func_type1_1_2,
     construct_func_type1_desc(int, 1, STATIC_CLASS), 1),
    (FuncType1ClassVersions.func_type1_1_3,
     construct_func_type1_desc(Any, 1, CLASS_LAMBDA), 1),
    (func_type1_local_version(FUNC_TYPE1_1_1),
     construct_func_type1_desc(str, 1, LOCAL), 1),
    (func_type1_local_version(FUNC_TYPE1_1_2),
     construct_func_type1_desc(int, 1, LOCAL), 1),
    (func_type1_local_version(FUNC_TYPE1_1_3),
     construct_func_type1_desc(Any, 1, LOCAL_LAMBDA), 1),
    (func_type1_2_1, construct_func_type1_desc(str, 2, REG), 2),
    (func_type1_2_2, construct_func_type1_desc(int, 2, REG), 2),
    (func_type1_2_3, construct_func_type1_desc(Any, 2, REG_LAMBDA), 2),
    (FuncType1ClassVersions.func_type1_2_1,
     construct_func_type1_desc(str, 2, STATIC_CLASS), 2),
    (FuncType1ClassVersions.func_type1_2_2,
     construct_func_type1_desc(int, 2, STATIC_CLASS), 2),
    (FuncType1ClassVersions.func_type1_2_3,
     construct_func_type1_desc(Any, 2, CLASS_LAMBDA), 2),
    (func_type1_local_version(FUNC_TYPE1_2_1),
     construct_func_type1_desc(str, 2, LOCAL), 2),
    (func_type1_local_version(FUNC_TYPE1_2_2),
     construct_func_type1_desc(int, 2, LOCAL), 2),
    (func_type1_local_version(FUNC_TYPE1_2_3),
     construct_func_type1_desc(Any, 2, LOCAL_LAMBDA), 2)
)

# As of the time of this comment, the expected behavior of hashing these
# functions is for all of them to be equivalent.
FUNC_TYPE1_EQ_HASH = parse_eq_dict(
    {func_type1_1_1: [p[0] for p in FUNC_TYPE1_PAIRS]})
# equality checks, not so much.
FUNC_TYPE1_EQ_EQ = parse_eq_dict({
    func_type1_1_1: [p[0] for p in FUNC_TYPE1_PAIRS if p[2] == 1],
    func_type1_2_1: [p[0] for p in FUNC_TYPE1_PAIRS if p[2] == 2]
})


@pytest.fixture(params=[p[0] for p in FUNC_TYPE1_PAIRS],
                ids=[p[1] for p in FUNC_TYPE1_PAIRS])
def func_type1_funcs1(request):
    return request.param


@pytest.fixture(params=[p[0] for p in FUNC_TYPE1_PAIRS],
                ids=[' <--> ' + p[1] for p in FUNC_TYPE1_PAIRS])
def func_type1_funcs2(request):
    return request.param


@pytest.fixture
def func_type1_hashes(func_type1_funcs1, func_type1_funcs2):
    return (func_type1_funcs1, func_type1_funcs2,
            func_type1_funcs2 in FUNC_TYPE1_EQ_HASH[func_type1_funcs1])


@pytest.fixture
def func_type1_eqs(func_type1_funcs1, func_type1_funcs2):
    return (func_type1_funcs1, func_type1_funcs2,
            func_type1_funcs2 in FUNC_TYPE1_EQ_EQ[func_type1_funcs1])


def test_func_types_and_variants_hash(func_type1_hashes):
    func1, func2, should_equal = func_type1_hashes
    hash1 = hash_function(func1)
    hash2 = hash_function(func2)
    if should_equal:
        assert hash1 == hash2

    else:
        assert hash1 != hash2


def test_func_types_and_variants_equal(func_type1_eqs):
    func1, func2, should_equal = func_type1_eqs
    if should_equal:
        assert check_function_equality(func1, func2)

    else:
        assert not check_function_equality(func1, func2)


# ==================================================================================================
# Functions For Testing When Arguments Have Defaults
# ==================================================================================================
# We want to minimize use of the constant pool's impact in ID-ing functions, do
# not define a function to get called by all the functions below.

D1G = 15
D2G = 12
D1B = 16
D2B = 10


def func_type2_1(arg1, arg2):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_2(arg1, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_2(arg1, arg2=D2B):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_3(arg1=D1G, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_3_1(arg1=D1G, arg2=D2B):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_3_2(arg1=D1B, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_4(arg1, arg2, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_5(arg1, arg2=D2G, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_5(arg1, arg2=D2B, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_6(arg1=D1G, arg2=D2G, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_6_1(arg1=D1G, arg2=D2B, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_6_2(arg1=D1B, arg2=D2G, /):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_7(*, arg1, arg2):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_8(*, arg1, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_8(*, arg1, arg2=D2B):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def func_type2_9(*, arg1=D1G, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_9_1(*, arg1=D1G, arg2=D2B):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


def false_func_type2_9_2(*, arg1=D1B, arg2=D2G):
    return str(arg1 * arg2) + f'-{arg2}-{arg1}'


# --------------------------------------------------------------------------------------------------
# Test Fixtures
# --------------------------------------------------------------------------------------------------
POS_ONLY = 'pos-only'
KW_ONLY = 'keyword-only'


# default1 and default2 are reversed because of restrictions on default
# arguments which prevent arg1 from ever having a default if arg2 doesn't
def construct_func_type2_desc(arg_type: str, default2: int = 'N/A',
                              default1: int = 'N/A'):
    return (f'Arguments Type: {arg_type}, arg1 Default: {default1},'
            f' arg2 Default: {default2}')


FUNC_TYPE2_PAIRS = (
    (func_type2_1, construct_func_type2_desc(REG)),
    (func_type2_2, construct_func_type2_desc(REG, D2G)),
    (false_func_type2_2, construct_func_type2_desc(REG, D2B)),
    (func_type2_3, construct_func_type2_desc(REG, D2G, D1G)),
    (false_func_type2_3_1, construct_func_type2_desc(REG, D2B, D1G)),
    (false_func_type2_3_2, construct_func_type2_desc(REG, D2G, D1B)),
    (func_type2_4, construct_func_type2_desc(POS_ONLY)),
    (func_type2_5, construct_func_type2_desc(POS_ONLY, D2G)),
    (false_func_type2_5, construct_func_type2_desc(POS_ONLY, D2B)),
    (func_type2_6, construct_func_type2_desc(POS_ONLY, D2G)),
    (false_func_type2_6_1, construct_func_type2_desc(POS_ONLY, D2B, D1G)),
    (false_func_type2_6_2, construct_func_type2_desc(POS_ONLY, D2G, D1B)),
    (func_type2_7, construct_func_type2_desc(KW_ONLY)),
    (func_type2_8, construct_func_type2_desc(KW_ONLY, D2G)),
    (false_func_type2_8, construct_func_type2_desc(KW_ONLY, D2B)),
    (func_type2_9, construct_func_type2_desc(KW_ONLY, D2G, D1G)),
    (false_func_type2_9_1, construct_func_type2_desc(KW_ONLY, D2B, D1G)),
    (false_func_type2_9_2, construct_func_type2_desc(KW_ONLY, D2G, D1B))
)

FUNC_TYPE2_EQ_HASH = parse_eq_dict({
    func_type2_1: [func_type2_2, false_func_type2_2, func_type2_3,
                   false_func_type2_3_1, false_func_type2_3_2],
    func_type2_4: [func_type2_5, false_func_type2_5, func_type2_6,
                   false_func_type2_6_1, false_func_type2_6_2, func_type2_7,
                   func_type2_8, false_func_type2_8, func_type2_9,
                   false_func_type2_9_1, false_func_type2_9_2]
})
# As of the time of this comment, the expected behavior of comparing these
# functions with check_function_equality is that none of them are the same as
# each other.
FUNC_TYPE2_EQ_EQ = parse_eq_dict({
    func_type2_1: [func_type2_1],
    func_type2_2: [func_type2_2],
    false_func_type2_2: [false_func_type2_2],
    func_type2_3: [func_type2_3],
    false_func_type2_3_1: [false_func_type2_3_1],
    false_func_type2_3_2: [false_func_type2_3_2],
    func_type2_4: [func_type2_4],
    func_type2_5: [func_type2_5],
    false_func_type2_5: [false_func_type2_5],
    func_type2_6: [func_type2_6],
    false_func_type2_6_1: [false_func_type2_6_1],
    false_func_type2_6_2: [false_func_type2_6_2],
    func_type2_7: [func_type2_7],
    func_type2_8: [func_type2_8],
    false_func_type2_8: [false_func_type2_8],
    func_type2_9: [func_type2_9],
    false_func_type2_9_1: [false_func_type2_9_1],
    false_func_type2_9_2: [false_func_type2_9_2]
})


@pytest.fixture(params=[p[0] for p in FUNC_TYPE2_PAIRS],
                ids=[p[1] for p in FUNC_TYPE2_PAIRS])
def func_type2_funcs1(request):
    return request.param


@pytest.fixture(params=[p[0] for p in FUNC_TYPE2_PAIRS],
                ids=[' <--> ' + p[1] for p in FUNC_TYPE2_PAIRS])
def func_type2_funcs2(request):
    return request.param


@pytest.fixture
def func_type2_hashes(func_type2_funcs1, func_type2_funcs2):
    return (func_type2_funcs1, func_type2_funcs2,
            func_type2_funcs2 in FUNC_TYPE2_EQ_HASH[func_type2_funcs1])


@pytest.fixture
def func_type2_eqs(func_type2_funcs1, func_type2_funcs2):
    return (func_type2_funcs1, func_type2_funcs2,
            func_type2_funcs2 in FUNC_TYPE2_EQ_EQ[func_type2_funcs1])


def test_func_defaults_hash(func_type2_hashes):
    func1, func2, should_equal = func_type2_hashes
    hash1 = hash_function(func1)
    hash2 = hash_function(func2)
    if should_equal:
        assert hash1 == hash2

    else:
        assert hash1 != hash2


def test_func_defaults_equal(func_type2_eqs):
    func1, func2, should_equal = func_type2_eqs
    if should_equal:
        assert check_function_equality(func1, func2)

    else:
        assert not check_function_equality(func1, func2)


# ==================================================================================================
# Functions For Testing When Arguments Are Positional-Only, Kw-Only, And Positional
# As Well As For Testing Whether Argument Names Matter
# ==================================================================================================
# We want to minimize use of the constant pool in ID-ing functions, do not
# define a function to get called by all the functions below.

def func_type3_1_1(arg1, arg2, arg3, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_1_2(lorem, ipsum, dolor, sit):
    builder = [lorem]
    builder *= ipsum
    builder.append(dolor)
    builder *= sit
    return builder


def func_type3_2_1(arg1, /, arg2, arg3, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_2_2(arg1, /, lorem, arg3, arg4):
    builder = [arg1]
    builder *= lorem
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_2_3(arg1, /, arg2, lorem, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(lorem)
    builder *= arg4
    return builder


def func_type3_2_4(arg1, /, arg2, arg3, lorem):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= lorem
    return builder


def func_type3_3_1(arg1, arg2, arg3, /, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_3_2(lorem, arg2, arg3, /, arg4):
    builder = [lorem]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_3_3(arg1, lorem, arg3, /, arg4):
    builder = [arg1]
    builder *= lorem
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_3_4(arg1, arg2, lorem, /, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(lorem)
    builder *= arg4
    return builder


def func_type3_4(arg1, *, arg2, arg3, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def false_func_type3_4_1(arg1, *, lorem, arg3, arg4):
    builder = [arg1]
    builder *= lorem
    builder.append(arg3)
    builder *= arg4
    return builder


def false_func_type3_4_2(arg1, *, arg2, lorem, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(lorem)
    builder *= arg4
    return builder


def false_func_type3_4_3(arg1, *, arg2, arg3, lorem):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= lorem
    return builder


def func_type3_5_1(arg1, arg2, arg3, *, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_5_2(lorem, arg2, arg3, *, arg4):
    builder = [lorem]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_5_3(arg1, lorem, arg3, *, arg4):
    builder = [arg1]
    builder *= lorem
    builder.append(arg3)
    builder *= arg4
    return builder


def func_type3_5_4(arg1, arg2, lorem, *, arg4):
    builder = [arg1]
    builder *= arg2
    builder.append(lorem)
    builder *= arg4
    return builder


def func_type4_1(arg1, /, arg2, arg3, arg4, *, arg5):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= arg4
    builder.append(arg5)
    return builder


def func_type4_2(arg1, /, lorem, arg3, arg4, *, arg5):
    builder = [arg1]
    builder *= lorem
    builder.append(arg3)
    builder *= arg4
    builder.append(arg5)
    return builder


def func_type4_3(arg1, /, arg2, lorem, arg4, *, arg5):
    builder = [arg1]
    builder *= arg2
    builder.append(lorem)
    builder *= arg4
    builder.append(arg5)
    return builder


def func_type4_4(arg1, /, arg2, arg3, lorem, *, arg5):
    builder = [arg1]
    builder *= arg2
    builder.append(arg3)
    builder *= lorem
    builder.append(arg5)
    return builder


# --------------------------------------------------------------------------------------------------
# Test Fixtures
# --------------------------------------------------------------------------------------------------
FIRST = 'first of the type'
MIDDLE = 'middle of the type'
END = 'end of the type'
TYPE2 = ' preceded by positional-only'
TYPE3 = ' proceeded by keyword-only'
TYPE4 = TYPE2 + ' and' + TYPE3


def construct_func_type3_desc(arg_type: str, different_name_pos: str = 'N/A'):
    return (f'Arguments Type: {arg_type},'
            f' Different Name Position: {different_name_pos}')


FUNC_TYPE3_PAIRS = (
    (func_type3_1_1, construct_func_type3_desc(REG)),
    (func_type3_1_2, construct_func_type3_desc(REG, 'ALL')),
    (func_type3_2_1, construct_func_type3_desc(REG + TYPE2)),
    (func_type3_2_2, construct_func_type3_desc(REG + TYPE2, FIRST)),
    (func_type3_2_3, construct_func_type3_desc(REG + TYPE2, MIDDLE)),
    (func_type3_2_4, construct_func_type3_desc(REG + TYPE2, END)),
    (func_type3_3_1, construct_func_type3_desc(POS_ONLY)),
    (func_type3_3_2, construct_func_type3_desc(POS_ONLY, FIRST)),
    (func_type3_3_3, construct_func_type3_desc(POS_ONLY, MIDDLE)),
    (func_type3_3_4, construct_func_type3_desc(POS_ONLY, END)),
    (func_type3_4, construct_func_type3_desc(KW_ONLY)),
    (false_func_type3_4_1, construct_func_type3_desc(KW_ONLY, FIRST)),
    (false_func_type3_4_2, construct_func_type3_desc(KW_ONLY, MIDDLE)),
    (false_func_type3_4_3, construct_func_type3_desc(KW_ONLY, END)),
    (func_type3_5_1, construct_func_type3_desc(REG + TYPE3)),
    (func_type3_5_2, construct_func_type3_desc(REG + TYPE3, FIRST)),
    (func_type3_5_3, construct_func_type3_desc(REG + TYPE3, MIDDLE)),
    (func_type3_5_4, construct_func_type3_desc(REG + TYPE3, END)),
    (func_type4_1, construct_func_type3_desc(REG + TYPE4)),
    (func_type4_2, construct_func_type3_desc(REG + TYPE4, FIRST)),
    (func_type4_3, construct_func_type3_desc(REG + TYPE4, MIDDLE)),
    (func_type4_4, construct_func_type3_desc(REG + TYPE4, END))
)

FUNC_TYPE3_EQ_HASH = parse_eq_dict({
    func_type3_1_1: [func_type3_1_2],
    func_type3_2_1: [func_type3_2_2, func_type3_2_3, func_type3_2_4,
                     func_type3_5_1, func_type3_5_2, func_type3_5_3,
                     func_type3_5_4],
    func_type3_3_1: [func_type3_3_2, func_type3_3_3, func_type3_3_4,
                     func_type3_4, false_func_type3_4_1, false_func_type3_4_2,
                     false_func_type3_4_3, func_type4_1, func_type4_2,
                     func_type4_3, func_type4_4]
})
FUNC_TYPE3_EQ_EQ = parse_eq_dict({
    func_type3_1_1: [func_type3_1_2],
    func_type3_2_1: [func_type3_2_2, func_type3_2_3, func_type3_2_4],
    func_type3_3_1: [func_type3_3_2, func_type3_3_3, func_type3_3_4],
    func_type3_4: [func_type3_4],
    false_func_type3_4_1: [false_func_type3_4_1],
    false_func_type3_4_2: [false_func_type3_4_2],
    false_func_type3_4_3: [false_func_type3_4_3],
    func_type3_5_1: [func_type3_5_2, func_type3_5_3, func_type3_5_4],
    func_type4_1: [func_type4_2, func_type4_3, func_type4_4]
})


@pytest.fixture(params=[p[0] for p in FUNC_TYPE3_PAIRS],
                ids=[p[1] for p in FUNC_TYPE3_PAIRS])
def func_type3_funcs1(request):
    return request.param


@pytest.fixture(params=[p[0] for p in FUNC_TYPE3_PAIRS],
                ids=[' <--> ' + p[1] for p in FUNC_TYPE3_PAIRS])
def func_type3_funcs2(request):
    return request.param


@pytest.fixture
def func_type3_hashes(func_type3_funcs1, func_type3_funcs2):
    return (func_type3_funcs1, func_type3_funcs2,
            func_type3_funcs2 in FUNC_TYPE3_EQ_HASH[func_type3_funcs1])


@pytest.fixture
def func_type3_eqs(func_type3_funcs1, func_type3_funcs2):
    return (func_type3_funcs1, func_type3_funcs2,
            func_type3_funcs2 in FUNC_TYPE3_EQ_EQ[func_type3_funcs1])


def test_func_names_hash(func_type3_hashes):
    func1, func2, should_equal = func_type3_hashes
    hash1 = hash_function(func1)
    hash2 = hash_function(func2)
    if should_equal:
        assert hash1 == hash2

    else:
        assert hash1 != hash2


def test_func_names_equal(func_type3_eqs):
    func1, func2, should_equal = func_type3_eqs
    if should_equal:
        assert check_function_equality(func1, func2)

    else:
        assert not check_function_equality(func1, func2)
