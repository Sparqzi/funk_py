from collections import namedtuple
from copy import deepcopy
import csv
import io
import json
from typing import List, Any, Union, Tuple, Dict, Optional, Callable
import yaml

import pytest

from funk_py.modularity.basic_structures import pass_, Speed
from funk_py.sorting.dict_manip import align_to_list, nest_under_keys
from funk_py.sorting.pieces import pick, PickType
from funk_py.sorting.converters import json_to_xml, json_to_csv, json_to_jsonl


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
VALS5 = ['"Caleb', 'Sidney', 'Constan,tine']
VALS6 = ['lovely"', 'strange', 'terrifying']
VALS7 = ['snake', 'capy"bara', 'mon"key']
VALS8 = ['Gerald Hempphry', 'Castlin', 'Al']
VALS9 = ['sil"ly', 'jer\'kish', 'tense, irritating']
VALS10 = ['parrot', 'crow', 'hare']
VALS11 = ['Clance', 'Jerry', 'Calvin']
VALS12 = ['crazy', 'level-headed', 'observant']
DATA_KEY1 = 'data'
DATA_KEY2 = 'group'
GEN_XML_MOD = (DATA_KEY1, DATA_KEY2)
TEXT = 'text'


def compare_lists_of_dicts_unordered(list1, list2) -> bool:
    sorted1 = sorted(list1, key=lambda d: sorted(d.items()))
    sorted2 = sorted(list2, key=lambda d: sorted(d.items()))
    assert sorted1 == sorted2


def make_dict(keys: List[str], vals: list) -> dict:
    return dict(zip(keys, vals))


def make_list(keys: List[str], *val_sets: list) -> list:
    return [make_dict(keys, val_set) for val_set in zip(*val_sets)]


def json_to_spacy_csv(data: List[dict]) -> str:
    headers = set()
    for line in data:
        headers.update(line.keys())

    headers = list(headers)
    str_headers = [str(h).center(20) for h in headers]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(str_headers)
    for row in data:
        writer.writerow([str(v).center(20) for v in align_to_list(headers, row, '')])

    return output.getvalue()


def json_to_xml_sa_list(data: List[dict]) -> str:
    return json_to_xml({DATA_KEY1: {DATA_KEY2: data}})


def json_to_xml_list(data: List[dict]) -> str:
    return json_to_xml({DATA_KEY1: {DATA_KEY2: data}}, True)


def json_to_xml_sa_dict(data) -> str:
    return json_to_xml({DATA_KEY1: data})


def json_to_xml_dict(data) -> str:
    return json_to_xml({DATA_KEY1: data}, True)


TBase = namedtuple('TBase', {'func', 'name', 'speed', 'output_modifier'})
ListSet = namedtuple('ListSet',
                     ('source1', 'source2', 'list1', 'list2', 'output_map1', 'output_map2',
                      'result_set', 'speed', 'name'))
DictSet = namedtuple('DictSet', ('source', 'dict', 'output_map', 'result_set', 'speed', 'name'))
TstDef = namedtuple('TstDef', {'func', 'output_map', 'result_set'})


PS_80_000 = Speed(40_000, 0.5)
PS_50_000 = Speed(25_000, 0.5)
PS_30_000 = Speed(15_000, 0.5)
PS_20_000 = Speed(10_000, 0.5)
PS_18_000 = Speed(9_000, 0.5)
PS_14_000 = Speed(7_000, 0.5)
PS_10_000 = Speed(5_000, 0.5)
PS_6_666__ = Speed(5_000, 0.75)
PS_6_000 = Speed(4_500, 0.75)
PS_4_000 = Speed(2_000, 0.5)
PS_2_500 = Speed(1_250, 0.5)
PS_1_000 = Speed(500, 0.5)
PS_800 = Speed(400, 0.5)
PS_500 = Speed(250, 0.5)
PS_250 = Speed(500, 2)


