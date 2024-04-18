import json
import sys
from collections import namedtuple

import yaml
from typing import List, Any, Union
from xml.etree import ElementTree as ET

import pytest

from funk_py.sorting.pieces import pick, PickType

COM = 'combinatorial'
TAN = 'tandem'
RED = 'reduce'
ACC = 'accumulate'


KEYS = ['k' + str(i) for i in range(100)]
OUT_KEYS = ['o' + str(i) for i in range(100)]
VALS1 = ['llama', 'horse', 'bear']
VALS2 = ['Hope', 'Jeffrey', 'Maldo']
VALS3 = ['funny', 'scary', 'happy']
VALS4 = ['puppy', 'cow', 'hippo']
VALS5 = ['Caleb', 'Sidney', 'Constantine']
VALS6 = ['lovely', 'strange', 'terrifying']
VALS7 = ['snake', 'capy"bara', 'mon"key']
VALS8 = ['Gerald Hempphry', 'Castlin', 'Al']
VALS9 = ['sil"ly', 'jer\'kish', 'tense, irritating']
VALS10 = ['parrot', 'crow', 'hare']
VALS11 = ['Clance', 'Jerry', 'Calvin']
VALS12 = ['crazy', 'level-headed', 'observant']
DATA_KEY1 = 'data'
DATA_KEY2 = 'group'
TEXT = 'text'


def compare_lists_of_dicts_unordered(list1, list2):
    sorted1 = sorted(list1, key=lambda d: sorted(d.items()))
    sorted2 = sorted(list2, key=lambda d: sorted(d.items()))
    assert sorted1 == sorted2


def make_csv(keys: List[str], *val_sets: list) -> str:
    builder = ','.join(key if ',' not in key else f'"{key}"' for key in keys)
    for vals in zip(*val_sets):
        builder += '\n'
        builder += ','.join(val if ',' not in val else f'"{val}"' for val in vals)

    return builder


def make_spacy_csv(keys: List[str], *val_sets: list) -> str:
    builder = ', '.join(key if ',' not in key else f'"{key}"' for key in keys)
    for vals in zip(*val_sets):
        builder += '\n'
        builder += ','.join(f' {val}' if ',' not in val else f'"{val}"' for val in vals)

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
        xmlify_no_attr(cur, vals[i])

    return ET.tostring(builder, 'unicode')


def xmlify_no_attr(builder: ET.Element, _input: Union[dict, list, str]):
    if (t := type(_input)) is dict:
        for key, val in _input.items():
            cur = ET.SubElement(builder, key)
            xmlify_no_attr(cur, val)

    elif t is list:
        for val in _input:
            cur = ET.SubElement(builder, DATA_KEY1)
            xmlify_no_attr(cur, val)

    else:
        builder.text = _input


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


SimpleDirection = namedtuple('SimpleDirection', ('func', 'output_map'))
ListSet = namedtuple('ListSet', ('list1', 'list2', 'output_map', 'result_set'))
ListBase = namedtuple('ListCommand', ('func', 'output_map', 'keys', 'vals'))
DictSet = namedtuple('DictSet', ('dict', 'output_map', 'result_set'))

TstDef = namedtuple('TstDef', {'func', 'output_map', 'result_set'})


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
    """
    .. code-block:: python

        input = [
            {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
            {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
            {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
        ]
        output_map = {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        red_result = [{'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
            }
        ]
    """
    func, output_map = request.param
    list1 = func(KEYS[:3], VALS1, VALS2, VALS3)
    list2 = func(KEYS[:3], VALS4, VALS5, VALS6)
    _output_map = dict(zip(KEYS[:3], OUT_KEYS[:3]))
    if output_map is not None:
        if output_map in ('xml', 'xml-sa'):
            _output_map = [output_map, {DATA_KEY1: {DATA_KEY2: _output_map}}]

        else:
            _output_map = [output_map, _output_map]

    result1 = make_json_list(OUT_KEYS[:3], VALS1, VALS2, VALS3)
    result2 = make_json_list(OUT_KEYS[:3], VALS4, VALS5, VALS6)

    return ListSet(list1, list2, _output_map, {
        COM: [result1, result2],
        TAN: [result1, result2],
        RED: [[result1[2]], [result2[2]]],
        ACC: [
            [dict(zip(OUT_KEYS[:3], [VALS1, VALS2, VALS3]))],
            [dict(zip(OUT_KEYS[:3], [VALS4, VALS5, VALS6]))],
        ],
    })


