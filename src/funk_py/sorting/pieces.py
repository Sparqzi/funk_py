import io
import xml.etree.ElementTree as ET
import json
import csv
from enum import IntEnum
from typing import Mapping, Any, Literal, Union, List, Dict, Tuple, Optional, Iterator, Generator, \
    Callable

import yaml

from funk_py.modularity.logging import make_logger


main_logger = make_logger('pieces', 'PIECES_LOG_LEVEL', default_level='warning')

main_logger.info('Setting up simple types...')
OutputMapType = (
    Union[Mapping,
          List[Union[str,
                     Mapping,
                     Literal['json',
                             'jsonl',
                             'json\'',
                             'xml',
                             'xml-sa',
                             'e-list',
                             'list',
                             'csv',
                             'yaml']]]])
PickProcessFunc = Callable[[list, list, dict], None]
PickFinalFunc = Callable[[list, dict], None]


class PickType(IntEnum):
    MULTIPLICATIVE = 0
    TANDEM = 1


main_logger.info('Finished setting up simple types.')


def pick(
        output_map: OutputMapType,
        _input: Any,
        list_handling_method: PickType = PickType.MULTIPLICATIVE
) -> list:
    if list_handling_method == PickType.MULTIPLICATIVE:
        return _pick(
            output_map,
            _input,
            _mul_tan_start_and_list_func,
            _mul_tan_start_and_list_func,
            _mul_iter_func,
            _mul_tan_final_func
        )
    elif list_handling_method == PickType.TANDEM:
        return _pick(
            output_map,
            _input,
            _mul_tan_start_and_list_func,
            _mul_tan_start_and_list_func,
            _tan_iter_func,
            _mul_tan_final_func
        )


def _pick_setup(
        output_map: OutputMapType,
        _input: Any
) -> Tuple[Optional[OutputMapType], Any, list, bool]:
    if isinstance(output_map, list):
        # If the output_map is a list, that should mean the user specified a type of conversion to
        # enact on the input (as long as their output_map is valid).
        if isinstance(_input, list) and output_map[0] != 'e-list':
            # In the case that _input is a list, we should first check if the user specified e-list
            # since that means "expected list". If they did specify that, we'll want to consume it,
            # so this branch won't execute, and we'll move over to the next step. If they didn't, we
            # continue on our mary way, and don't move forward on the output_map yet. We want to
            # pass the non-mutated _input as well since there's no mutation to be performed on it.
            return output_map, _input, [], False

        else:
            # In the case that _input is not a list, we will just attempt to parse as the user
            # expected.
            try:
                worker = parse_type_as(output_map[0], _input)

            except Exception as e:
                main_logger.warning(f'User\'s expected parsing method failed. Exception raised: '
                                    f'{e}')
                return None, None, [], True

            return output_map[1], worker, [], False

    elif isinstance(output_map, str):
        # Theoretically, we should never get here, but just in case, this line should catch
        # instances where a key is immediately requested. Who knows, maybe a change down the line
        # will cause this code to be needed.
        return None, None, [{output_map: _input}], False

    # If nothing caught, just pass everything back as-is.
    return output_map, _input, [], False


def _find_and_follow_first_path_in_pick(
        output_map_iter: Iterator,
        worker: Any,
        builder: list,
        static_builder: dict
) -> Tuple[Optional[OutputMapType], Any, bool]:
    while True:
        try:
            path, instruction = next(output_map_iter)
            if path in worker:
                if isinstance(instruction, str):
                    if not isinstance(worker, dict):
                        main_logger.warning(f'An unexpected value was encountered in pick attempt. '
                                            f'a path has now been skipped. value = {worker}')
                        return None, None, False

                    static_builder[instruction] = worker[path]
                    builder.append({})
                    # The caller doesn't need to call anything, we did everything needed for the
                    # first key.
                    return None, None, False

                else:
                    # Rather than recursively calling a function from inside of this function, we
                    # pass back the values that the caller needs to use to call the function itself.
                    # This is done this way to limit how deep we go on the stack. It also means the
                    # caller can decide which function to call on the values.
                    return instruction, worker[path], False

        except StopIteration:
            # Welp, the caller will have to return immediately, none of the paths requested were
            # present.
            return None, None, True


def _pick_iter(
        output_map_iter: Iterator,
        worker: Any,
        builder: list,
        static_builder: dict,
        func: Callable[[list, list, dict], None]
) -> Generator[Tuple[Optional[OutputMapType], Any, bool], list, None]:
    """
    Finishes iterating after the first path was successfully followed. Expects the result of an
    external function call to be sent to it if it yields an instruction.
    """
    for path, instruction in output_map_iter:
        if path in worker:
            if isinstance(instruction, str):
                static_builder[instruction] = worker[path]

            else:
                # Rather than recursively calling a function from inside of this function, we
                # pass back the values that the caller needs to use to call the function itself.
                # This is done this way to limit how deep we go on the stack. It also means the
                # caller can decide which function to call on the values.
                # The caller should send the result of the function back to us here so that we can
                # call func on it.
                result = yield instruction, worker[path], False
                func(result, builder, static_builder)

    yield None, None, True


def _pick(
        output_map: OutputMapType,
        _input: Any,
        start_func: PickProcessFunc,
        list_func: PickProcessFunc,
        iter_func: PickProcessFunc,
        final_func: PickFinalFunc
) -> list:
    """
    The core of :func:`pick`. All pick types run through this method.

    :param output_map: The map which describes how incoming data should be parsed.
    :param _input: The incoming data.
    :param start_func: The function that should be used when parsing a list of results for ingestion
        into the list being built.
    :param iter_func: The function that should be used to parse a list of results during iteration
        over the ``output_map``.
    :param final_func: The function which should be called to finalize the result at the end of
        retrieving all possible data.
    :return:
    """
    static_builder = {}
    output_map, worker, builder, fail = _pick_setup(output_map, _input)
    if fail or len(builder):
        return builder

    __pick = lambda o_map, w: _pick(o_map, w, start_func, list_func, iter_func, final_func)  # noqa

    if isinstance(worker, list):
        for item in worker:
            list_func(__pick(output_map, item), builder, static_builder)

    else:
        output_map_iter = iter(output_map.items())
        *instruction, return_now = _find_and_follow_first_path_in_pick(
            output_map_iter, worker, builder, static_builder)
        if return_now:
            return builder

        elif instruction[0] is not None:
            # If instructions were given by _find_and_follow_first_path_in_pick, then we need to
            # recursively call this function with the results.
            start_func(__pick(*instruction), builder, static_builder)

        pick_iter = _pick_iter(output_map_iter, worker, builder, static_builder, iter_func)

        for *instruction, return_now in pick_iter:
            if instruction[0] is not None:
                # If instructions were given by pick_iter, then we need to recursively call this
                # function and pass the results back to pick_iter.
                pick_iter.send(__pick(*instruction))

        final_func(builder, static_builder)

    return builder


def _mul_tan_start_and_list_func(ans: list, builder: list, static_builder: dict) -> None:
    builder.extend(ans)


def _mul_iter_func(ans: list, builder: list, static_builder: dict) -> None:
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


def _mul_tan_final_func(builder: list, static_builder: dict) -> None:
    for result in builder:
        result.update(static_builder)


def _tan_iter_func(ans: list, builder: list, static_builder: dict) -> None:
    if len(builder) >= len(ans):
        for i in range(len(ans)):
            builder[i].update(ans[i])

    else:
        for i in range(len(builder)):
            builder[i].update(ans[i])

        for i in range(len(builder), len(ans)):
            builder.append(ans[i])


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