import math
from collections import namedtuple

import pytest

from t_support import cov, cov_counter
from funk_py.simplicity import Obj


@pytest.fixture(scope='session', autouse=True)
def c():
    if not cov_counter.value:
        cov.start()
        cov_counter.value += 1

    yield cov

    cov_counter.value -= 1
    if not cov_counter.value:
        cov.stop()
        cov.save()
        cov.report()


TCoord = namedtuple('TCoord', ('address', 'value', 'lambda_'))


def set_attr(obj, address, value):
    obj.__setattr__(address, value)


def set_item(obj, address, value):
    obj[address] = value


SIMPLE_VALS1 = (1, 'lorem', math.pi)
SIMPLE_VALS2 = (2, 'ipsum', math.inf)
SIMPLE_VAL_NAMES = ('int', 'str', 'flt')
SIMPLE_KEYS = tuple(c for c in 'abcdefghijklmnopqrstuvwxyz')
BASIC_ADD_LAMBDAS = (set_item, set_attr)
BASIC_ADD_LAMBDA_NAMES = ('setting an item', 'setting an attribute')


EXTRA_VALUE_SET = (3, 'dolor', -0)
SIMPLE_KEYS1 = SIMPLE_KEYS[:len(SIMPLE_VALS1)]
SIMPLE_KEYS2 = SIMPLE_KEYS[len(SIMPLE_VALS1):
                           len(SIMPLE_VALS1) + len(SIMPLE_VALS2)]
EXTRA_KEYS = SIMPLE_KEYS[len(SIMPLE_VALS1) + len(SIMPLE_VALS2):
                         len(SIMPLE_VALS1) + len(SIMPLE_VALS2) +
                         len(EXTRA_VALUE_SET)]


@pytest.fixture
def regular_dict():
    return dict(zip(EXTRA_KEYS, EXTRA_VALUE_SET))


@pytest.fixture
def regular_dict2():
    return dict(zip(SIMPLE_KEYS2, SIMPLE_VALS1))


@pytest.fixture
def iterable_dict():
    return tuple(zip(EXTRA_KEYS, EXTRA_VALUE_SET))


BAD_ATTR_MSG = ('The correct value was retrieved by index, but the same value'
                ' was not retrieved via attribute. There may be a problem with'
                ' __getattr__.')
BAD_ITEM_MSG = ('Getting the stored value via attribute succeeded, but the same'
                ' value was not retrieved by index. There may be a problem with'
                ' __getitem__.')
BAD_ATTR_ITEM_MSG = ('A match was retrieved by neither attribute nor index;'
                     ' however, the correct value was actually stored. Both'
                     ' __getitem__ and __getattr__ have a problem.')
WRONG_ITEM_STORED = ('The wrong value was stored. Normal access methods were'
                     ' bypassed to confirm this.')

WRONG_LEN = ('All expected key-value pairs were entered, but there are more'
             ' pairs in the object than there should be.')
LEN_MUTATED = ("__len__ generated a key when it shouldn't have. This likely"
               " means that __len__ may need to be added to _HIDE_THESE. It is"
               " also advisable to check if the same issue is occurring with"
               " other methods, since it means that python has begun working"
               " differently from how it previously worked.")


def confirm_expected_storage(testy, key, val):
    # Since we have two expected ways to get the value we stored out, we'll
    # see if either of them works. That way a false fail on this test due to
    # a broken __getattr__ or __getitem__ can be properly-diagnosed.
    ans1 = testy.__getattr__(key) == val
    if not ans1:
        ans2 = testy[key] == val
        if not ans2:
            assert dict.__getitem__(testy, key) == val, WRONG_ITEM_STORED
            assert False, BAD_ATTR_ITEM_MSG

        assert False, BAD_ATTR_MSG

    assert testy[key] == val, BAD_ITEM_MSG

def multi_confirm_expected_storage(testy, source):
    for key, val in source:
        confirm_expected_storage(testy, key, val)


def confirm_expected_storage_size(testy, expected_len):
    assert len(testy) == expected_len, WRONG_LEN
    assert len(testy) == expected_len, LEN_MUTATED


def test_can_be_created_empty():
    testy = Obj()
    confirm_expected_storage_size(testy, 0)