@list_fixture
def dissimilar_lists(request):
    """
    .. code-block:: python

        input = [
            {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
            {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
            {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
        ]
        output_map = {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        red_result = [{'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
            }
        ]
    """
    func, output_map = request.param
    list1 = func(KEYS[:3], VALS1, VALS2, VALS3)
    list2 = func(KEYS[3:6], VALS4, VALS5, VALS6)
    _output_map1 = dict(zip(KEYS[:3], OUT_KEYS[:3]))
    _output_map2 = dict(zip(KEYS[3:6], OUT_KEYS[3:6]))
    if output_map is not None:
        if output_map in ('xml', 'xml-sa'):
            _output_map1 = [output_map, {DATA_KEY1: {DATA_KEY2: _output_map1}}]
            _output_map2 = [output_map, {DATA_KEY1: {DATA_KEY2: _output_map2}}]

        else:
            _output_map1 = [output_map, _output_map1]
            _output_map2 = [output_map, _output_map2]

    _output_map = [_output_map1, _output_map2]

    result1 = make_json_list(OUT_KEYS[:3], VALS1, VALS2, VALS3)
    result2 = make_json_list(OUT_KEYS[3:6], VALS4, VALS5, VALS6)

    return ListSet(list1, list2, _output_map, {
        COM: [result1, result2],
        TAN: [result1, result2],
        RED: [[result1[2]], [result2[2]]],
        ACC: [
            [dict(zip(OUT_KEYS[:3], [VALS1, VALS2, VALS3]))],
            [dict(zip(OUT_KEYS[3:6], [VALS4, VALS5, VALS6]))],
        ],
    })


