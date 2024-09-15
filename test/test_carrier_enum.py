from typing import Union, List

import pytest

from funk_py.modularity.decoration.enums import CarrierEnum, ignore


def test_can_create_empty():
    class Bologna(CarrierEnum): pass


def test_can_create_with_simple_values():
    class Bologna(CarrierEnum):
        HORSE = 1
        HOUSE = 2
        HISS = 'snake'
        HOARSE = 13.75


def test_can_create_with_simple_values_and_use():
    class Bologna(CarrierEnum):
        HORSE = 1
        HOUSE = 2
        HISS = 'snake'
        HOARSE = 13.75

    assert Bologna.HORSE.value == 1
    assert Bologna.HORSE.name == 'HORSE'
    assert Bologna.HOUSE.value == 2
    assert Bologna.HOUSE.name == 'HOUSE'
    assert Bologna.HISS.value == 'snake'
    assert Bologna.HISS.name == 'HISS'
    assert Bologna.HOARSE.value == 13.75
    assert Bologna.HOARSE.name == 'HOARSE'


def test_simple_values_cant_be_called():
    class Bologna(CarrierEnum):
        HORSE = 1
        HOUSE = 2
        HISS = 'snake'
        HOARSE = 13.75

    with pytest.raises(TypeError):
        Bologna.HORSE(5)

    with pytest.raises(TypeError):
        Bologna.HORSE[0]


def test_can_create_with_complex_values():
    class Bologna(CarrierEnum):
        @staticmethod
        def HORSE(name_: str, owner: Union[str, List[str]] = None, age: int = 1): ...

        @staticmethod
        def HOUSE(address: str, *, owner: str = None, age: int = 0): ...

        APPLE = 'Bologna'


    # Check that HORSE works as intended:
    assert Bologna.HORSE.value == 'HORSE'
    assert Bologna.HORSE.name == 'HORSE'
    testy = Bologna.HORSE('Jennifer')
    assert testy.value == 'HORSE'
    assert testy.name == 'HORSE:1'
    assert testy.name_ == 'Jennifer'
    assert testy.owner is None
    assert testy.age == 1
    assert testy[0] == 'Jennifer'
    assert testy[1] is None
    assert testy[2] == 1

    testy = Bologna.HORSE('Jennifer', 'albatross')
    assert testy.value == 'HORSE'
    assert testy.name == 'HORSE:2'
    assert testy.name_ == 'Jennifer'
    assert testy.owner == 'albatross'
    assert testy.age == 1
    assert testy[0] == 'Jennifer'
    assert testy[1] == 'albatross'
    assert testy[2] == 1

    testy = Bologna.HORSE('Jennifer', age=47)
    assert testy.value == 'HORSE'
    assert testy.name == 'HORSE:3'
    assert testy.name_ == 'Jennifer'
    assert testy.owner is None
    assert testy.age == 47
    assert testy[0] == 'Jennifer'
    assert testy[1] is None
    assert testy[2] == 47

    assert Bologna.HOUSE.value == 'HOUSE'
    assert Bologna.HOUSE.name == 'HOUSE'
    testy = Bologna.HOUSE('1234 Monkey Lane')
    assert testy.value == 'HOUSE'
    assert testy.name == 'HOUSE:1'
    assert testy.address == '1234 Monkey Lane'
    assert testy.owner is None
    assert testy.age == 0


def test_complex_values_which_cant_be_called():
    class Bologna(CarrierEnum):
        @staticmethod
        def HORSE(name_: str, owner: Union[str, List[str]] = None, age: int = 1): ...

        @staticmethod
        def HOUSE(address: str, *, owner: str = None, age: int = 0): ...

        APPLE = 'Bologna'

    testy = Bologna.HORSE('Jennifer')

    with pytest.raises(TypeError):
        # Verify using the type that should work for the instance that generated this instance, just
        # to verify it actually doesn't generate.
        testy('hoarde')


B_VAL = 'Value was not the expected value.'
B_NAME = 'Name was not the expected name.'
B_ATTR = 'Getting a value by attribute did not work right.'
B_POS = 'Getting a value by index did not work right.'


