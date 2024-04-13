import json
from collections import namedtuple

import yaml
from typing import List, Any
from xml.etree import ElementTree as ET

import pytest

from funk_py.sorting.pieces import pick

KEYS = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6']
OUT_KEYS = ['o1', 'o2', 'o3', 'o4', 'o5', 'o6']
VALS1 = ['llama', 'horse', 'bear']
VALS2 = ['Hope', 'Jeffrey', 'Maldo']
VALS3 = ['funny', 'scary', 'happy']
VALS4 = ['puppy', 'cow', 'hippo']
VALS5 = ['Caleb', 'Sidney', 'Constantine']
VALS6 = ['lovely', 'strange', 'terrifying']
DATA_KEY1 = 'data'
DATA_KEY2 = 'group'
TEXT = 'text'


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


def make_xml_dict_no_attr(keys: List[str], *vals: Any) -> str:
    builder = ET.Element(DATA_KEY2)
    for i in range(len(keys)):
        cur = ET.SubElement(builder, keys[i])
        cur.text = str(vals[i])

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
    builder = ET.Element(DATA_KEY2, make_json_dict(keys, *vals))
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


ListSet = namedtuple(
    'ListSet',
    ('list1', 'list2', 'instruction', 'result1', 'result2')
)


@pytest.fixture(params=(
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
def lists(request):
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

    return ListSet(list1, list2, _instruction, result1, result2)


@pytest.fixture(params=(
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
def dicts_with_one_nested_list(request, lists):
    func, instruction = request.param
    dict1 = func([KEYS[3]], lists.list1)
    dict2 = func([KEYS[3]], lists.list2)
    _instruction = lists.instruction
    if instruction is not None:
        if instruction in ('xml', 'xml-sa'):
            if type(lists.instruction) is dict:
                _instruction = ['json\'', _instruction]

            _instruction = [instruction, {DATA_KEY2: {KEYS[3]: _instruction}}]

        else:
            _instruction = [instruction, {KEYS[3]: _instruction}]

    else:
        _instruction = {KEYS[3]: _instruction}

    return ListSet(dict1, dict2, _instruction, lists.result1, lists.result2)


class TestLists:
    def test_simple_lists_multiplied(self, lists):
        ans = pick(lists.instruction, lists.list1)
        assert ans == lists.result1

        ans = pick(lists.instruction, lists.list2)
        assert ans == lists.result2

    def test_single_dict_nested_lists_multiplied(self, dicts_with_one_nested_list):
        print(repr(dicts_with_one_nested_list.list1))
        print(repr(dicts_with_one_nested_list.list2))
        print(repr(dicts_with_one_nested_list.instruction))
        ans = pick(dicts_with_one_nested_list.instruction, dicts_with_one_nested_list.list1)
        assert ans == dicts_with_one_nested_list.result1

        ans = pick(dicts_with_one_nested_list.instruction, dicts_with_one_nested_list.list2)
        assert ans == dicts_with_one_nested_list.result2
