import json
import os
from collections import namedtuple
from datetime import datetime, time, date, timedelta, timezone
from typing import TextIO

import pytest

from t_support import cov, cov_counter
# _DiskCacheNameConverters is included to facilitate testing of syntax.
from funk_py.modularity.decoration.cache_modifiers import (_DiskCacheNameConverters, disk_cache,
                                                           DiskCacheMethod)

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


TDef = namedtuple('TDef', ('input', 'output'))
ABC = 'abcdefghijklmnopqrstuvwxyz'
MSG = 'Hello world!'


def abc_provider():
    while True:
        for i in range(len(ABC)):
            yield ABC[i]


@pytest.fixture(params=(
    TDef('lorem', ';str;lorem'),
    TDef(543, ';int;543'),
    TDef(97.5, ';float;97.5'),
    TDef(datetime(2024, 9, 18, 14, 22, 33), ';datetime;2024-09-18--14-22-33--'),
    TDef(date(2024, 9, 18), ';date;2024-09-18'),
    TDef(time(14, 22, 33), ';time;14-22-33--'),
), ids=('str', 'int', 'float', 'datetime', 'date', 'time'))
def simple_vals(request):
    return request.param


@pytest.fixture(params=(
    TDef('ipsum', ';str;ipsum'),
    TDef(987, ';int;987'),
    TDef(16.666, ';float;16.666'),
    TDef(datetime(2025, 4, 13, 19, 12, 0, tzinfo=timezone(-timedelta(hours=6))),
         ';datetime;2025-04-13--19-12-00--UTC-06:00'),
    TDef(date(2025, 4, 13), ';date;2025-04-13'),
    TDef(time(19, 12, 0, tzinfo=timezone(-timedelta(hours=6))), ';time;19-12-00--UTC-06:00'),
), ids=('str', 'int', 'float', 'datetime', 'date', 'time'))
def more_simple_vals(request):
    return request.param

@pytest.fixture(params=(
    TDef('dolor', ';str;dolor'),
    TDef(5, ';int;5'),
    TDef(9.0, ';float;9.0'),
    TDef(datetime(2023, 1, 1, 1, 0, 0, 19), ';datetime;2023-01-01--01-00-00--'),
    TDef(date(2023, 1, 1), ';date;2023-01-01'),
    TDef(time(1, 0, 0, 19), ';time;01-00-00--'),
), ids=('str', 'int', 'float', 'datetime', 'date', 'time'))
def even_more_simple_vals(request):
    return request.param

@pytest.fixture(params=(
    TDef('sit', ';str;sit'),
    TDef(19, ';int;19'),
    TDef(float('inf'), ';float;inf'),
), ids=('str', 'int', 'float'))
def still_even_more_simple_vals(request):
    return request.param


class DumbStr(str): ...
class DumbInt(int): ...
class DumbFloat(float): ...
class DumbList(list): ...
class DumbTuple(tuple): ...
class DumbDict(dict): ...
class Horse:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __str__(self) -> str:
        return f'Horse(name={self.name}, age={self.age})'

    def __eq__(self, other: 'Horse') -> bool:
        return self.name == other.name and self.age == other.age


@pytest.fixture(params=(
    TDef(DumbStr('lorem'), ';str;lorem'),
    TDef(DumbInt(19), ';int;19'),
    TDef(DumbFloat(9.75), ';float;9.75'),
), ids=('str', 'int', 'float'))
def simple_subclass_vals(request):
    return request.param


@pytest.fixture(params=(
        (list, 'list'),
        (tuple, 'tuple'),
        (DumbList, 'list'),
        (DumbTuple, 'tuple')
), ids=('list', 'tuple', 'inherited list', 'inherited tuple'))
def iterable_vals(request, simple_vals, more_simple_vals, even_more_simple_vals,
                  still_even_more_simple_vals):
    _type, name = request.param
    _in = _type([simple_vals.input, more_simple_vals.input, even_more_simple_vals.input,
                 still_even_more_simple_vals.input])
    out = f';{name};' + ','.join([simple_vals.output, more_simple_vals.output,
                                  even_more_simple_vals.output,
                                  still_even_more_simple_vals.output]) + f';end-{name};'
    return TDef(_in, out)

