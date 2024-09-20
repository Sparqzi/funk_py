import pytest

from funk_py.sorting.pieces import fracture


# Sample data for the tests
NAME = 'name'
AGE = 'age'
CITY = 'city'

P1 = 'Alice'
P2 = 'Bob'
P3 = 'Charlie'
NAMES = (P1, P2, P1, P3, P2)

A1 = 30
A2 = 25
A3 = 35
A4 = 29
AGES = (A1, A2, A1, A3, A4)

C1 = 'New York'
C2 = 'Los Angeles'
C3 = 'San Francisco'
CITIES = (C1, C2, C3, C1, C2)


def make_item(index_: int) -> dict:
    return {NAME: NAMES[index_], AGE: AGES[index_], CITY: CITIES[index_]}


@pytest.fixture
def item1(): return make_item(0)


@pytest.fixture
def item2(): return make_item(1)


@pytest.fixture
def item3(): return make_item(2)


@pytest.fixture
def item4(): return make_item(3)


@pytest.fixture
def item5(): return make_item(4)


@pytest.fixture(params=(False, True), ids=('not inplace', 'inplace'))
def data(request, item1, item2, item3, item4, item5):
    if request.param:
        return True, [item1, item2, item3, item4, item5]

    return False, [item1.copy(), item2.copy(), item3.copy(), item4.copy(), item5.copy()]


def assert_correct(inplace, result, expected):
    assert len(result) == len(expected), 'Result does not have the correct length.'
    if inplace:
        # If inplace, `is` should be used to compare items, but the rest should be compared
        # normally.
        for r_subset, e_subset in zip(result, expected):
            assert r_subset[0] == e_subset[0]
            assert len(r_subset[1]) == len(e_subset[1]), ('Result does not have the correct number '
                                                          'of values for a subset.')
            for r_item, e_item in zip(r_subset[1], e_subset[1]):
                assert r_item is e_item

    else:
        # When not inplace, a regular equality comparison can be used.
        assert result == expected


@pytest.fixture
def single_key(item1, item2, item3, item4, item5):
    # Don't make copies of the items, instead use the original items. This allows the inplace test
    # to work.
    return [
        ({NAME: P1}, [item1, item3]),
        ({NAME: P2}, [item2, item5]),
        ({NAME: P3}, [item4]),
    ]


def test_single_key(single_key, data):
    inplace, _data = data
    result = list(fracture(_data, NAME))
    assert_correct(inplace, result, single_key)


@pytest.fixture
def multiple_keys(item1, item2, item3, item4, item5):
    # Don't make copies of the items, instead use the original items. This allows the inplace test
    # to work.
    return [
        ({NAME: P1, CITY: C1}, [item1]),
        ({NAME: P2, CITY: C2}, [item2, item5]),
        ({NAME: P1, CITY: C3}, [item3]),
        ({NAME: P3, CITY: C1}, [item4]),
    ]


def test_multiple_keys_inplace(multiple_keys, data):
    inplace, _data = data
    result = list(fracture(_data, NAME, CITY))
    assert_correct(inplace, result, multiple_keys)


def test_empty_list():
    result = list(fracture([], 'name'))
    assert result == []


@pytest.fixture
def item1_partial(): return {NAME: P1, AGE: A1}


@pytest.fixture
def item2_partial(): return {NAME: P2, AGE: A2}


@pytest.fixture
def item3_partial(): return {AGE: A1, CITY: C3}


@pytest.fixture
def item4_partial(): return {NAME: P3, AGE: A3, CITY: C1}


@pytest.fixture
def item5_partial(): return {CITY: C2}


@pytest.fixture(params=(False, True), ids=('not inplace', 'inplace'))
def data_missing_keys(
        request,
        item1_partial,
        item2_partial,
        item3_partial,
        item4_partial,
        item5_partial,
):
    if request.param:
        return True, [item1_partial, item2_partial, item3_partial, item4_partial, item5_partial]

    return (
        False,
        [
            item1_partial.copy(),
            item2_partial.copy(),
            item3_partial.copy(),
            item4_partial.copy(),
            item5_partial.copy(),
        ],
    )


@pytest.fixture
def single_key_missing_from_some(
        item1_partial,
        item2_partial,
        item3_partial,
        item4_partial,
        item5_partial,
):
    return [
        ({NAME: P1}, [item1_partial]),
        ({NAME: P2}, [item2_partial]),
        ({}, [item3_partial, item5_partial]),
        ({NAME: P3}, [item4_partial]),
    ]


def test_missing_keys(single_key_missing_from_some, data_missing_keys):
    inplace, _data = data_missing_keys
    result = list(fracture(_data, NAME))
    assert_correct(inplace, result, single_key_missing_from_some)
