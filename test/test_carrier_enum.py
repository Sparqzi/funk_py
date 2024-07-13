from enum import Enum

import pytest


from funk_py.modularity.decoration.enums import CarrierEnum


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
        def HORSE(name_: str, owner: str | list[str] = None, age: int = 1): ...

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
