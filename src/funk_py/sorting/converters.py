import csv
import io
import json
from typing import Union, Dict, List, Tuple, Optional, Any
from xml.etree import ElementTree as ET

from funk_py.sorting.dict_manip import align_to_list, acc_

TEXT = 'text'


def csv_to_json(data: str) -> list:
    """
    Converts a CSV string to a list of json dicts. Will use the first row as the keys for all other
    rows.

    :param data: The ``str`` to be converted.
    :return: A ``list`` of the rows as ``dict`` items.
    """
    builder = []
    csv_reader = csv.reader(io.StringIO(data))
    headers = [header.strip() for header in next(csv_reader)]
    for row in csv_reader:
        builder.append(dict(zip(headers, [val.strip() for val in row])))

    return builder


def json_to_csv(data: List[dict]) -> str:
    """
    Converts a list of dictionaries to a CSV string. Will check every item to determine needed
    headers.

    :param data: The ``list`` to convert.
    :return: A ``str`` of the items in ``data`` converted to CSV.
    """
    if len(data):
        if type(data[0]) is dict:
            headers = set(data[0].keys())
            for i in range(1, len(data)):
                if type(data[i]) is dict:
                    headers.update(data[i].keys())

                else:
                    raise TypeError('Items must be dictionaries.')

            headers = list(headers)
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(headers)
            for row in data:
                writer.writerow(align_to_list(headers, row))

            return output.getvalue()

        raise TypeError('Items must be dictionaries.')

    return ''