@list_fixture
def more_dissimilar_lists(request):
    """
    .. code-block:: python

        input = [
            {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
            {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
            {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
        ]
        output_map = {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        red_result = [{'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
            }
        ]
    """
    func, output_map = request.param
    list1 = func(KEYS[6:9], VALS7, VALS8, VALS9)
    list2 = func(KEYS[9:12], VALS10, VALS11, VALS12)
    _output_map1 = dict(zip(KEYS[6:9], OUT_KEYS[6:9]))
    _output_map2 = dict(zip(KEYS[9:12], OUT_KEYS[9:12]))
    if output_map is not None:
        if output_map in ('xml', 'xml-sa'):
            _output_map1 = [output_map, {DATA_KEY1: {DATA_KEY2: _output_map1}}]
            _output_map2 = [output_map, {DATA_KEY1: {DATA_KEY2: _output_map2}}]

        else:
            _output_map1 = [output_map, _output_map1]
            _output_map2 = [output_map, _output_map2]

    _output_map = [_output_map1, _output_map2]

    result1 = make_json_list(OUT_KEYS[6:9], VALS7, VALS8, VALS9)
    result2 = make_json_list(OUT_KEYS[9:12], VALS10, VALS11, VALS12)

    return ListSet(list1, list2, _output_map, {
        COM: [result1, result2],
        TAN: [result1, result2],
        RED: [[result1[2]], [result2[2]]],
        ACC: [
            [dict(zip(OUT_KEYS[6:9], [VALS7, VALS8, VALS9]))],
            [dict(zip(OUT_KEYS[9:12], [VALS10, VALS11, VALS12]))],
        ],
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
    """
    .. code-block:: python

        input = {
            'k3': [
                {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
            ]
        }
        output_map = {'k3': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}}
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}
        ]
        red_result = [{'o0': 'v12', 'o1': 'v22', 'o2': 'v32'}]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32']
            }
        ]
    """
    func, output_map = request.param
    dict1 = func([KEYS[3]], similar_lists.list1)
    dict2 = func([KEYS[3]], similar_lists.list2)
    _output_map = similar_lists.output_map
    if output_map is not None:
        if output_map == 'xml':
            if type(similar_lists.output_map) is dict:
                _output_map = ['json', _output_map]

            _output_map = {DATA_KEY2: {KEYS[3]: _output_map}}

        elif output_map == 'xml-sa':
            if type(similar_lists.output_map) is dict:
                _output_map = {DATA_KEY1: _output_map}

            _output_map = {DATA_KEY2: {KEYS[3]: _output_map}}

        else:
            _output_map = {KEYS[3]: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {KEYS[3]: _output_map}

    return ListSet(dict1, dict2, _output_map, {
        COM: similar_lists.result_set[COM],
        TAN: similar_lists.result_set[TAN],
        RED: similar_lists.result_set[RED],
        ACC: similar_lists.result_set[ACC],
    })


@dict_fixture
def dict_with_two_nested_similar_lists_in_list(request, similar_lists):
    """
    .. code-block:: python

        input = {
            'k6': [
                [
                    {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                    {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                    {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
                ],
                [
                    {'k0': 'v40', 'k1': 'v50', 'k2': 'v60'},
                    {'k0': 'v41', 'k1': 'v51', 'k2': 'v61'},
                    {'k0': 'v42', 'k1': 'v52', 'k2': 'v62'}
                ]
            ]
        }
        output_map = {'k6': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}}
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'},
            {'o0': 'v40', 'o1': 'v50', 'o2': 'v60'},
            {'o0': 'v41', 'o1': 'v51', 'o2': 'v61'},
            {'o0': 'v42', 'o1': 'v52', 'o2': 'v62'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'},
            {'o0': 'v40', 'o1': 'v50', 'o2': 'v60'},
            {'o0': 'v41', 'o1': 'v51', 'o2': 'v61'},
            {'o0': 'v42', 'o1': 'v52', 'o2': 'v62'}
        ]
        red_result = [{'o0': 'v42', 'o1': 'v52', 'o2': 'v62'}]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12', 'v40', 'v41', 'v43'],
                'o1': ['v20', 'v21', 'v22', 'v50', 'v51', 'v53'],
                'o2': ['v30', 'v31', 'v32', 'v60', 'v61', 'v63'],
            }
        ]
    """
    func, output_map = request.param
    _dict = func([KEYS[6]], [similar_lists.list1, similar_lists.list2])
    _output_map = similar_lists.output_map
    if output_map is not None:
        if output_map == 'xml-sa':
            if type(similar_lists.output_map) is dict:
                _output_map = {DATA_KEY1: _output_map}

            _output_map = {DATA_KEY1: _output_map}

        elif output_map == 'xml':
            _output_map = ['json', _output_map]

        _output_map = {KEYS[6]: _output_map}

        if 'xml' in output_map:
            _output_map = {DATA_KEY2: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {KEYS[6]: _output_map}

    res = similar_lists.result_set[COM]

    return DictSet(_dict, _output_map, {
        COM: res[0] + res[1],
        TAN: res[0] + res[1],
        RED: [res[1][2]],
        ACC: [dict(zip(OUT_KEYS[:3], [VALS1 + VALS4, VALS2 + VALS5, VALS3 + VALS6]))],
    })


@dict_fixture
def dict_with_two_nested_dissimilar_lists_in_list(request, dissimilar_lists):
    """
    .. code-block:: python

        input = {
            'k6': [
                [
                    {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                    {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                    {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
                ],
                [
                    {'k3': 'v40', 'k4': 'v50', 'k5': 'v60'},
                    {'k3': 'v41', 'k4': 'v51', 'k5': 'v61'},
                    {'k3': 'v42', 'k4': 'v52', 'k5': 'v62'}
                ]
            ]
        }
        output_map = {
            'k6': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2', 'k3': 'o3', 'k4': 'o4', 'k5': 'o5'}
        }
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'},
            {'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32'},
            {'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        red_result = [
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                '02': ['v30', 'v31', 'v32'],
                'o3': ['v40', 'v41', 'v43'],
                'o4': ['v50', 'v51', 'v53'],
                'o5': ['v60', 'v61', 'v63']
            }
        ]
    """
    func, output_map = request.param
    _dict = func([KEYS[6]], [dissimilar_lists.list1, dissimilar_lists.list2])
    _output_map = make_json_dict(KEYS[:6], *OUT_KEYS[:6])
    if isinstance(dissimilar_lists.output_map[0], list):
        if (t := dissimilar_lists.output_map[0][0]) in ('xml', 'xml-sa'):
            _output_map = [t, {DATA_KEY1: {DATA_KEY2: _output_map}}]

        else:
            _output_map = [t, _output_map]

    if output_map is not None:
        if output_map == 'xml-sa':
            if type(dissimilar_lists.output_map[0]) is dict:
                _output_map = {DATA_KEY1: _output_map}

            _output_map = {DATA_KEY1: _output_map}

        elif output_map == 'xml':
            _output_map = ['json', _output_map]

        _output_map = {KEYS[6]: _output_map}

        if 'xml' in output_map:
            _output_map = {DATA_KEY2: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {KEYS[6]: _output_map}

    res = dissimilar_lists.result_set[COM]

    copier = res[0][2].copy()
    copier.update(res[1][2])
    red_result = [copier]

    return DictSet(_dict, _output_map, {
        COM: res[0] + res[1],
        TAN: res[0] + res[1],
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6]))],
    })


@dict_fixture
def two_nested_lists_under_keys(request, dissimilar_lists):
    """
    .. code-block:: python

        input = {
            'k6': [
                {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
            ],
            'k7': [
                {'k3': 'v40', 'k4': 'v50', 'k5': 'v60'},
                {'k3': 'v41', 'k4': 'v51', 'k5': 'v61'},
                {'k3': 'v42', 'k4': 'v52', 'k5': 'v62'}
            ]
        }
        output_map = {
            'k6': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'},
            'k7': {'k3': 'o3', 'k4': 'o4', 'k5': 'o5'}
        }
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        red_result = [
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
                'o3': ['v40', 'v41', 'v42'],
                'o4': ['v50', 'v51', 'v52'],
                'o5': ['v60', 'v61', 'v62']
            }
        ]
    """
    func, output_map = request.param
    _dict = func(KEYS[6:8], dissimilar_lists.list1, dissimilar_lists.list2)
    _output_map1, _output_map2 = dissimilar_lists.output_map
    if output_map is not None:
        if output_map == 'xml-sa':
            if type(_output_map1) is dict:
                _output_map1 = {DATA_KEY1: _output_map1}
                _output_map2 = {DATA_KEY1: _output_map2}

        elif output_map == 'xml' and type(_output_map1) is dict:
            _output_map1 = ['json', _output_map1]
            _output_map2 = ['json', _output_map2]

        _output_map = {KEYS[6]: _output_map1, KEYS[7]: _output_map2}

        if 'xml' in output_map:
            _output_map = {DATA_KEY2: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {KEYS[6]: _output_map1, KEYS[7]: _output_map2}

    mul_result = []
    res = dissimilar_lists.result_set[COM]
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

    copier = res[0][2].copy()
    copier.update(res[1][2])
    red_result = [copier]

    return DictSet(_dict, _output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6]))],
    })