list_fixture = pytest.fixture(params=(
    TBase(func=pass_, name=None, speed=PS_50_000, output_modifier=None),
    TBase(func=json.dumps, name='json', speed=PS_14_000, output_modifier=None),
    TBase(func=json_to_jsonl, name='jsonl', speed=PS_20_000, output_modifier=None),
    TBase(func=json_to_xml_list, name='xml', speed=PS_10_000, output_modifier=GEN_XML_MOD),
    TBase(func=json_to_xml_sa_list, name='xml-sa', speed=PS_10_000, output_modifier=GEN_XML_MOD),
    TBase(func=json_to_csv, name='csv', speed=PS_20_000, output_modifier=None),
    TBase(func=json_to_spacy_csv, name='csv', speed=PS_20_000, output_modifier=None),
    TBase(func=yaml.dump, name='yaml', speed=PS_800, output_modifier=None),
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


def make_two_lists(case: TBase, list1_def: list, list2_def: list, result1_def: list,
                   result2_def: list, output_map: Union[dict, list],
                   o_output_map: Union[dict, list] = None) -> ListSet:
    list1 = case.func(make_list(*list1_def))
    list2 = case.func(make_list(*list2_def))
    result1 = make_list(*result1_def)
    result2 = make_list(*result2_def)

    # Set up the accumulator results, since they're different.
    keys, *vals = result1_def
    acc1 = make_dict(keys, vals)
    keys, *vals = result2_def
    acc2 = make_dict(keys, vals)

    # If o_output_map is not specified, desired behavior is to duplicate output_map.
    if o_output_map is None:
        o_output_map = deepcopy(output_map)

    # Mutate output_map appropriately.
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)
        o_output_map = nest_under_keys(o_output_map, *output_modifier)

    if (name := case.name) is not None:
        output_map = [name, output_map]
        o_output_map = [name, o_output_map]

    return ListSet(list1_def, list2_def, list1, list2, output_map, o_output_map, {
        COM: [result1, result2],
        TAN: [result1, result2],
        RED: [[result1[2]], [result2[2]]],
        ACC: [[acc1], [acc2]],
    }, case.speed, name)

@list_fixture
def similar_lists(request):
    """
    .. code-block:: python

        _input = [
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
    return make_two_lists(request.param,
                          [KEYS[:3], VALS1, VALS2, VALS3],
                          [KEYS[:3], VALS4, VALS5, VALS6],
                          [OUT_KEYS[:3], VALS1, VALS2, VALS3],
                          [OUT_KEYS[:3], VALS4, VALS5, VALS6],
                          make_dict(KEYS[:3], OUT_KEYS[:3]))


@list_fixture
def dissimilar_lists(request):
    """
    .. code-block:: python

        _input = [
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
    return make_two_lists(request.param,
                          [KEYS[:3], VALS1, VALS2, VALS3],
                          [KEYS[3:6], VALS4, VALS5, VALS6],
                          [OUT_KEYS[:3], VALS1, VALS2, VALS3],
                          [OUT_KEYS[3:6], VALS4, VALS5, VALS6],
                          make_dict(KEYS[:3], OUT_KEYS[:3]),
                          make_dict(KEYS[3:6], OUT_KEYS[3:6]))


@list_fixture
def more_dissimilar_lists(request):
    """
    .. code-block:: python

        _input = [
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
    return make_two_lists(request.param,
                          [KEYS[6:9], VALS7, VALS8, VALS9],
                          [KEYS[9:12], VALS10, VALS11, VALS12],
                          [OUT_KEYS[6:9], VALS7, VALS8, VALS9],
                          [OUT_KEYS[9:12], VALS10, VALS11, VALS12],
                          make_dict(KEYS[6:9], OUT_KEYS[6:9]),
                          make_dict(KEYS[9:12], OUT_KEYS[9:12]))


dict_fixture = pytest.fixture(params=(
    TBase(func=pass_, name=None, speed=PS_80_000, output_modifier=None),
    TBase(func=json.dumps, name='json', speed=PS_18_000, output_modifier=None),
    TBase(func=json_to_xml_dict, name='xml', speed=PS_6_000, output_modifier=(DATA_KEY1,)),
    TBase(func=json_to_xml_sa_dict, name='xml-sa', speed=PS_6_666__, output_modifier=(DATA_KEY1,)),
    TBase(func=yaml.dump, name='yaml', speed=PS_1_000, output_modifier=None),
), ids=(
    'regular dict',
    'json string dict',
    'xml with attributes dict',
    'xml without attributes dict',
    'yaml dict',
))


def correct_speed(overrides: Dict[tuple, Speed], outer_overrides: Dict[Optional[str], Speed],
                  outer_name: Optional[str], outer: Speed,
                  inner_name: Union[str, Tuple[str, ...]] = None,
                  inner: Union[Speed, Tuple[Speed, ...]] = None,
                  inner_modifier: Union[int, float] = 1,
                  calc: Callable[[Speed, Speed], Speed] = None):
    if (speed := overrides.get((outer_name, inner_name))) is not None:
        # Overrides should be taken as strictly-correct, they are mapped directly to combinations,
        # and should be used when the calculation for a particular combo is wrong.
        return speed

    if (speed := outer_overrides.get(outer_name)) is not None:
        # outer_overrides only apply to the outer speed, and should not result in early return.
        # They are to be used when a fixture's speeds generally cover a case, but do not fully cover
        # it (one name for outer experiences abnormally-slow tests).
        outer = speed

    if inner is None:
        # If inner speed does not exist, just return outer_speed.
        return outer

    # Apply the modifier to inner speed.
    if (t := type(inner)) is tuple:
        inner = (inn * inner_modifier for inn in inner)

    else:
        inner = inner * inner_modifier

    if calc is not None:
        # Run the given calculation on the values.
        # We assume that the user accounted for inner being a tuple if it is.
        return calc(outer, inner)

    elif t is tuple:
        # No calculation was given. We just assume the slowest speed controls the test.
        # In this case, the tuple must be unpacked lest we have unintended errors.
        return min(outer, *inner)

    # No calculation was given. We just assume the slowest speed controls the test.
    # In this case, inner does not have to be unpacked.
    return min(outer, inner)


@dict_fixture
def dicts_with_one_nested_list(request, similar_lists):
    """
    .. code-block:: python

        _input = {
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
    case = request.param
    speed = correct_speed({
        ('json', 'csv'): PS_14_000,
        ('yaml', None): PS_500
    }, {}, name := case.name, case.speed, similar_lists.name, similar_lists.speed)

    dict1 = case.func(s1 := make_dict([KEYS[3]], [similar_lists.list1]))
    dict2 = case.func(s2 := make_dict([KEYS[3]], [similar_lists.list2]))

    output_map1 = {KEYS[3]: similar_lists.output_map1}
    output_map2 = {KEYS[3]: similar_lists.output_map2}
    if (output_modifier := case.output_modifier) is not None:
        output_map1 = nest_under_keys(output_map1, *output_modifier)
        output_map2 = nest_under_keys(output_map2, *output_modifier)

    if name is not None:
        output_map1 = [name, output_map1]
        output_map2 = [name, output_map2]

    # Build results:
    return ListSet(s1, s2, dict1, dict2, output_map1, output_map2, {
        COM: similar_lists.result_set[COM],
        TAN: similar_lists.result_set[TAN],
        RED: similar_lists.result_set[RED],
        ACC: similar_lists.result_set[ACC],
    }, speed, (name, similar_lists.name))


@dict_fixture
def dict_with_two_nested_similar_lists_in_list(request, similar_lists):
    """
    .. code-block:: python

        _input = {
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
    case = request.param
    speed = correct_speed({
        ('yaml', None): PS_500,
        ('xml', 'xml'): PS_4_000,
        ('xml', 'xml-sa'): PS_4_000,
        ('json', 'csv'): PS_6_666__,
        ('yaml', 'yaml'): PS_250
    }, {}, name := case.name, case.speed, similar_lists.name, similar_lists.speed, 0.5)

    _dict = case.func(source := make_dict([KEYS[6]], [[similar_lists.list1, similar_lists.list2]]))

    output_map = make_dict([KEYS[6]], [similar_lists.output_map1])
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)

    if name is not None:
        output_map = [name, output_map]

    # Build results:
    res = similar_lists.result_set[COM]

    return DictSet(source, _dict, output_map, {
        COM: res[0] + res[1],
        TAN: res[0] + res[1],
        RED: [res[1][2]],
        ACC: [make_dict(OUT_KEYS[:3], [VALS1 + VALS4, VALS2 + VALS5, VALS3 + VALS6])],
    }, speed, (name, similar_lists.name))


@dict_fixture
def dict_with_two_nested_dissimilar_lists_in_list(request, dissimilar_lists):
    """
    .. code-block:: python

        _input = {
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
    case = request.param
    speed = correct_speed({
        ('yaml', None): PS_500,
        ('yaml', 'yaml'): PS_250,
        ('json', 'csv'): PS_10_000
    }, {
        'xml-sa': PS_2_500
    }, name := case.name, case.speed, dissimilar_lists.name, dissimilar_lists.speed, 0.5)

    _dict = case.func(
        source := make_dict([KEYS[6]], [[dissimilar_lists.list1, dissimilar_lists.list2]]))

    if (_name := dissimilar_lists.name) is not None:
        output_map = dissimilar_lists.output_map1[1]
        if 'xml' in _name:
            output_map[DATA_KEY1][DATA_KEY2].update(
                dissimilar_lists.output_map2[1][DATA_KEY1][DATA_KEY2])

        else:
            output_map.update(dissimilar_lists.output_map2[1])

        output_map = [_name, output_map]

    else:
        output_map = dissimilar_lists.output_map1
        output_map.update(dissimilar_lists.output_map2)

    output_map = {KEYS[6]: output_map}
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)

    if name is not None:
        output_map = [name, output_map]

    # Build results:
    res = dissimilar_lists.result_set[COM]
    copier = res[0][2].copy()
    copier.update(res[1][2])
    red_result = [copier]

    return DictSet(source, _dict, output_map, {
        COM: res[0] + res[1],
        TAN: res[0] + res[1],
        RED: red_result,
        ACC: [make_dict(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6])],
    }, speed, (name, dissimilar_lists.name))


@dict_fixture
def two_nested_lists_under_keys(request, dissimilar_lists):
    """
    .. code-block:: python

        _input = {
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
    case = request.param
    speed = correct_speed({
        ('yaml', None): PS_500
    }, {}, name := case.name, case.speed, dissimilar_lists.name, dissimilar_lists.speed, 1 / 3)

    _dict = case.func(
        source := make_dict(KEYS[6:8], [dissimilar_lists.list1, dissimilar_lists.list2]))

    output_map = {KEYS[6]: dissimilar_lists.output_map1, KEYS[7]: dissimilar_lists.output_map2}
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)

    if name is not None:
        output_map = [name, output_map]

    # Build results:
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

    return DictSet(source, _dict, output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [make_dict(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6])],
    }, speed, (name, dissimilar_lists.name))


@dict_fixture
def dict_with_list_of_dicts(request):
    """
    .. code-block:: python

        _input = {
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
    case = request.param
    speed = correct_speed({}, {
        None: PS_20_000,
        'json': PS_14_000,
        'yaml': PS_500
    }, name := case.name, case.speed)

    output_map = {KEYS[0]: {KEYS[1]: {KEYS[2]: make_dict(KEYS[3:9], OUT_KEYS[3:9])}}}
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)

    if name is not None:
        output_map = [name, output_map]

    # Build results AND input:
    mul_result = []
    tan_result = []
    red_result = [dict(zip(OUT_KEYS[3:6], VALS1))]
    red_result[0].update(dict(zip(OUT_KEYS[6:9], VALS2)))
    acc_result = [{k: [v] for k, v in red_result[0].items()}]

    source = {KEYS[0]: {KEYS[1]: []}}
    _list = source[KEYS[0]][KEYS[1]]
    for i in range(3):
        _list.append({KEYS[2]: {KEYS[3 + i]: VALS1[i]}})
        _list.append({KEYS[2]: {KEYS[6 + i]: VALS2[i]}})
        mul_result.append({OUT_KEYS[3 + i]: VALS1[i]})
        mul_result.append({OUT_KEYS[6 + i]: VALS2[i]})
        tan_result.append({OUT_KEYS[3 + i]: VALS1[i]})
        tan_result.append({OUT_KEYS[6 + i]: VALS2[i]})

    _dict = case.func(source)

    return DictSet(source, _dict, output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: acc_result,
    }, speed, name)


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
    case = request.param
    speed = correct_speed({
        ('json', None): PS_14_000,
        ('yaml', None): PS_250
    }, {
        'yaml': PS_800
    }, name := case.name, case.speed, dissimilar_lists.name, dissimilar_lists.speed, 1 / 3)

    _dict = case.func(source := make_dict(KEYS[6:8],
                                          [{KEYS[8]: dissimilar_lists.list1},
                                           {KEYS[9]: dissimilar_lists.list2}]))

    output_map = {KEYS[6]: {KEYS[8]: dissimilar_lists.output_map1},
                  KEYS[7]: {KEYS[9]: dissimilar_lists.output_map2}}
    if (output_modifier := case.output_modifier) is not None:
        output_map = nest_under_keys(output_map, *output_modifier)

    if name is not None:
        output_map = [name, output_map]

    # Build results:
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

    return DictSet(source, _dict, output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:6], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6]))],
    }, speed, name)


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
    case = request.param
    speed = correct_speed({}, {}, name := case.name, case.speed,
                          (dissimilar_lists.name, more_dissimilar_lists.name),
                          (dissimilar_lists.speed, more_dissimilar_lists.speed),
                          calc=lambda x, y: min(x, *y) / 6)

    source = make_dict([KEYS[12], KEYS[15]],
                       [
                           {
                               KEYS[13]: dissimilar_lists.list1,
                               KEYS[14]: dissimilar_lists.list2
                           },
                           {
                               KEYS[16]: more_dissimilar_lists.list1,
                               KEYS[17]: more_dissimilar_lists.list2
                           }
                       ])
    _dict = case.func(source)

    output_map = {
        KEYS[12]: {
            KEYS[13]: dissimilar_lists.output_map1,
            KEYS[14]: dissimilar_lists.output_map2
        },
        KEYS[15]: {
            KEYS[16]: more_dissimilar_lists.output_map1,
            KEYS[17]: more_dissimilar_lists.output_map2
        }
    }
    if case.output_modifier is not None:
        output_map = {DATA_KEY1: output_map}

    if name is not None:
        output_map = [name, output_map]

    # Build results:
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

    return DictSet(source, _dict, output_map, {
        COM: mul_result,
        TAN: tan_result,
        RED: red_result,
        ACC: [dict(zip(OUT_KEYS[:12], [VALS1, VALS2, VALS3, VALS4, VALS5, VALS6,
                                       VALS7, VALS8, VALS9, VALS10, VALS11, VALS12]))],
    }, speed, (name, dissimilar_lists.name, more_dissimilar_lists.name))