@pytest.fixture(params=(dict, DumbDict), ids=('dict', 'inherited dict'))
def dict_vals(request, simple_vals, more_simple_vals, even_more_simple_vals,
              still_even_more_simple_vals):
    _type = request.param
    _in = _type({simple_vals.input: more_simple_vals.input,
                 even_more_simple_vals.input: still_even_more_simple_vals.input})
    out = (f';dict;{simple_vals.output}:{more_simple_vals.output},'
           f'{even_more_simple_vals.output}:{still_even_more_simple_vals.output};end-dict;')
    return TDef(_in, out)


@pytest.fixture
def unknown_val():
    return TDef(Horse('Bob', 19), ';Horse;Horse(name=Bob, age=19)')


def test_simple_vals_name(simple_vals):
    assert _DiskCacheNameConverters.to_str(simple_vals.input) == simple_vals.output


def test_simple_subclass_vals_name(simple_subclass_vals):
    assert (_DiskCacheNameConverters.to_str(simple_subclass_vals.input)
            == simple_subclass_vals.output)


def test_iterable_vals_name(iterable_vals):
    assert _DiskCacheNameConverters.to_str(iterable_vals.input) == iterable_vals.output


def test_dict_vals_name(dict_vals):
    assert _DiskCacheNameConverters.to_str(dict_vals.input) == dict_vals.output


def test_unknown_val_name(unknown_val):
    assert _DiskCacheNameConverters.to_str(unknown_val.input) == unknown_val.output


N01 = 'Thunder'
N02 = 'Breeze'
N03 = 'Jasper'
N04 = 'Fleet'
N05 = 'Mystic'
N06 = 'Sandy'
N07 = 'Stormy'
N08 = 'Blaze'
N09 = 'Copper'
N10 = 'Moonshine'
N11 = 'Whisper'
N12 = 'Sky'
N13 = 'Forest'
N14 = 'Rusty'
N15 = 'Starlight'
N16 = 'Dash'
N17 = 'Midnight'
N18 = 'River'

A1 = 1
A2 = 13
A3 = 3
A4 = 2
A5 = 4
A6 = 6
A7 = 7
A8 = 8
A9 = 9
A10 = 10
A11 = 11
A12 = 16
A13 = 5
A14 = 14
A15 = 15
A16 = 19
A17 = 20

HORSE01 = N01, A3
HORSE02 = N02, A2
HORSE03 = N03, A4
HORSE04 = N02, A5
HORSE05 = N04, A7
HORSE06 = N05, A12
HORSE07 = N01, A10
HORSE08 = N06, A9
HORSE09 = N07, A1
HORSE10 = N02, A13
HORSE11 = N08, A8
HORSE12 = N09, A3
HORSE13 = N08, A17
HORSE14 = N10, A1
HORSE15 = N11, A5
HORSE16 = N02, A15
HORSE17 = N08, A12
HORSE18 = N12, A2
HORSE19 = N06, A7
HORSE20 = N13, A14
HORSE21 = N08, A12
HORSE22 = N09, A11
HORSE23 = N14, A16
HORSE24 = N15, A6
HORSE25 = N16, A9
HORSE26 = N17, A17
HORSE27 = N18, A14
HORSE28 = N13, A3
HORSE29 = N16, A2
HORSE30 = N01, A13


def make_horse_str(name: str, age: int) -> str:
    return f';str;{name}\\;int;{age}'.lower()


HORSE01_10 = (HORSE01, HORSE02, HORSE03, HORSE04, HORSE05, HORSE06, HORSE07, HORSE08, HORSE09,
              HORSE10)