@dict_fixture
def dict_with_list_of_dicts(request):
    """
    .. code-block:: python

        input = {
            'k0': {
                'k1': [
                    {'k2': {'k3': 'v10'}},
                    {'k2': {'k4': 'v11'}},
                    {'k2': {'k5': 'v12'}},
                    {'k2': {'k6': 'v20'}},
                    {'k2': {'k7': 'v21'}},
                    {'k2': {'k8': 'v22'}}
                ]
            }
        }
        output_map = {
            'k0': {
                'k1': {
                    'k2': {'k3': 'o3', 'k4': 'o4', 'k5': 'o5', 'k6': 'o6', 'k7': 'o7', 'k8': 'o8'}
                }
            }
        }
        mul_result = [
            {'o3': 'v10'}, {'o4': 'v11'}, {'o5': 'v12'}, {'o6': 'v20'}, {'o7': 'v21'}, {'o8': 'v22'}
        ]
        tan_result = [
            {'o3': 'v10'}, {'o4': 'v11'}, {'o5': 'v12'}, {'o6': 'v20'}, {'o7': 'v21'}, {'o8': 'v22'}
        ]
        red_result = [
            {'o3': 'v10', 'o4': 'v11', 'o5': 'v12', 'o6': 'v20', 'o7': 'v21', 'o8': 'v22'}
        ]
        acc_result = [
            {
                'o3': ['v10'], 'o4': ['v11'], 'o5': ['v12'],
                'o6': ['v20'], 'o7': ['v21'], 'o8': ['v22']
            }
        ]
    """
    func, output_map = request.param
    _input = {KEYS[0]: {KEYS[1]: []}}

    output_map = {KEYS[0]: {KEYS[1]: {KEYS[2]: dict(zip(KEYS[3:9], OUT_KEYS[3:9]))}}}
    if output_map in ('xml', 'xml-sa'):
        output_map = {DATA_KEY1: {DATA_KEY2: output_map}}

    _list = _input[KEYS[0]][KEYS[1]]
    mul_result = []
    tan_result = []
    red_result = [dict(zip(OUT_KEYS[3:6], VALS1))]
    red_result[0].update(dict(zip(OUT_KEYS[6:9], VALS2)))
    acc_result = [{k: [v] for k, v in red_result[0].items()}]

    for i in range(3):
        _list.append({KEYS[2]: {KEYS[3 + i]: VALS1[i]}})
        _list.append({KEYS[2]: {KEYS[6 + i]: VALS2[i]}})
        mul_result.append({OUT_KEYS[3 + i]: VALS1[i]})
        mul_result.append({OUT_KEYS[6 + i]: VALS2[i]})
        tan_result.append({OUT_KEYS[3 + i]: VALS1[i]})
        tan_result.append({OUT_KEYS[6 + i]: VALS2[i]})

    return DictSet(_input, output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: acc_result,
    })