@pytest.fixture(params=(
    {KEYS[0]: {KEYS[1]: {KEYS[3]: VALS2[0]}}},
    {KEYS[0]: {KEYS[1]: {}}},
    {KEYS[0]: {KEYS[1]: None}},
    {KEYS[0]: {KEYS[2]: VALS2[0]}},
    {KEYS[0]: {}},
    {KEYS[0]: None}
), ids=(
    'Last key different',
    'last no keys',
    'last None',
    'second value',
    'second no keys',
    'second None'
))
def danger_dict(request): return {KEYS[0]: {KEYS[1]: {KEYS[2]: OUT_KEYS[2]}}}, request.param


@pytest.fixture(params=(
    {KEYS[0]: {KEYS[1]: {KEYS[3]: VALS2[0]}}, KEYS[1]: VALS1[0]},
    {KEYS[0]: {KEYS[1]: {}}, KEYS[1]: VALS1[0]},
    {KEYS[0]: {KEYS[1]: None}, KEYS[1]: VALS1[0]},
    {KEYS[0]: {KEYS[2]: VALS2[0]}, KEYS[1]: VALS1[0]},
    {KEYS[0]: {}, KEYS[1]: VALS1[0]},
    {KEYS[0]: None, KEYS[1]: VALS1[0]}
), ids=(
    'Last key different',
    'last no keys',
    'last None',
    'second value',
    'second no keys',
    'second None'
))
def less_danger_dict(request):
    return {
        KEYS[0]: {
            KEYS[1]: {
                KEYS[2]: OUT_KEYS[2],
            },
        },
        KEYS[1]: OUT_KEYS[1],
    }, request.param