@pytest.fixture(params=enumerate(HORSE01_10), ids=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
def horse01_10(request):
    horse = request.param
    builder = []
    for i in range(horse[0] + 1):
        builder.append(make_horse_str(*HORSE01_10[i]).lower())

    return TDef(horse[1], (make_horse_str(*horse[1]), Horse(*horse[1]), builder))


@pytest.fixture
def horse01():
    return TDef(HORSE01, (make_horse_str(*HORSE01), Horse(*HORSE01)))


@pytest.fixture
def horse02():
    return TDef(HORSE02, (make_horse_str(*HORSE02), Horse(*HORSE02)))


@pytest.fixture
def horse03():
    return TDef(HORSE03, (make_horse_str(*HORSE03), Horse(*HORSE03)))


@pytest.fixture
def horse04():
    return TDef(HORSE04, (make_horse_str(*HORSE04), Horse(*HORSE04)))


@pytest.fixture
def horse05():
    return TDef(HORSE05, (make_horse_str(*HORSE05), Horse(*HORSE05)))


@pytest.fixture
def horse11():
    return TDef(HORSE11, (make_horse_str(*HORSE11), Horse(*HORSE11)))


@pytest.fixture(params=(HORSE11, HORSE12, HORSE13, HORSE14, HORSE15, HORSE16, HORSE17, HORSE18,
                        HORSE19, HORSE20),
                ids=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
def horse11_20(request):
    horse = request.param
    return TDef(horse, (make_horse_str(*horse), Horse(*horse)))


def horse_write_method(horse: Horse, io: TextIO):
    json.dump(dict(name=horse.name, age=horse.age), io)


def horse_read_method(io: TextIO):
    return Horse(**json.load(io))


TARGET_DIR = 'target_dir'
TARGET_DIR2 = 'target_dir2'
MAX_SIZE = 10
BAD_RETURN = 'The function did not return the expected value.'
BAD_NUMBER = 'The expected number of results was not present.'
BAD_USES = 'The incorrect number of uses was stored for a result.'
SHOULD_BE_PRESENT = 'A name that should already be in the results is not yet present.'
EXPECTED_PATH = 'The expected path for a file does not exist.'
WRONG_OVER = 'The wrong value got overwritten.'


def check_index(index,
                ex_len: int,
                accessor: callable = None,
                base=None,
                non_base=None,
                non_base_names: list = None,
                others: dict = None,
                should_contain: list = None,
                other_asserts: callable = None,
                file_accessor: callable = lambda x: x[0]):
    assert len(index) == ex_len, BAD_NUMBER
    if accessor is not None and base is not None:
        t = {}
        if non_base is not None and non_base_names is not None:
            for name in non_base_names:
                t[name] = non_base

        if others is not None:
            for name, val in others.items():
                t[name] = val

        for name in index:
            if other_asserts is not None:
                other_asserts(name, index)

            assert accessor(index[name]) == t.get(name, base)
            assert os.path.exists(os.path.join(TARGET_DIR, file_accessor(index[name]))), \
                EXPECTED_PATH

    else:
        for name in index:
            if other_asserts is not None:
                other_asserts(name, index)

            assert os.path.exists(os.path.join(TARGET_DIR, file_accessor(index[name]))), \
                EXPECTED_PATH

    if should_contain is not None:
        for name in should_contain:
            assert name in index, SHOULD_BE_PRESENT


class TestLfuDiskCache:
    @pytest.fixture(scope='class')
    def setup(self):
        os.mkdir(TARGET_DIR)

        yield

        for root, _, files in os.walk(TARGET_DIR):
            for file in files:
                os.remove(os.path.join(root, file))

        os.rmdir(TARGET_DIR)

    @staticmethod
    def overwrite_tst(t_func, horse01, horse02, horse11):
        ans = t_func(*horse01.input)
        assert ans == horse01.output[1]
        ans = t_func(*horse11.input)
        assert ans == horse11.output[1]
        index = t_func._DiskCache__index
        h1_name = horse01.output[0]
        h11_name = horse11.output[0]
        o_names = [make_horse_str(*h) for h in HORSE01_10[2:]]
        check_index(index, MAX_SIZE, lambda x: x[1], 2, others={h1_name: 3, h11_name: 1},
                    should_contain=[h1_name, h11_name] + o_names)
        ans = t_func(*horse02.input)
        assert ans == horse02.output[1]
        h2_name = horse02.output[0]
        check_index(index, MAX_SIZE, lambda x: x[1], 2, others={h1_name: 3, h2_name: 1},
                    should_contain=[h1_name, h2_name] + o_names)

    class TestSingleInstance:
        # Scope of the below is set to class to ensure the built index is never deconstructed.
        # These tests are supposed to represent usage during a single session.
        @pytest.fixture(scope='class')
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, len(ex_index), lambda x: x[1], 1, should_contain=ex_index)

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, MAX_SIZE, lambda x: x[1], 1, 2, ex_index)

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLfuDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestSingleModifiedInstance:
        # Scope of the below is set to class to ensure the built index is never deconstructed.
        # These tests are supposed to represent usage during a single session.
        @pytest.fixture(scope='class')
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, in_bytes=False, write_converter=horse_write_method,
                        read_converter=horse_read_method)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, len(ex_index), lambda x: x[1], 1, should_contain=ex_index)

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, MAX_SIZE, lambda x: x[1], 1, 2, ex_index)

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLfuDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestMultipleInstances:
        # Scope of the below is not set The goal of this is to ensure a new object is instantiated
        # for every test. This ensures that files are actually saved correctly.
        @pytest.fixture
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, len(ex_index), lambda x: x[1], 1, should_contain=ex_index)

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, MAX_SIZE, lambda x: x[1], 1, 2, ex_index)

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLfuDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestMultipleModifiedInstances:
        # Scope of the below is not set The goal of this is to ensure a new object is instantiated
        # for every test. This ensures that files are actually saved correctly.
        @pytest.fixture
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, in_bytes=False, write_converter=horse_write_method,
                        read_converter=horse_read_method)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, len(ex_index), lambda x: x[1], 1, should_contain=ex_index)

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            check_index(index, MAX_SIZE, lambda x: x[1], 1, 2, ex_index)

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLfuDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)
                
                
class TestLruDiskCache:
    @pytest.fixture(scope='class')
    def setup(self):
        os.mkdir(TARGET_DIR)

        yield

        for root, _, files in os.walk(TARGET_DIR):
            for file in files:
                os.remove(os.path.join(root, file))

        os.rmdir(TARGET_DIR)

    @staticmethod
    def overwrite_tst(t_func, horse01, horse02, horse11):
        ans = t_func(*horse01.input)
        assert ans == horse01.output[1]
        ans = t_func(*horse11.input)
        assert ans == horse11.output[1]
        index = t_func._DiskCache__index
        assert len(index) == MAX_SIZE, BAD_NUMBER
        ex_names = ([horse01.output[0]] + [horse11.output[0]]
                    + [make_horse_str(*h) for h in HORSE01_10[2:]])
        for name in index:
            assert name in ex_names, WRONG_OVER
            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        ans = t_func(*horse02.input)
        assert ans == horse02.output[1]
        assert len(index) == MAX_SIZE, BAD_NUMBER
        ex_names[2] = horse02.output[0]
        for name in index:
            assert name in ex_names, WRONG_OVER
            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        for horse in HORSE01_10[3:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

    class TestSingleInstance:
        # Scope of the below is set to class to ensure the built index is never deconstructed.
        # These tests are supposed to represent usage during a single session.
        @pytest.fixture(scope='class')
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.LRU)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLruDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestMultipleInstances:
        # Scope of the below is not set The goal of this is to ensure a new object is instantiated
        # for every test. This ensures that files are actually saved correctly.
        @pytest.fixture
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.LRU)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestLruDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)


