import json
import sys
from collections import namedtuple

import yaml
from typing import List, Any
from xml.etree import ElementTree as ET

import pytest

from funk_py.sorting.pieces import pick, PickType

MUL = 'multiplicative'
TAN = 'tandem'


KEYS = ['k' + str(i) for i in range(100)]
OUT_KEYS = ['o' + str(i) for i in range(100)]
VALS1 = ['llama', 'horse', 'bear']
VALS2 = ['Hope', 'Jeffrey', 'Maldo']
VALS3 = ['funny', 'scary', 'happy']
VALS4 = ['puppy', 'cow', 'hippo']
VALS5 = ['Caleb', 'Sidney', 'Constantine']
VALS6 = ['lovely', 'strange', 'terrifying']
DATA_KEY1 = 'data'
DATA_KEY2 = 'group'
TEXT = 'text'


def compare_lists_of_dicts_unordered(list1, list2):
    sorted1 = sorted(list1, key=lambda d: sorted(d.items()))
    sorted2 = sorted(list2, key=lambda d: sorted(d.items()))
    assert sorted1 == sorted2


def make_csv(keys: List[str], *val_sets: list) -> str:
    builder = ','.join(keys)
    for vals in zip(*val_sets):
        builder += '\n'
        builder += ','.join(vals)

    return builder


def make_spacy_csv(keys: List[str], *val_sets: list) -> str:
    builder = ', '.join(keys)
    for vals in zip(*val_sets):
        builder += '\n'
        builder += ', '.join(vals)

    return builder


def make_json_dict(keys: List[str], *vals: Any) -> dict:
    return dict(zip(keys, vals))


def make_json_list(keys: List[str], *val_sets: list) -> list:
    builder = []
    val_sets = zip(*val_sets)
    for vals in val_sets:
        builder.append(dict(zip(keys, vals)))

    return builder


def make_json_dict_str(keys: List[str], *vals: Any) -> str:
    return json.dumps(dict(zip(keys, vals)))


def make_json_list_str(keys: List[str], *val_sets: list) -> str:
    return json.dumps(make_json_list(keys, *val_sets))


def make_jsonl_list(keys: List[str], *val_sets: list) -> str:
    source = make_json_list(keys, *val_sets)
    return '\n'.join(json.dumps(group) for group in source)


def safe_json(value):
    if isinstance(value, list) or isinstance(value, dict):
        return json.dumps(value)

    return str(value)


def make_xml_dict_no_attr(keys: List[str], *vals: Any) -> str:
    builder = ET.Element(DATA_KEY2)
    for i in range(len(keys)):
        cur = ET.SubElement(builder, keys[i])
        cur.text = safe_json(vals[i])

    return ET.tostring(builder, 'unicode')


def make_xml_list_no_attr(keys: List[str], *val_sets: list) -> str:
    builder = ET.Element(DATA_KEY1)
    for i in range(len(val_sets[0])):
        cur = ET.SubElement(builder, DATA_KEY2)
        for j in range(len(keys)):
            _cur = ET.SubElement(cur, keys[j])
            _cur.text = val_sets[j][i]

    return ET.tostring(builder, 'unicode')


def make_xml_dict_attr(keys: List[str], *vals: Any) -> str:
    builder = ET.Element(DATA_KEY2, make_json_dict(keys, *[safe_json(v) for v in vals]))
    return ET.tostring(builder, 'unicode')


def make_xml_list_attr(keys: List[str], *val_sets: list) -> str:
    builder = ET.Element(DATA_KEY1)
    for vals in zip(*val_sets):
        ET.SubElement(builder, DATA_KEY2, dict(zip(keys, vals)))

    return ET.tostring(builder, 'unicode')


def make_yaml_dict(keys: List[str], *vals: Any) -> str:
    return yaml.dump(make_json_dict(keys, *vals))


def make_yaml_list(keys: List[str], *val_sets: list) -> str:
    return yaml.dump(make_json_list(keys, *val_sets))


SimpleDirection = namedtuple('SimpleDirection', ('func', 'instruction'))
ListSet = namedtuple('ListSet', ('list1', 'list2', 'instruction', 'result_set'))
ListBase = namedtuple('ListCommand', ('func', 'instruction', 'keys', 'vals'))
DictSet = namedtuple('DictSet', ('dict', 'instruction', 'result_set'))


list_fixture = pytest.fixture(params=(
    (make_json_list, None),
    (make_json_list_str, 'json'),
    (make_jsonl_list, 'jsonl'),
    (make_xml_list_attr, 'xml'),
    (make_xml_list_no_attr, 'xml-sa'),
    (make_csv, 'csv'),
    (make_spacy_csv, 'csv'),
    (make_yaml_list, 'yaml'),
), ids=(
    'regular lists',
    'json string lists',
    'jsonl string',
    'xml with attributes lists',
    'xml without attributes lists',
    'csv lists',
    'spacy csv lists',
    'yaml lists',
))