class TestMultiplicative:
    name = COM
    pick_type = PickType.COMBINATORIAL

    def test_simple_lists(self, similar_lists):
        t = similar_lists
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        t = dicts_with_one_nested_list
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        t = dict_with_two_nested_similar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        t = dict_with_two_nested_dissimilar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        t = two_nested_lists_under_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        t = dict_with_list_of_dicts
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        t = two_nested_lists_under_double_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_complicated_dict1(self, complicated_dict1):
        t = complicated_dict1
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_danger_dict(self, danger_dict):
        output_map, _dict = danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert len(ans) == 0

    def test_less_danger_dict(self, less_danger_dict):
        output_map, _dict = less_danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert ans == [{OUT_KEYS[1]: VALS1[0]}]


class TestTandem:
    name = TAN
    pick_type = PickType.TANDEM

    def test_simple_lists(self, similar_lists):
        t = similar_lists
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        t = dicts_with_one_nested_list
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        t = dict_with_two_nested_similar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        t = dict_with_two_nested_dissimilar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        t = two_nested_lists_under_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        t = dict_with_list_of_dicts
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        t = two_nested_lists_under_double_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_complicated_dict1(self, complicated_dict1):
        t = complicated_dict1
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_danger_dict(self, danger_dict):
        output_map, _dict = danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert len(ans) == 0

    def test_less_danger_dict(self, less_danger_dict):
        output_map, _dict = less_danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert ans == [{OUT_KEYS[1]: VALS1[0]}]