class TestWuncDiskCache:
    @pytest.fixture(scope='class')
    def setup(self):
        os.mkdir(TARGET_DIR)

        yield

        for root, _, files in os.walk(TARGET_DIR):
            for file in files:
                os.remove(os.path.join(root, file))

        os.rmdir(TARGET_DIR)

    @staticmethod
    def overwrite_tst(t_func, horse01, horse02, horse11):
        ans = t_func(*horse01.input)
        assert ans == horse01.output[1]
        ans = t_func(*horse11.input)
        assert ans == horse11.output[1]
        index = t_func._DiskCache__index
        assert len(index) == MAX_SIZE, BAD_NUMBER
        for name in index:
            if name == horse01.output[0]:
                assert index[name][1] == 3, BAD_USES

            elif name == horse11.output[0]:
                assert index[name][1] == 1, BAD_USES

            else:
                assert index[name][1] == 2, BAD_USES

            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        for horse in HORSE01_10[3:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

        ans = t_func(*horse02.input)
        assert ans == horse02.output[1]
        assert len(index) == MAX_SIZE, BAD_NUMBER
        for name in index:
            if name == horse01.output[0]:
                assert index[name][1] == 3, BAD_USES

            elif name in (horse02.output[0], horse11.output[0]):
                assert index[name][1] == 1, BAD_USES

            else:
                assert index[name][1] == 2, BAD_USES

            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        for horse in HORSE01_10[3:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

    class TestSingleInstance:
        # Scope of the below is set to class to ensure the built index is never deconstructed.
        # These tests are supposed to represent usage during a single session.
        @pytest.fixture(scope='class')
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.WUNC)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                assert index[name][1] == 1, BAD_USES
                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                if name in ex_index:
                    assert index[name][1] == 2, BAD_USES

                else:
                    assert index[name][1] == 1, BAD_USES

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestWuncDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestMultipleInstances:
        # Scope of the below is not set The goal of this is to ensure a new object is instantiated
        # for every test. This ensures that files are actually saved correctly.
        @pytest.fixture
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.WUNC)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                assert index[name][1] == 1, BAD_USES
                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                if name in ex_index:
                    assert index[name][1] == 2, BAD_USES

                else:
                    assert index[name][1] == 1, BAD_USES

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestWuncDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)