@dict_fixture
def two_nested_lists_under_double_keys(request, dissimilar_lists):
    """
    .. code-block:: python

        input = {
            'k6': {
                'k8': [
                    {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                    {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                    {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
                ]
            },
            'k7': {
                'k9': [
                    {'k3': 'v40', 'k4': 'v50', 'k5': 'v60'},
                    {'k3': 'v41', 'k4': 'v51', 'k5': 'v61'},
                    {'k3': 'v42', 'k4': 'v52', 'k5': 'v62'}
                ]
            }
        }
        output_map = {
            'k6': {'k8': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'}},
            'k7': {'k9': {'k3': 'o3', 'k4': 'o4', 'k5': 'o5'}}
        }
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        red_result = [
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62'}
        ]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
                'o3': ['v40', 'v41', 'v42'],
                'o4': ['v50', 'v51', 'v52'],
                'o5': ['v60', 'v61', 'v62']
            }
        ]
    """
    func, output_map = request.param
    _dict = func(KEYS[6:8], {KEYS[8]: dissimilar_lists.list1}, {KEYS[9]: dissimilar_lists.list2})
    _output_map1, _output_map2 = dissimilar_lists.output_map
    if output_map is not None:
        if output_map == 'xml-sa' and type(_output_map1) is dict:
            _output_map1 = {DATA_KEY1: _output_map1}
            _output_map2 = {DATA_KEY1: _output_map2}

        _output_map1 = {KEYS[8]: _output_map1}
        _output_map2 = {KEYS[9]: _output_map2}

        if output_map == 'xml':
            _output_map1 = ['json', _output_map1]
            _output_map2 = ['json', _output_map2]

        _output_map = {KEYS[6]: _output_map1, KEYS[7]: _output_map2}

        if 'xml' in output_map:
            _output_map = {DATA_KEY2: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {KEYS[6]: {KEYS[8]: _output_map1}, KEYS[7]: {KEYS[9]: _output_map2}}

    mul_result = []
    res = dissimilar_lists.result_set[COM]
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

    copier = res[0][2].copy()
    copier.update(res[1][2])
    red_result = [copier]

    return DictSet(_dict, _output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6]))],
    })