@list_fixture
def similar_lists(request):
    func, instruction = request.param
    list1 = func(KEYS[:3], VALS1, VALS2, VALS3)
    list2 = func(KEYS[:3], VALS4, VALS5, VALS6)
    _instruction = dict(zip(KEYS[:3], OUT_KEYS[:3]))
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            _instruction = [instruction, {DATA_KEY1: {DATA_KEY2: _instruction}}]

        else:
            _instruction = [instruction, _instruction]

    result1 = make_json_list(OUT_KEYS[:3], VALS1, VALS2, VALS3)
    result2 = make_json_list(OUT_KEYS[:3], VALS4, VALS5, VALS6)

    return ListSet(list1, list2, _instruction, {
        MUL: [result1, result2],
        TAN: [result1, result2],
    })


# @pytest.fixture(params=(
#     (make_json_list, None),
#     (make_json_list_str, 'json'),
#     (make_jsonl_list, 'jsonl'),
#     (make_xml_list_attr, 'xml'),
#     (make_xml_list_no_attr, 'xml-sa'),
#     (make_csv, 'csv'),
#     (make_spacy_csv, 'csv'),
#     (make_yaml_list, 'yaml'),
# ), ids=(
#     'regular lists',
#     'json string lists',
#     'jsonl string',
#     'xml with attributes lists',
#     'xml without attributes lists',
#     'csv lists',
#     'spacy csv lists',
#     'yaml lists',
# ))
# def similar_lists(request):
#     func, instruction = request.param
#     list1 = func(KEYS[:3], VALS1, VALS2, VALS3)
#     list2 = func(KEYS[:3], VALS4, VALS5, VALS6)
#     _instruction = dict(zip(KEYS[:3], OUT_KEYS[:3]))
#     if instruction is not None:
#         if instruction in ('xml', 'xml-sa'):
#             _instruction = [instruction, {DATA_KEY1: {DATA_KEY2: _instruction}}]
#
#         else:
#             _instruction = [instruction, _instruction]
#
#     result1 = make_json_list(OUT_KEYS[:3], VALS1, VALS2, VALS3)
#     result2 = make_json_list(OUT_KEYS[:3], VALS4, VALS5, VALS6)
#
#     return ListSet(list1, list2, _instruction, result1, result2)


@list_fixture
def dissimilar_lists(request):
    func, instruction = request.param
    list1 = func(KEYS[:3], VALS1, VALS2, VALS3)
    list2 = func(KEYS[3:6], VALS4, VALS5, VALS6)
    _instruction1 = dict(zip(KEYS[:3], OUT_KEYS[:3]))
    _instruction2 = dict(zip(KEYS[3:6], OUT_KEYS[3:6]))
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            _instruction1 = [instruction, {DATA_KEY1: {DATA_KEY2: _instruction1}}]
            _instruction2 = [instruction, {DATA_KEY1: {DATA_KEY2: _instruction2}}]

        else:
            _instruction1 = [instruction, _instruction1]
            _instruction2 = [instruction, _instruction2]

    _instruction = [_instruction1, _instruction2]

    result1 = make_json_list(OUT_KEYS[:3], VALS1, VALS2, VALS3)
    result2 = make_json_list(OUT_KEYS[3:6], VALS4, VALS5, VALS6)

    return ListSet(list1, list2, _instruction, {
        MUL: [result1, result2],
        TAN: [result1, result2],
    })


dict_fixture = pytest.fixture(params=(
    (make_json_dict, None),
    (make_json_dict_str, 'json'),
    (make_xml_dict_attr, 'xml'),
    (make_xml_dict_no_attr, 'xml-sa'),
    (make_yaml_dict, 'yaml'),
), ids=(
    'regular dict',
    'json string dict',
    'xml with attributes dict',
    'xml without attributes dict',
    'yaml dict',
))


@dict_fixture
def dicts_with_one_nested_list(request, similar_lists):
    func, instruction = request.param
    dict1 = func([KEYS[3]], similar_lists.list1)
    dict2 = func([KEYS[3]], similar_lists.list2)
    _instruction = similar_lists.instruction
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            if type(similar_lists.instruction) is dict:
                _instruction = ['json', _instruction]

            _instruction = [instruction, {DATA_KEY2: {KEYS[3]: _instruction}}]

        else:
            _instruction = [instruction, {KEYS[3]: _instruction}]

    else:
        _instruction = {KEYS[3]: _instruction}

    return ListSet(dict1, dict2, _instruction, {
        MUL: similar_lists.result_set[MUL],
        TAN: similar_lists.result_set[TAN],
    })


@dict_fixture
def dict_with_two_nested_similar_lists_in_list(request, similar_lists):
    func, instruction = request.param
    _dict = func([KEYS[6]], [similar_lists.list1, similar_lists.list2])
    _instruction = similar_lists.instruction
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            _instruction = [instruction, {DATA_KEY2: {KEYS[6]: ['json', _instruction]}}]

        else:
            _instruction = [instruction, {KEYS[6]: _instruction}]

    else:
        _instruction = {KEYS[6]: _instruction}

    res = similar_lists.result_set[MUL]

    return DictSet(_dict, _instruction, {
        MUL: res[0] + res[1],
        TAN: res[0] + res[1],
    })


