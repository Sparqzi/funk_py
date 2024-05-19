from enum import Enum, IntEnum

import pytest

from t_support import cov, cov_counter
from funk_py.modularity.decoration.enum_modifiers import converts_enums


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


LOREM = 'lorem'


class TestEnum:
    class TEnum(Enum):
        HORSE = 1
        LLAMA = 'llama'
        DOG = 3.5

    T_ENUM_ENUM_MATCH = {TEnum.HORSE: 'abc', TEnum.LLAMA: 'def', TEnum.DOG: 'ghi'}
    T_ENUM_VAL_MATCH = {1: 'abc', 'llama': 'def', 3.5: 'ghi'}

    def test_enum_is_valid(self):
        assert TestEnum.TEnum.HORSE.value == 1
        assert TestEnum.TEnum.LLAMA.value == 'llama'
        assert TestEnum.TEnum.DOG.value == 3.5

    @staticmethod
    def undecorated_enum_func(name: str, description: TEnum) -> str:
        return f'{name} - {TestEnum.T_ENUM_ENUM_MATCH[description]}'

    @staticmethod
    @converts_enums
    def decorated_enum_func(name: str, description: TEnum) -> str:
        return f'{name} - {TestEnum.T_ENUM_ENUM_MATCH[description]}'

    def test_has_purpose(self):
        assert TestEnum.TEnum.HORSE != 1
        assert TestEnum.TEnum.LLAMA != 'llama'
        assert TestEnum.TEnum.DOG != 3.5
        with pytest.raises(KeyError):
            TestEnum.undecorated_enum_func(LOREM, list(TestEnum.T_ENUM_VAL_MATCH.keys())[0])

    def test_works_for_values(self):
        for val, _val in TestEnum.T_ENUM_VAL_MATCH.items():
            assert TestEnum.decorated_enum_func(LOREM, val) == f'{LOREM} - {_val}'

    def test_works_for_enums(self):
        for enum, val in TestEnum.T_ENUM_ENUM_MATCH.items():
            assert TestEnum.decorated_enum_func(LOREM, enum) == f'{LOREM} - {val}'


class TestIntEnum:
    # IntEnum normally handles ints just fine, but just to make sure we don't break that behavior,
    # we test it. We also test to make sure it hasn't become necessary.

    class TEnum(IntEnum):
        HORSE = 1
        LLAMA = 2
        DOG = 3

    T_ENUM_ENUM_MATCH = {TEnum.HORSE: 'abc', TEnum.LLAMA: 'def', TEnum.DOG: 'ghi'}
    T_ENUM_VAL_MATCH = {1: 'abc', 2: 'def', 3: 'ghi'}

    def test_int_enum_is_valid(self):
        assert TestIntEnum.TEnum.HORSE.value == 1
        assert TestIntEnum.TEnum.LLAMA.value == 2
        assert TestIntEnum.TEnum.DOG.value == 3

    @staticmethod
    def undecorated_enum_func(name: str, description: TEnum) -> str:
        return f'{name} - {TestIntEnum.T_ENUM_ENUM_MATCH[description]}'

    @staticmethod
    @converts_enums
    def decorated_enum_func(name: str, description: TEnum) -> str:
        return f'{name} - {TestIntEnum.T_ENUM_ENUM_MATCH[description]}'

    def test_has_no_purpose_for_int_enum(self):
        TestIntEnum.undecorated_enum_func(
            LOREM,
            list(TestIntEnum.T_ENUM_VAL_MATCH.keys())[0]
        )

    def test_works_for_values(self):
        for val, _val in TestIntEnum.T_ENUM_VAL_MATCH.items():
            assert TestIntEnum.decorated_enum_func(LOREM, val) == f'{LOREM} - {_val}'

    def test_works_for_enums(self):
        for enum, val in TestIntEnum.T_ENUM_ENUM_MATCH.items():
            assert TestIntEnum.decorated_enum_func(LOREM, enum) == f'{LOREM} - {val}'