@dict_fixture
def complicated_dict1(request, dissimilar_lists, more_dissimilar_lists):
    """
    .. code-block:: python

        input = {
            'k12': {
                'k13': [
                    {'k0': 'v10', 'k1': 'v20', 'k2': 'v30'},
                    {'k0': 'v11', 'k1': 'v21', 'k2': 'v31'},
                    {'k0': 'v12', 'k1': 'v22', 'k2': 'v32'}
                ],
                'k14': [
                    {'k3': 'v40', 'k4': 'v50', 'k5': 'v60'},
                    {'k3': 'v41', 'k4': 'v51', 'k5': 'v61'},
                    {'k3': 'v42', 'k4': 'v52', 'k5': 'v62'}
                ]
            },
            'k15': {
                'k16': [
                    {'k6': 'v70', 'k7': 'v80', 'k8': 'v90'},
                    {'k6': 'v71', 'k7': 'v81', 'k8': 'v91'},
                    {'k6': 'v72', 'k7': 'v82', 'k8': 'v92'}
                ],
                'k17': [
                    {'k9': 'v100', 'k10': 'v110', 'k11': 'v120'},
                    {'k9': 'v101', 'k10': 'v111', 'k11': 'v121'},
                    {'k9': 'v102', 'k10': 'v112', 'k11': 'v122'}
                ]
            }
        }
        output_map = {
            'k12': {
                'k13': {'k0': 'o0', 'k1': 'o1', 'k2': 'o2'},
                'k14': {'k3': 'o3', 'k4': 'o4', 'k5': 'o5'}
            },
            'k15': {
                'k16': {'k6': 'o6', 'k7': 'o7', 'k8': 'o8'},
                'k17': {'k9': 'o9', 'k10': 'o10', 'k11': 'o11'}
            }
        }
        mul_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'}
        ]
        tan_result = [
            {'o0': 'v10', 'o1': 'v20', 'o2': 'v30', 'o3': 'v40', 'o4': 'v50', 'o5': 'v60',
             'o6': 'v70', 'o7': 'v80', 'o8': 'v90', 'o9': 'v100', 'o10': 'v110', 'o11': 'v120'},
            {'o0': 'v11', 'o1': 'v21', 'o2': 'v31', 'o3': 'v41', 'o4': 'v51', 'o5': 'v61',
             'o6': 'v71', 'o7': 'v81', 'o8': 'v91', 'o9': 'v101', 'o11': 'v110', 'o11': 'v121'},
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'}
        ]
        red_result = [
            {'o0': 'v12', 'o1': 'v22', 'o2': 'v32', 'o3': 'v42', 'o4': 'v52', 'o5': 'v62',
             'o6': 'v72', 'o7': 'v82', 'o8': 'v92', 'o9': 'v102', 'o10': 'v112', 'o11': 'v122'}
        ]
        acc_result = [
            {
                'o0': ['v10', 'v11', 'v12'],
                'o1': ['v20', 'v21', 'v22'],
                'o2': ['v30', 'v31', 'v32'],
                'o3': ['v40', 'v41', 'v42'],
                'o4': ['v50', 'v51', 'v52'],
                'o5': ['v60', 'v61', 'v62'],
                'o6': ['v70', 'v71', 'v72'],
                'o7': ['v80', 'v81', 'v82'],
                'o8': ['v90', 'v91', 'v92'],
                'o9': ['v100', 'v101', 'v102'],
                'o10': ['v110', 'v111', 'v112'],
                'o11': ['v120', 'v121', 'v122']
            }
        ]
    """
    func, output_map = request.param
    _dict = func([KEYS[12], KEYS[15]],
                 {KEYS[13]: dissimilar_lists.list1, KEYS[14]: dissimilar_lists.list2},
                 {KEYS[16]: more_dissimilar_lists.list1, KEYS[17]: more_dissimilar_lists.list2})
    _output_map1, _output_map2 = dissimilar_lists.output_map
    _output_map3, _output_map4 = more_dissimilar_lists.output_map
    if output_map is not None:
        if output_map == 'xml-sa':
            if type(_output_map1) is dict:
                _output_map1 = {DATA_KEY1: _output_map1}
                _output_map2 = {DATA_KEY1: _output_map2}

            if type(_output_map3) is dict:
                _output_map3 = {DATA_KEY1: _output_map3}
                _output_map4 = {DATA_KEY1: _output_map4}

        _output_map1 = {KEYS[13]: _output_map1, KEYS[14]: _output_map2}
        _output_map2 = {KEYS[16]: _output_map3, KEYS[17]: _output_map4}

        if output_map == 'xml':
            _output_map1 = ['json', _output_map1]
            _output_map2 = ['json', _output_map2]

        _output_map = {KEYS[12]: _output_map1, KEYS[15]: _output_map2}

        if 'xml' in output_map:
            _output_map = {DATA_KEY2: _output_map}

        _output_map = [output_map, _output_map]

    else:
        _output_map = {
            KEYS[12]: {KEYS[13]: _output_map1, KEYS[14]: _output_map2},
            KEYS[15]: {KEYS[16]: _output_map3, KEYS[17]: _output_map4},
        }

    mul_result = []
    res1 = dissimilar_lists.result_set[COM]
    res2 = more_dissimilar_lists.result_set[COM]

    for result1 in res1[0]:
        for result2 in res1[1]:
            for result3 in res2[0]:
                for result4 in res2[1]:
                    copier = result1.copy()
                    copier.update(result2)
                    copier.update(result3)
                    copier.update(result4)
                    mul_result.append(copier)

    tan_result = []
    for i in range(len(res1[0])):
        copier = res1[0][i].copy()
        copier.update(res1[1][i])
        copier.update(res2[0][i])
        copier.update(res2[1][i])
        tan_result.append(copier)

    copier = res1[0][2].copy()
    copier.update(res1[1][2])
    copier.update(res2[0][2])
    copier.update(res2[1][2])
    red_result = [copier]

    return DictSet(_dict, _output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:12], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6,
                                       VALS7, VALS8, VALS9, VALS10, VALS11, VALS12]))],
    })