@dict_fixture
def dict_with_two_nested_dissimilar_lists_in_list(request, dissimilar_lists):
    func, instruction = request.param
    _dict = func([KEYS[6]], [dissimilar_lists.list1, dissimilar_lists.list2])
    _instruction = make_json_dict(KEYS[:6], *OUT_KEYS[:6])
    if isinstance(dissimilar_lists.instruction[0], list):
        if (t := dissimilar_lists.instruction[0][0]) in ('xml', 'xml-sa'):
            _instruction = [t, {DATA_KEY1: {DATA_KEY2: _instruction}}]

        else:
            _instruction = [t, _instruction]

    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            _instruction = [
                instruction,
                {
                    DATA_KEY2: {
                        KEYS[6]: [
                            'json',
                            _instruction
                        ],
                    },
                },
            ]

        else:
            _instruction = [instruction, {KEYS[6]: _instruction}]

    else:
        _instruction = {KEYS[6]: _instruction}

    res = dissimilar_lists.result_set[MUL]

    return DictSet(_dict, _instruction, {
        MUL: res[0] + res[1],
        TAN: res[0] + res[1],
    })


@dict_fixture
def two_nested_lists_under_keys(request, dissimilar_lists):
    func, instruction = request.param
    _dict = func(KEYS[6:8], dissimilar_lists.list1, dissimilar_lists.list2)
    _instruction1, _instruction2 = dissimilar_lists.instruction
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            if isinstance(_instruction1, dict):
                _instruction = [
                    instruction,
                    {
                        DATA_KEY2: {
                            KEYS[6]: ['json', _instruction1],
                            KEYS[7]: ['json', _instruction2],
                        },
                    },
                ]

            else:
                _instruction = [
                    instruction,
                    {
                        DATA_KEY2: {
                            KEYS[6]: _instruction1,
                            KEYS[7]: _instruction2,
                        },
                    },
                ]

        else:
            _instruction = [instruction, {KEYS[6]: _instruction1, KEYS[7]: _instruction2}]

    else:
        _instruction = {KEYS[6]: _instruction1, KEYS[7]: _instruction2}

    mul_result = []
    res = dissimilar_lists.result_set[MUL]
    for result1 in res[0]:
        for result2 in res[1]:
            copier = result1.copy()
            copier.update(result2)
            mul_result.append(copier)

    tan_result = []
    for i in range(len(res[0])):
        copier = res[0][i].copy()
        copier.update(res[1][i])
        tan_result.append(copier)

    return DictSet(_dict, _instruction, {
        MUL: mul_result,
        TAN: tan_result,
    })


class TestMultiplicative:
    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.instruction, similar_lists.list1)
        assert ans == similar_lists.result_set[MUL][0]

        ans = pick(similar_lists.instruction, similar_lists.list2)
        assert ans == similar_lists.result_set[MUL][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.instruction, dicts_with_one_nested_list.list1)
        assert ans == dicts_with_one_nested_list.result_set[MUL][0]

        ans = pick(dicts_with_one_nested_list.instruction, dicts_with_one_nested_list.list2)
        assert ans == dicts_with_one_nested_list.result_set[MUL][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.instruction,
                   dict_with_two_nested_similar_lists_in_list.dict)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[MUL]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.instruction,
                   dict_with_two_nested_dissimilar_lists_in_list.dict)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[MUL]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.instruction, two_nested_lists_under_keys.dict)
        compare_lists_of_dicts_unordered(ans, two_nested_lists_under_keys.result_set[MUL])


class TestTandem:
    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.instruction, similar_lists.list1, PickType.TANDEM)
        assert ans == similar_lists.result_set[TAN][0]

        ans = pick(similar_lists.instruction, similar_lists.list2, PickType.TANDEM)
        assert ans == similar_lists.result_set[TAN][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.instruction,
                   dicts_with_one_nested_list.list1,
                   PickType.TANDEM)
        assert ans == dicts_with_one_nested_list.result_set[TAN][0]

        ans = pick(dicts_with_one_nested_list.instruction,
                   dicts_with_one_nested_list.list2,
                   PickType.TANDEM)
        assert ans == dicts_with_one_nested_list.result_set[TAN][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.instruction,
                   dict_with_two_nested_similar_lists_in_list.dict,
                   PickType.TANDEM)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[TAN]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.instruction,
                   dict_with_two_nested_dissimilar_lists_in_list.dict)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[TAN]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.instruction,
                   two_nested_lists_under_keys.dict,
                   PickType.TANDEM)
        compare_lists_of_dicts_unordered(ans, two_nested_lists_under_keys.result_set[TAN])