def xml_to_json(data: str, sans_attributes: bool = False):
    """
    Converts XML data to a JSON representation. Attributes will be interpreted as keys of a dict, as
    will tags within elements. If there are multiple of a tag within one element, the values inside
    of those tags will be treated as individual items and added to a list under that tag as a key.
    Genuine text values of elements will be included in dicts under the key ``'text'``. If
    sans_attributes is ``True``, then attributes will not be considered as keys unless there are
    no internal elements and no text, in which case they will be included.

    Example:

    .. code-block:: python

        data = '''<a>
            <b>
                <c d="e" f="g"/>
                <h>i</h>
            </b>
            <j>
                <k>
                    <l m="o" n="r"/>
                    <l m="p" n="s">t</l>
                    <l m="q">u</l>
                    <l m="v">w</l>
                    <x z="aa">
                        <y>ab</y>
                        <y>ac</y>
                    </x>
                </k>
            </j>
        </a>'''

        xml = xml_to_json(data)

        # xml == {
        #     'a': {
        #         'b': {
        #             'c': {'d': 'e', 'f': 'g', 'text': None},
        #             'h': {'text': 'i'},
        #             'text': str
        #         },
        #         'j': {
        #             'k': {
        #                 'l': [
        #                     {'m': 'o', 'n': 'r', 'text': None},
        #                     {'m': 'p', 'n': 's', 'text': 't'},
        #                     {'m': 'q', 'text': 'u'},
        #                     {'m': 'v', 'text': 'w'}
        #                 ],
        #                 'x': {
        #                     'y': [
        #                         {'text': 'ab'},
        #                         {'text': 'ac'}
        #                     ],
        #                     'z': 'aa',
        #                     'text': str
        #                 },
        #                 'text': str
        #             },
        #             'text': str
        #         },
        #         'text': str
        #     }
        # }

        xml_sa = xml_to_json(data, True)

        # xml_sa == {
        #     'a': {
        #         'b': {
        #             'c': {'d': 'e', 'f': 'g'},
        #             'h': 'i'
        #         },
        #         'j': {
        #             'k': {
        #                 'l': [{'m': 'o', 'n':'r'}, 't', 'u', 'w'],
        #                 'x': {
        #                     'y': ['ab', 'ac']
        #                 }
        #             }
        #         }
        #     }
        # }

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

            return str(t)

    else:
        builder.update(element.attrib)
        if element.text is None:
            return builder

        else:
            builder['text'] = str(element.text)
            if len(builder) == 1:
                builder = builder['text']

    return builder


def _get_xml_element_internal_names(element: ET.Element) -> Dict[str, int]:
    """
    Counts the occurrences of each tag among the children of an XML element.

    :param element: The XML element.
    :return: A ``dict`` containing tag names as keys and the count of their occurrences as values.
    """
    builder = {}
    for ele in element:
        t = ele.tag
        builder[t] = builder.get(t, 0) + 1

    return builder


def json_to_xml(data: dict, favor_attributes: bool = False,
                avoid_text_and_elements: bool = True):
    """
    Converts JSON data to an XML representation. If ``favor_attributes`` is ``True`` then:

        - Should a value be a dictionary, it will be interpreted as a contained element.
        - Should a value be a list, it will be interpreted as a series of XML elements with the same
          tag.
        - If a value is not a dictionary or a list, it will be stored under the current element as
          an attribute labeled with its key.


    If ``favor_attributes`` is ``False``:

        - Should a value be a dictionary, it will be interpreted as a contained element.
        - Should a value be a list, it will be interpreted as a series of XML elements with the same
          tag.
        - If a value is not a dictionary or a list, it will be stored as the text of an element with
          its key as a tag.

    If ``

    As long as ``avoid_text_and_elements`` is ``True``, if the key ``'text'`` is present, behavior
    will be overriden, and the value under ``'text'`` will be used as the text of an element, while
    any other pairs will be entered as attributes. A non-dictionary value in a list will also be
    interpreted as the text of a containing element.

    In the case that ``avoid_text_and_elements`` is ``False``, any other pairs will be interpreted
    as elements, so long as ``favor_attributes`` is not ``True``.

    Example:

    .. code-block:: python

        data = {
            'a': {
                'b': {
                    'c': {'text': '', 'd': 'e', 'f': 'g'},
                    'h': 'i'
                },
                'j': {
                    'k': {
                        'l': [
                            {'m': 'o', 'n': 'r'},
                            {'m': 'p', 'n': 's', 'text': t},
                            [{'m': 'q'}, 'u'],
                            {'m': 'v', 'text': 'w'}
                        ],
                        'x': {
                            'y': ['ab', 'ac']
                        }
                    }
                }
            }
        }

        xml = json_to_xml(data)

        # xml == ('<a>'
        #         '<b>'
        #         '<c d="e" f="g" />'
        #         '<h>i</h>'
        #         '</b>'
        #         '<j>'
        #         '<k>'
        #         '<l>'
        #         '<m>o</m>'
        #         '<n>r</n>'
        #         '</l>'
        #         '<l m="p" n="s">t</l>'
        #         '<l m="q">u</l>'
        #         '<l m="v">w</l>'
        #         '<x>'
        #         '<y>ab</y>'
        #         '<y>ac</y>'
        #         '</x>'
        #         '</k>'
        #         '</j>'
        #         '</a>')

        xml_chaos = json_to_xml(data, avoid_text_and_elements=False)

        # xml_chaos == ('<a>'
        #               '<b>'
        #               '<c>'
        #               '<d>e</d>'
        #               '<f>g</f>'
        #               '</c>'
        #               '<h>i</h>'
        #               '</b>'
        #               '<j>'
        #               '<k>'
        #               '<l>'
        #               '<m>o</m>'
        #               '<n>r</n>'
        #               '</l>'
        #               '<l>t'
        #               '<m>p</m>'
        #               '<n>s</n>'
        #               '</l>'
        #               '<l>u'
        #               '<m>q</m>
        #               '</l>'
        #               '<l>w'
        #               '<m>v</m>'
        #               '</l>'
        #               '<x>'
        #               '<y>ab</y>'
        #               '<y>ac</y>'
        #               '</x>'
        #               '</k>'
        #               '</j>'
        #               '</a>')

        xml_fa = json_to_xml(data, True)

        # xml_fa == ('<a>'
        #            '<b h="i">'
        #            '<c d="e" f="g" />'
        #            '</b>'
        #            '<j>'
        #            '<k>'
        #            '<l m="o" n="r" />'
        #            '<l m="p" n="s">t</l>'
        #            '<l m="q">u</l>'
        #            '<l m="v">w</l>'
        #            '<x>'
        #            '<y>ab</y>'
        #            '<y>ac</y>'
        #            '</x>'
        #            '</k>'
        #            '</j>'
        #            '</a>')

    :param data: The JSON data to convert.
    :type data: dict
    :param favor_attributes: Whether to favor storing values as attributes or not.
    :type favor_attributes: bool
    :param avoid_text_and_elements: If ``True``, then attempts will be made to avoid an element
        having both text and internal elements. If ``False``, no such attempts will be made.
    :type avoid_text_and_elements: bool
    :return: A string representing the JSON object converted to an XML format.
    """
    if len(data) == 1:
        root = ET.Element(key := list(data.keys())[0])
        if (t := type(data[key])) is dict:
            attributes, elements, text = _json_dict_to_element(data[key], favor_attributes,
                                                               avoid_text_and_elements)
            root.attrib.update(attributes)
            for element in elements:
                root.append(element)

            if text:
                root.text = text

        elif t is list:
            for v in data[key]:
                _, elements, _ = _json_dict_to_element(v, favor_attributes, avoid_text_and_elements)
                for element in elements:
                    root.append(element)

        else:
            root.text = str(data[key])

        return ET.tostring(root).decode()

    elif len(data) > 1:
        raise ValueError('The root dictionary should only have one key to generate XML data.')

    raise ValueError('Why have you done this? Whatever you passed to json_to_xml had a length, but '
                     'could not be converted.')


def _json_dict_to_element(
        data: Any,
        fa: bool,
        ave: bool = True
) -> Tuple[dict, List[ET.Element], Optional[str]]:
    text = None
    attributes = {}
    elements = []

    def add_element(key, val):
        elements.append(current := ET.Element(str(key)))
        if val is not None:
            current.text = str(val)

    def add_attribute(key, val):
        attributes[str(key)] = str(val)

    if isinstance(data, dict):
        text = data.get(TEXT)
        if TEXT in data:
            text = str(text) if text is not None else None
            # We KNOW the element we're sending data back to has text. The best course is to
            # avoid adding elements to that element unless attributes are not favored AND the user
            # explicitly wants elements to be valid within elements that have text.
            if fa or ave:
                for k, v in data.items():
                    if k != TEXT:
                        _parse_pair_to_elements(elements, attributes, k, v, fa, ave, add_attribute)

            else:
                for k, v in data.items():
                    if k != TEXT:
                        _parse_pair_to_elements(elements, attributes, k, v, fa, ave, add_element)

        elif fa:
            for k, v in data.items():
                _parse_pair_to_elements(elements, attributes, k, v, fa, ave, add_attribute)

        else:
            for k, v in data.items():
                _parse_pair_to_elements(elements, attributes, k, v, fa, ave, add_element)

    return attributes, elements, str(text) if text is not None else None


def _parse_dict_to_element(tag: Any, val: dict, fa, ave):
    attributes, elements, text = _json_dict_to_element(val, fa, ave)
    current = ET.Element(str(tag), attributes)
    if len(elements):
        for element in elements:
            current.append(element)

    if text is not None:
        current.text = str(text)

    return current


def _parse_list_in_list_to_elements(tag: Any, val: list, fa, ave):
    building = False
    __text = _text = None
    for v in val:
        if not isinstance(v, dict):
            __text = v

    if __text is not None and ave:
        fa = True

    for v in val:
        if isinstance(v, dict):
            attributes, elements, text = _json_dict_to_element(v, fa, ave)
            if len(attributes) or len(elements):
                if not building:
                    current = ET.Element(str(tag))
                    building = True

                for element in elements:
                    current.append(element)

                current.attrib.update(attributes)

            if text:
                _text = text

    __text = _text if __text is None else __text
    if not building:
        current = ET.Element(str(tag))

    if __text is not None:
        current.text = str(__text)

    else:
        output = []
        for v in val:
            if isinstance(v, dict):
                attributes, elements, text = _json_dict_to_element(v, fa, ave)
                if len(attributes) or len(elements):
                    output.append(current := ET.Element(str(tag), attributes))
                    for element in elements:
                        current.append(element)

        return output

    return [current]


def _parse_dict_in_list_to_elements(tag: Any, val: dict, fa, ave):
    current = None
    attributes, elements, text = _json_dict_to_element(val, fa, ave)
    if len(attributes) or len(elements) or len(text):
        current = ET.Element(str(tag), attributes)
        for element in elements:
            current.append(element)

        current.text = text

    return current


def _parse_pair_to_elements(elements: list, attributes: dict, key: Any, val: Any, fa, ave,
                            default: callable):
    if isinstance(val, dict):
        # Not much choice if it's a dictionary, a new element must be generated.
        elements.append(_parse_dict_to_element(key, val, fa, ave))

    elif isinstance(val, list):
        list_handler = {}
        for v in val:
            if isinstance(v, dict):
                if (t := _parse_dict_in_list_to_elements(key, v, fa, ave)) is not None:
                    elements.append(t)

                else:
                    acc_(list_handler, key, v)
                    default(key, v)

            elif isinstance(v, list):
                elements.extend(_parse_list_in_list_to_elements(key, v, fa, ave))

            else:
                acc_(list_handler, key, v)
                default(key, v)

        # The below handles making elements if a list was mistakenly erased.
        # It is possible to mistakenly store list elements into an attribute, overwriting one after
        # another, so this restores the entire list (if necessary) by removing the attribute and
        # adding all the values that were encountered for the list as elements.
        for k, v in list_handler.items():
            if len(v) > 1:
                if k in attributes:
                    del attributes[k]
                    for _v in v:
                        elements.append(current := ET.Element(k))
                        current.text = _v

    else:
        default(key, val)


def wonky_json_to_json(data: str, different_quote: str = '\''):
    """
    Converts a JSON-like string that uses a non-standard quote character into valid JSON. At least,
    it tries to.

    :param data: The JSON-like string to be converted to a ``dict`` or ``list``.
    :param different_quote: The different quote that was used for the string.
    :return: The string converted to a ``dict`` or ``list``, depending on what was encoded.
    """
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


def jsonl_to_json(data: str) -> list:
    """
    Converts a JSONL string to a list of objects.

    :param data: The JSONL string to convert.
    :return: A ``list`` containing the ``dict`` and ``list`` items stored in the JSONL string.
    """
    return [json.loads(p) for p in data.split('\n')]