class TestMultiplicative:
    name = COM
    pick_type = PickType.COMBINATORIAL

    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.output_map, similar_lists.list1, self.pick_type)
        assert ans == similar_lists.result_set[self.name][0]

        ans = pick(similar_lists.output_map, similar_lists.list2, self.pick_type)
        assert ans == similar_lists.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list1,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][0]

        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list2,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.output_map,
                   dict_with_two_nested_similar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.output_map,
                   dict_with_two_nested_dissimilar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.output_map,
                   two_nested_lists_under_keys.dict,
                   self.pick_type)
        compare_lists_of_dicts_unordered(ans, two_nested_lists_under_keys.result_set[self.name])

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        ans = pick(dict_with_list_of_dicts.output_map, dict_with_list_of_dicts.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, dict_with_list_of_dicts.result_set[self.name])

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        ans = pick(two_nested_lists_under_double_keys.output_map,
                   two_nested_lists_under_double_keys.dict,
                   self.pick_type)
        compare_lists_of_dicts_unordered(ans,
                                         two_nested_lists_under_double_keys.result_set[self.name])

    def test_complicated_dict1(self, complicated_dict1):
        print(complicated_dict1.output_map)
        print(complicated_dict1.dict)
        ans = pick(complicated_dict1.output_map, complicated_dict1.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, complicated_dict1.result_set[self.name])