class TestAgeDiskCache:
    BAD_TIME = ('The datetime either was not stored properly, or the format in which it is stored '
                'has changed. Value was {}. Expected format was \'%Y-%m-%d--%H:%M:%S.%f\'.')
    MISS_VAL = 'An expected value was missing.'
    @pytest.fixture(scope='class')
    def setup(self):
        os.mkdir(TARGET_DIR)

        yield

        for root, _, files in os.walk(TARGET_DIR):
            for file in files:
                os.remove(os.path.join(root, file))

        os.rmdir(TARGET_DIR)

    @staticmethod
    def overwrite_tst(t_func, horse01, horse02, horse11):
        ans = t_func(*horse01.input)
        assert ans == horse01.output[1]
        ans = t_func(*horse11.input)
        assert ans == horse11.output[1]
        index = t_func._DiskCache__index
        assert len(index) == MAX_SIZE, BAD_NUMBER
        for name in index:
            try:
                datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

            except ValueError:
                assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        assert horse11.output[0] in index, TestAgeDiskCache.MISS_VAL
        for horse in HORSE01_10[1:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

        ans = t_func(*horse02.input)
        assert ans == horse02.output[1]
        assert len(index) == MAX_SIZE, BAD_NUMBER
        for name in index:
            try:
                datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

            except ValueError:
                assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        assert horse11.output[0] in index, TestAgeDiskCache.MISS_VAL
        for horse in HORSE01_10[1:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

        ans = t_func(*horse01.input)
        assert ans == horse01.output[1]
        for name in index:
            try:
                datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

            except ValueError:
                assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

            assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        assert horse11.output[0] in index, TestAgeDiskCache.MISS_VAL
        assert horse01.output[0] in index, TestAgeDiskCache.MISS_VAL
        for horse in HORSE01_10[2:]:
            assert make_horse_str(*horse) in index, WRONG_OVER

    class TestSingleInstance:
        # Scope of the below is set to class to ensure the built index is never deconstructed.
        # These tests are supposed to represent usage during a single session.
        @pytest.fixture(scope='class')
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.AGE)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                try:
                    datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

                except ValueError:
                    assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                try:
                    datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

                except ValueError:
                    assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestAgeDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)

    class TestMultipleInstances:
        # Scope of the below is not set The goal of this is to ensure a new object is instantiated
        # for every test. This ensures that files are actually saved correctly.
        @pytest.fixture
        def t_func(self):
            @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.AGE)
            def make_horse(name: str, age: int) -> Horse:
                return Horse(name, age)

            return make_horse

        def test_up_to_max_no_problem(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == len(ex_index), BAD_NUMBER
            for name in ex_index:
                assert name in index, SHOULD_BE_PRESENT
                try:
                    datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

                except ValueError:
                    assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_increments_correctly(self, setup, t_func, horse01_10):
            ans = t_func(*horse01_10.input)
            assert ans == horse01_10.output[1], BAD_RETURN
            ex_index = horse01_10.output[2]
            index = t_func._DiskCache__index
            assert len(index) == MAX_SIZE, BAD_NUMBER
            for name in index:
                try:
                    datetime.strptime(index[name][1], '%Y-%m-%d--%H:%M:%S.%f')

                except ValueError:
                    assert False, TestAgeDiskCache.BAD_TIME.format(index[name][1])

                assert os.path.exists(os.path.join(TARGET_DIR, index[name][0])), EXPECTED_PATH

        def test_not_replace_higher(self, setup, t_func, horse01, horse02, horse11):
            TestAgeDiskCache.overwrite_tst(t_func, horse01, horse02, horse11)


class TestMultipleTypes:
    @pytest.fixture(scope='class')
    def setup(self):
        os.mkdir(TARGET_DIR)
        os.mkdir(TARGET_DIR2)

        yield

        for root, _, files in os.walk(TARGET_DIR):
            for file in files:
                os.remove(os.path.join(root, file))

        for root, _, files in os.walk(TARGET_DIR2):
            for file in files:
                os.remove(os.path.join(root, file))

        os.rmdir(TARGET_DIR)
        os.rmdir(TARGET_DIR2)

    @pytest.fixture(scope='class')
    def t_funcs(self):
        @disk_cache(TARGET_DIR, MAX_SIZE, cache_method=DiskCacheMethod.LFU)
        def make_horse1(name: str, age: int) -> Horse:
            return Horse(name, age)

        @disk_cache(TARGET_DIR2, MAX_SIZE, cache_method=DiskCacheMethod.LRU)
        def make_horse2(name: str, age: int) -> Horse:
            return Horse(name, age)

        return make_horse1, make_horse2

    def test_up_to_max_no_problem(self, setup, t_funcs, horse01_10):
        t_func1, t_func2 = t_funcs
        # Test for LFU behavior
        ans = t_func1(*horse01_10.input)
        assert ans == horse01_10.output[1], BAD_RETURN
        ex_index = horse01_10.output[2]
        index = t_func1._DiskCache__index
        check_index(index, len(ex_index), lambda x: x[1], 1, should_contain=ex_index)
        # Test for LRU behavior
        ans = t_func2(*horse01_10.input)
        assert ans == horse01_10.output[1], BAD_RETURN
        ex_index = horse01_10.output[2]
        index = t_func2._DiskCache__index
        assert len(index) == len(ex_index), BAD_NUMBER
        for name in ex_index:
            assert name in index, SHOULD_BE_PRESENT
            assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

    def test_increments_correctly(self, setup, t_funcs, horse01_10):
        t_func1, t_func2 = t_funcs
        # Test for LFU behavior
        ans = t_func1(*horse01_10.input)
        assert ans == horse01_10.output[1], BAD_RETURN
        ex_index = horse01_10.output[2]
        index = t_func1._DiskCache__index
        check_index(index, MAX_SIZE, lambda x: x[1], 1, 2, ex_index)
        # Test for LRU behavior
        ans = t_func2(*horse01_10.input)
        assert ans == horse01_10.output[1], BAD_RETURN
        index = t_func2._DiskCache__index
        assert len(index) == MAX_SIZE, BAD_NUMBER
        for name in index:
            assert os.path.exists(os.path.join(TARGET_DIR, index[name])), EXPECTED_PATH

    def test_not_replace_higher(self, setup, t_funcs, horse01, horse02, horse11):
        t_func1, t_func2 = t_funcs
        TestLfuDiskCache.overwrite_tst(t_func1, horse01, horse02, horse11)
        TestLruDiskCache.overwrite_tst(t_func2, horse01, horse02, horse11)