class TestEverything:
    PI = 3.14159
    @pytest.fixture(scope='class')
    def t_enum(self):
        class MyEnum(CarrierEnum):
            def __init__(i_self, value):
                super().__init__(value)
                i_self.uses = 0

            PI = self.PI

            POINT4D = lambda w, x, y, z: ...

            @staticmethod
            def POINT2D(x: int, y: int = 0): ...

            @staticmethod
            def POINT3D(x: int, /, y: int, *, z: int): ...

            @classmethod
            def PI_POINT3D(cls, x: int, y: int): return {'z': cls.PI.value}

            def CALC_POINT2D(i_self, x: int):
                i_self.uses += 1
                return {'y': i_self.uses * i_self.gen_random() * x}

            @ignore
            @staticmethod
            def gen_random():
                return 4  # chosen by fair dice roll.
                          # guaranteed to be random.

        return MyEnum

    def test_simple_value_works_as_intended(self, t_enum):
        assert t_enum.PI.value == 3.14159, B_VAL
        assert t_enum.PI.name == 'PI', B_NAME
        pytest.raises(TypeError, lambda: t_enum.PI())
        pytest.raises(TypeError, lambda: t_enum.PI[0])
        pytest.raises(AttributeError, lambda: t_enum.PI.x)

    def test_simple_static_method_using_default(self, t_enum):
        point = t_enum.POINT2D(42)
        assert point.value == 'POINT2D', B_VAL
        assert point.name == 'POINT2D:1', B_NAME
        assert point.x == 42, B_ATTR
        assert point[0] == 42, B_POS
        assert point.y == 0, B_ATTR
        assert point[1] == 0, B_POS

    def test_simple_static_method_not_using_default(self, t_enum):
        point = t_enum.POINT2D(42, 55)
        assert point.value == 'POINT2D', B_VAL
        assert point.name == 'POINT2D:2', B_NAME + ' (Second Time Attempting)'
        assert point.x == 42, B_ATTR
        assert point[0] == 42, B_POS
        assert point.y == 55, B_ATTR
        assert point[1] == 55, B_POS

    def test_simple_static_method_with_specific_types_of_args(self, t_enum):
        point = t_enum.POINT3D(53, 19, z=93)
        assert point.value == 'POINT3D', B_VAL
        assert point.name == 'POINT3D:1', B_NAME
        assert point[0] == 53, B_POS
        assert point.y == 19, B_ATTR
        assert point[1] == 19, B_POS
        assert point.z == 93, B_ATTR
        pytest.raises(AttributeError, lambda: point.x)
        pytest.raises(IndexError, lambda: point[2])

    def test_class_method_which_returns(self, t_enum):
        point = t_enum.PI_POINT3D(1, 2)
        assert point.value == 'PI_POINT3D', B_VAL
        assert point.name == 'PI_POINT3D:1', B_NAME
        assert point.x == 1, B_ATTR
        assert point[0] == 1, B_POS
        assert point.y == 2, B_ATTR
        assert point[1] == 2, B_POS
        assert point.z == 3.14159, B_ATTR
        pytest.raises(IndexError, lambda: point[2])

    def test_instance_method_which_returns(self, t_enum):
        point = t_enum.CALC_POINT2D(14)
        assert point.value == 'CALC_POINT2D', B_VAL + ' (1st)'
        assert point.name == 'CALC_POINT2D:1', B_NAME + ' (1st)'
        assert point.x == 14, B_ATTR + ' (1st)'
        assert point[0] == 14, B_POS + ' (1st)'
        assert point.y == 56, B_ATTR + ' (1st)'
        pytest.raises(IndexError, lambda: point[1])

        point = t_enum.CALC_POINT2D(14)
        assert point.value == 'CALC_POINT2D', B_VAL + ' (2nd)'
        assert point.name == 'CALC_POINT2D:2', B_NAME + ' (2nd)'
        assert point.x == 14, B_ATTR + ' (2nd)'
        assert point[0] == 14, B_POS + ' (2nd)'
        assert point.y == 112, B_ATTR + ' (2nd)'
        pytest.raises(IndexError, lambda: point[1])

    def test_ignore_works(self, t_enum): assert t_enum.gen_random() == 4

    def test_lambda(self, t_enum):
        point = t_enum.POINT4D(5, 6, 7, 8)
        assert point.value == 'POINT4D', B_VAL
        assert point.name == 'POINT4D:1', B_NAME
        assert point.w == 5, B_ATTR
        assert point[0] == 5, B_POS
        assert point.x == 6, B_ATTR
        assert point[1] == 6, B_POS
        assert point.y == 7, B_ATTR
        assert point[2] == 7, B_POS
        assert point.z == 8, B_ATTR
        assert point[3] == 8, B_POS