class TestTandem:
    name = TAN
    pick_type = PickType.TANDEM

    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.output_map, similar_lists.list1, self.pick_type)
        assert ans == similar_lists.result_set[self.name][0]

        ans = pick(similar_lists.output_map, similar_lists.list2, self.pick_type)
        assert ans == similar_lists.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list1,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][0]

        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list2,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.output_map,
                   dict_with_two_nested_similar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.output_map,
                   dict_with_two_nested_dissimilar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.output_map,
                   two_nested_lists_under_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_keys.result_set[self.name]

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        ans = pick(dict_with_list_of_dicts.output_map, dict_with_list_of_dicts.dict, self.pick_type)
        assert ans == dict_with_list_of_dicts.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        ans = pick(two_nested_lists_under_double_keys.output_map,
                   two_nested_lists_under_double_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_double_keys.result_set[self.name]

    def test_complicated_dict1(self, complicated_dict1):
        ans = pick(complicated_dict1.output_map, complicated_dict1.dict, self.pick_type)
        assert ans == complicated_dict1.result_set[self.name]


class TestReduce:
    name = RED
    pick_type = PickType.REDUCE

    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.output_map, similar_lists.list1, self.pick_type)
        assert ans == similar_lists.result_set[self.name][0]

        ans = pick(similar_lists.output_map, similar_lists.list2, self.pick_type)
        assert ans == similar_lists.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list1,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][0]

        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list2,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.output_map,
                   dict_with_two_nested_similar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.output_map,
                   dict_with_two_nested_dissimilar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.output_map,
                   two_nested_lists_under_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_keys.result_set[self.name]

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        ans = pick(dict_with_list_of_dicts.output_map, dict_with_list_of_dicts.dict, self.pick_type)
        assert ans == dict_with_list_of_dicts.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        ans = pick(two_nested_lists_under_double_keys.output_map,
                   two_nested_lists_under_double_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_double_keys.result_set[self.name]

    def test_complicated_dict1(self, complicated_dict1):
        ans = pick(complicated_dict1.output_map, complicated_dict1.dict, self.pick_type)
        assert ans == complicated_dict1.result_set[self.name]


class TestAccumulate:
    name = ACC
    pick_type = PickType.ACCUMULATE

    def test_simple_lists(self, similar_lists):
        ans = pick(similar_lists.output_map, similar_lists.list1, self.pick_type)
        assert ans == similar_lists.result_set[self.name][0]

        ans = pick(similar_lists.output_map, similar_lists.list2, self.pick_type)
        assert ans == similar_lists.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list1,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][0]

        ans = pick(dicts_with_one_nested_list.output_map,
                   dicts_with_one_nested_list.list2,
                   self.pick_type)
        assert ans == dicts_with_one_nested_list.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        ans = pick(dict_with_two_nested_similar_lists_in_list.output_map,
                   dict_with_two_nested_similar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_similar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        ans = pick(dict_with_two_nested_dissimilar_lists_in_list.output_map,
                   dict_with_two_nested_dissimilar_lists_in_list.dict,
                   self.pick_type)
        assert ans == dict_with_two_nested_dissimilar_lists_in_list.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        ans = pick(two_nested_lists_under_keys.output_map,
                   two_nested_lists_under_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_keys.result_set[self.name]

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        ans = pick(dict_with_list_of_dicts.output_map, dict_with_list_of_dicts.dict, self.pick_type)
        assert ans == dict_with_list_of_dicts.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        ans = pick(two_nested_lists_under_double_keys.output_map,
                   two_nested_lists_under_double_keys.dict,
                   self.pick_type)
        assert ans == two_nested_lists_under_double_keys.result_set[self.name]

    def test_complicated_dict1(self, complicated_dict1):
        ans = pick(complicated_dict1.output_map, complicated_dict1.dict, self.pick_type)
        assert ans == complicated_dict1.result_set[self.name]