class TestReduce:
    name = RED
    pick_type = PickType.REDUCE

    def test_simple_lists(self, similar_lists):
        t = similar_lists
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        t = dicts_with_one_nested_list
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        t = dict_with_two_nested_similar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        t = dict_with_two_nested_dissimilar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        t = two_nested_lists_under_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        t = dict_with_list_of_dicts
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        t = two_nested_lists_under_double_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_complicated_dict1(self, complicated_dict1):
        t = complicated_dict1
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_danger_dict(self, danger_dict):
        output_map, _dict = danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert len(ans) == 0

    def test_less_danger_dict(self, less_danger_dict):
        output_map, _dict = less_danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert ans == [{OUT_KEYS[1]: VALS1[0]}]


class TestAccumulate:
    name = ACC
    pick_type = PickType.ACCUMULATE

    def test_simple_lists(self, similar_lists):
        t = similar_lists
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_single_dict_nested_lists(self, dicts_with_one_nested_list):
        t = dicts_with_one_nested_list
        ans = pick(t.output_map1, t.list1, self.pick_type)
        assert ans == t.result_set[self.name][0]

        ans = pick(t.output_map2, t.list2, self.pick_type)
        assert ans == t.result_set[self.name][1]

    def test_dict_nested_lists_in_list(self, dict_with_two_nested_similar_lists_in_list):
        t = dict_with_two_nested_similar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_in_list(
            self,
            dict_with_two_nested_dissimilar_lists_in_list
    ):
        t = dict_with_two_nested_dissimilar_lists_in_list
        ans = pick(t.output_map, t.dict, self.pick_type)
        assert ans == t.result_set[self.name]

    def test_dict_nested_dissimilar_lists_under_keys(self, two_nested_lists_under_keys):
        t = two_nested_lists_under_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_with_list_of_dicts(self, dict_with_list_of_dicts):
        t = dict_with_list_of_dicts
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_dict_nested_dissimilar_lists_under_double_keys(
            self,
            two_nested_lists_under_double_keys
    ):
        t = two_nested_lists_under_double_keys
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_complicated_dict1(self, complicated_dict1):
        t = complicated_dict1
        ans = pick(t.output_map, t.dict, self.pick_type)
        compare_lists_of_dicts_unordered(ans, t.result_set[self.name])

    def test_danger_dict(self, danger_dict):
        output_map, _dict = danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert len(ans) == 1

    def test_less_danger_dict(self, less_danger_dict):
        output_map, _dict = less_danger_dict
        ans = pick(output_map, _dict, self.pick_type)
        assert ans == [{OUT_KEYS[1]: [VALS1[0]]}]