def test_can_be_created_with_regular_dict(regular_dict):
    testy = Obj(regular_dict)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    multi_confirm_expected_storage(testy, regular_dict.items())
    confirm_expected_storage_size(testy, len(regular_dict))


def test_can_be_created_with_iterable(iterable_dict):
    testy = Obj(iterable_dict)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    multi_confirm_expected_storage(testy, iterable_dict)
    confirm_expected_storage_size(testy, len(iterable_dict))


def test_can_be_created_with_kwargs(regular_dict):
    testy = Obj(**regular_dict)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    multi_confirm_expected_storage(testy, regular_dict.items())
    confirm_expected_storage_size(testy, len(regular_dict))


def test_can_be_created_with_regular_dict_and_kwargs(regular_dict,
                                                     regular_dict2):
    testy = Obj(regular_dict, **regular_dict2)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    multi_confirm_expected_storage(testy, regular_dict.items())
    multi_confirm_expected_storage(testy, regular_dict2.items())
    confirm_expected_storage_size(testy, len(regular_dict) + len(regular_dict2))


def test_can_be_created_with_iterable_and_kwargs(iterable_dict, regular_dict2):
    testy = Obj(iterable_dict, **regular_dict2)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    multi_confirm_expected_storage(testy, iterable_dict)
    multi_confirm_expected_storage(testy, regular_dict2.items())

    confirm_expected_storage_size(testy,
                                  len(iterable_dict) + len(regular_dict2))


@pytest.fixture(params=SIMPLE_VALS1,
                ids=tuple('value=' + v for v in SIMPLE_VAL_NAMES))
def simple_values(request):
    return request.param


@pytest.fixture(params=SIMPLE_VALS2,
                ids=tuple('key=' + v for v in SIMPLE_VAL_NAMES))
def weird_keys(request):
    return request.param


@pytest.fixture(params=SIMPLE_KEYS[:len(SIMPLE_VALS1)])
def simple_keys(request):
    return request.param


@pytest.fixture(params=BASIC_ADD_LAMBDAS, ids=BASIC_ADD_LAMBDA_NAMES)
def add_methods(request):
    return request.param


def test_adding_simple_values(simple_values, weird_keys, add_methods,
                              regular_dict, regular_dict2, iterable_dict):
    testy = Obj()
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)

    # created with regular dict
    testy = Obj(regular_dict)
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)
    multi_confirm_expected_storage(testy, regular_dict.items())

    # created with kwargs
    testy = Obj(**regular_dict)
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)
    multi_confirm_expected_storage(testy, regular_dict.items())

    # created with iterable
    testy = Obj(iterable_dict)
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)
    multi_confirm_expected_storage(testy, iterable_dict)

    # created with regular dict and kwargs
    testy = Obj(regular_dict, **regular_dict2)
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)
    multi_confirm_expected_storage(testy, regular_dict.items())
    multi_confirm_expected_storage(testy, regular_dict2.items())

    # created with iterable and kwargs
    testy = Obj(iterable_dict, **regular_dict2)
    add_methods(testy, weird_keys, simple_values)
    confirm_expected_storage(testy, weird_keys, simple_values)
    multi_confirm_expected_storage(testy, iterable_dict)
    multi_confirm_expected_storage(testy, regular_dict2.items())


def test_update_works(regular_dict, regular_dict2):
    # Verify it works without any prior reads.
    testy = Obj(regular_dict)
    testy.update(regular_dict2)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    for key, val in regular_dict.items():
        confirm_expected_storage(testy, key, val)
    # NOT DUPLICATE
    for key, val in regular_dict2.items():
        confirm_expected_storage(testy, key, val)

    confirm_expected_storage_size(testy, len(regular_dict) + len(regular_dict2))

    # Verify it works with prior reads.
    # Literally repeat everything, just do a mid-way check.
    testy = Obj(regular_dict)

    # Do a read of the values in the Obj to verify the expected Obj was created.
    for key, val in regular_dict.items():
        confirm_expected_storage(testy, key, val)

    testy.update(regular_dict2)
    # Do a read of the values in the Obj to verify the expected Obj was created.
    for key, val in regular_dict.items():
        confirm_expected_storage(testy, key, val)
    # NOT DUPLICATE
    for key, val in regular_dict2.items():
        confirm_expected_storage(testy, key, val)

    confirm_expected_storage_size(testy, len(regular_dict) + len(regular_dict2))
