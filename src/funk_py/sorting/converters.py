import csv
import io
import json
from typing import Union, Dict
from xml.etree import ElementTree as ET


def csv_to_json(data: str) -> list:
    """
    Converts a CSV string to a list of json dicts. Will use the first row as the keys for all other
    rows.

    :param data: The ``str`` to be converted.
    :return: A list of the rows as dictionaries.
    """
    builder = []
    csv_reader = csv.reader(io.StringIO(data))
    headers = [header.strip() for header in next(csv_reader)]
    for row in csv_reader:
        builder.append(dict(zip(headers, [val.strip() for val in row])))

    return builder


def xml_to_json(data: str, sans_attributes: bool = False):
    """
    Converts XML data to a JSON representation. Attributes will be interpreted as keys of a dict, as
    will tags within elements. If there are multiple of a tag within one element, the values inside
    of those tags will be treated as individual items and added to a list under that tag as a key.
    Genuine text values of elements will be included in dicts under the key ``'text'``. If
    sans_attributes is ``True``, then attributes will not be considered as keys unless there are
    no internal elements and no text, in which case they will be included.

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
