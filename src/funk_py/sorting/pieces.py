import io
import xml.etree.ElementTree as ET
import json
import csv
from enum import IntEnum

import yaml
from typing import Mapping, Any, Literal, Union, List, Dict


class PickType(IntEnum):
    MULTIPLIED = 0
    ADDITIVE = 1
    NESTED = 2


def pick(
        output_map: Union[Mapping, List[Union[Literal['json', 'xml', 'xml-sa', 'e-list', 'list',
                                                      'csv', 'yaml'], str, Mapping]]],
        _input: Any,
        list_handling_method: PickType = PickType.MULTIPLIED) -> list:
    builder = []
    static_builder = {}

    if isinstance(output_map, list):
        worker = parse_type_as(output_map[0], _input)
        output_map = output_map[1]

    elif isinstance(output_map, str):
        builder.append({output_map: _input})
        return builder

    else:
        worker = _input

    if isinstance(worker, list):
        for item in worker:
            builder.extend(pick(output_map, item))

    else:
        output_map_iter = iter(output_map.items())

        not_found = True
        while not_found:
            try:
                path, instruction = next(output_map_iter)
                if path in worker:
                    if isinstance(instruction, str):
                        static_builder[instruction] = worker[path]
                        builder.append({})

                    else:
                        builder.extend(pick(instruction, worker[path]))

                    not_found = False

            except StopIteration:
                return []

        for path, instruction in output_map_iter:
            if path in worker:
                if isinstance(instruction, str):
                    static_builder[instruction] = worker[path]

                else:
                    ans = pick(instruction, worker[path])
                    if len(ans) != 1:
                        for i in range(len(builder)):
                            for _ans in ans[1:]:
                                copier = builder[i].copy()
                                copier.update(_ans)
                                builder.append(copier)

                            builder[i].update(ans[0])

                    else:
                        for source in builder:
                            source.update(ans[0])

        for result in builder:
            result.update(static_builder)

    return builder


def parse_type_as(
        _type: Literal['json', 'xml', 'xml-sa', 'e-list', 'list', 'csv', 'yaml'],
        data: Any) -> Union[dict, list]:
    if _type == 'json':
        return json.loads(data)

    elif _type == 'jsonl':
        return jsonl_to_json(data)

    elif _type == 'json\'':
        return wonky_json_to_json(data)

    elif _type == 'xml':
        return xml_to_json(data)

    elif _type == 'xml-sa':
        return xml_to_json(data, True)

    elif _type == 'e-list':
        return data if isinstance(data, list) else [data]

    elif _type == 'csv':
        return csv_to_json(data)

    elif _type == 'list':
        return data.split(',')

    elif _type == 'yaml':
        return yaml.safe_load(data)

    else:
        raise ValueError('Invalid type specified.')


def csv_to_json(data: str):
    builder = []
    csv_reader = csv.reader(io.StringIO(data))
    headers = [header.strip() for header in next(csv_reader)]
    for row in csv_reader:
        builder.append(dict(zip(headers, [val.strip() for val in row])))

    return builder


def xml_to_json(data: str, sans_attributes: bool = False):
    """
    Converts XML data to a JSON representation

    :param data: The XML data to parse.
    :param sans_attributes: Whether to exclude attributes from the JSON output.
    :return: The JSON representation of the XML data.
    """
    root = ET.fromstring(data)
    return {root.tag: _parse_xml_internal(root, sans_attributes)}


def _parse_xml_internal(element: ET.Element, sans_attributes: bool) -> Union[dict, str]:
    """
    Recursively parses XML elements.

    :param element: The XML element to be processed.
    :param sans_attributes: Whether to exclude attributes from the JSON output.
    :return: The JSON representation of the XML data.
    """
    builder = {}
    counts = _get_xml_element_internal_names(element)
    for ele in element:
        t = ele.tag
        if counts[t] > 1:
            if t in builder:
                builder[t].append(_parse_xml_internal(ele, sans_attributes))

            else:
                builder[t] = [_parse_xml_internal(ele, sans_attributes)]

        else:
            builder[t] = _parse_xml_internal(ele, sans_attributes)

    if sans_attributes:
        if not len(builder):
            if (t := element.text) is None:
                return element.attrib.copy()

            return t

    else:
        builder.update(element.attrib)
        builder['text'] = element.text

    return builder


def _get_xml_element_internal_names(element: ET.Element) -> Dict[str, int]:
    """
    Counts the occurrences of each tag among the children of an XML element.

    :param element: The XML element.
    :return: A ``dict`` containing tag names as keys and the count of their
        occurrences as values.
    """
    builder = {}
    for ele in element:
        t = ele.tag
        builder[t] = builder.get(t, 0) + 1

    return builder


def wonky_json_to_json(data: str, different_quote: str = '\''):
    if len(different_quote) > 1:
        raise ValueError('You cannot use a multi-character quote (yet).')

    # Split the string around escaped occurrences of different_quote to avoid mutating escaped
    # instances of different_quote in further steps.
    around_escaped = data.split('\\' + different_quote)

    # Replace all double quotes with escaped double quotes, wouldn't want them to mess up JSON
    # parsing.
    around_escaped = [p.replace('"', '\\"') for p in around_escaped]

    # Replace all instances of different_quote with double quotes.
    around_escaped = [p.replace(different_quote, '"') for p in around_escaped]

    # Join it all back together using different_quote. We use an unescaped form because it would
    # no-longer require escaping in its new form.
    data = different_quote.join(around_escaped)

    # Now parse the json string. Good luck and hope this works every time.
    return json.loads(data)


def jsonl_to_json(data: str):
    return [json.loads(p) for p in data.split('\n')]
