import json
from copy import deepcopy
from enum import Enum, IntEnum
from typing import Mapping, Any, Literal, Union, List, Tuple, Optional, Iterator, Generator, \
    Callable, Dict, Hashable, Iterable
from urllib.parse import parse_qs

import yaml

from funk_py.modularity.decoration.enums import converts_enums, CarrierEnum, ignore, special_member
from funk_py.modularity.logging import make_logger
from funk_py.sorting.converters import csv_to_json, xml_to_json, wonky_json_to_json, jsonl_to_json
from funk_py.sorting.dict_manip import convert_tuplish_dict, get_subset_values, get_subset

main_logger = make_logger('pieces', 'PIECES_LOG_LEVEL', default_level='warning')

Ls = List[str]
Ldct = List[dict]

main_logger.info('Setting up simple types...')
OutputMapSpecifier = Literal['json', 'jsonl', 'json\'',
                             'xml', 'xml-sa',
                             'e-list', 'list',
                             'csv',
                             'yaml',
                             'tuple-dict',
                             'form-urlencoded',
                             'combinatorial', 'tandem', 'reduce', 'accumulate']
PickProcessFunc = Callable[[list, list, dict], None]
PickFinalFunc = Callable[[list, dict], None]


class PickType(Enum):
    """
    ``PickType`` is an enum containing the valid pick types for :func:`pick`. Available types are
    ``COMBINATORIAL``, ``TANDEM``, ``REDUCE``, and ``ACCUMULATE``.
    """
    COMBINATORIAL = 'combinatorial'
    TANDEM = 'tandem'
    REDUCE = 'reduce'
    ACCUMULATE = 'accumulate'


class PickInstruction(Enum):
    """
    ``PickInstruction`` is an enum containing the valid pick instructions for :func:`pick`.
    Available instructions are ``JSON``, ``JSONL``, ``JSON_SINGLE_QUOTE``, ``XML``,
    ``XMLSA`` (XML sans-attributes), ``ELIST``, ``LIST``, ``CSV``, ``YAML``, ``TUPLE_DICT``,
    and ``FORM``. Members mimicking :class:`PickType`'s members are also available, and their use
    indicates that pick type should be changed before diving deeper into the original object.
    """
    JSON = 'json'
    JSONL = 'jsonl'
    JSON_SINGLE_QUOTE = 'json\''
    XML = 'xml'
    XMLSA = 'xml-sa'
    ELIST = 'e-list'
    LIST = 'list'
    CSV = 'csv'
    YAML = 'yaml'
    TUPLE_DICT = 'tuple-dict'
    FORM = 'form-urlencoded'

    COMBINATORIAL = 'combinatorial'
    TANDEM = 'tandem'
    REDUCE = 'reduce'
    ACCUMULATE = 'accumulate'


OutputMapType = Union[Mapping[str, Union[str, Mapping, PickInstruction]],
                      List[Union[str, Mapping, PickInstruction]]]


main_logger.info('Finished setting up simple types.')


def _com_tan_start_and_list_func(ans: list, builder: list, static_builder: dict) -> None:
    builder.extend(ans)


def _acc_start_list_and_iter_func(ans: list, builder: list, static_builder: dict) -> None:
    if not len(builder):
        builder.append({})
        for _ans in ans:
            for k, v in _ans.items():
                if isinstance(v, list):
                    builder[0][k] = v

                else:
                    builder[0][k] = [v]

    else:
        for _ans in ans:
            for k, v in _ans.items():
                if k in builder[0]:
                    if isinstance(v, list):
                        builder[0][k].extend(v)

                    else:
                        builder[0][k].append(v)

                elif isinstance(v, list):
                    builder[0][k] = v

                else:
                    builder[0][k] = [v]


def _com_iter_func(ans: list, builder: list, static_builder: dict) -> None:
    if (t := len(ans)) >= 1:
        for i in range(len(builder)):
            for _ans in ans[1:]:
                copier = builder[i].copy()
                copier.update(_ans)
                builder.append(copier)

            builder[i].update(ans[0])

    elif t == 1:
        for source in builder:
            source.update(ans[0])


def _tan_iter_func(ans: list, builder: list, static_builder: dict) -> None:
    if len(ans) == 0:
        return

    if len(builder) >= len(ans):
        for i in range(len(ans)):
            builder[i].update(ans[i])

    else:
        for i in range(len(builder)):
            builder[i].update(ans[i])

        for i in range(len(builder), len(ans)):
            builder.append(ans[i])


def _com_tan_final_func(builder: list, static_builder: dict) -> None:
    if len(static_builder) and not len(builder):
        builder.append(static_builder)
        return

    for result in builder:
        result.update(static_builder)


def _acc_final_func(builder: list, static_builder: dict) -> None:
    if not len(builder):
        builder.append(static_builder)

    else:
        for k, v in static_builder.items():
            if k in builder[0]:
                if isinstance(v, list):
                    builder[0][k].extend(v)

                else:
                    builder[0][k].append(v)

            elif isinstance(v, list):
                builder[0][k] = v

            else:
                builder[0][k] = [v]


_PICK_TYPE_DEFS = {
    PickType.COMBINATORIAL: (
        _com_tan_start_and_list_func,
        _com_tan_start_and_list_func,
        _com_iter_func,
        _com_tan_final_func,
    ),
    PickType.TANDEM: (
        _com_tan_start_and_list_func,
        _com_tan_start_and_list_func,
        _tan_iter_func,
        _com_tan_final_func,
    ),
    PickType.REDUCE: (
        _com_tan_start_and_list_func,
        _tan_iter_func,
        _com_iter_func,
        _com_tan_final_func,
    ),
    PickType.ACCUMULATE: (
        _acc_start_list_and_iter_func,
        _acc_start_list_and_iter_func,
        _acc_start_list_and_iter_func,
        _acc_final_func,
    ),
}
_PICK_TYPE_NAMES = {
    'combinatorial': _PICK_TYPE_DEFS[PickType.COMBINATORIAL],
    'tandem': _PICK_TYPE_DEFS[PickType.TANDEM],
    'reduce': _PICK_TYPE_DEFS[PickType.REDUCE],
    'accumulate': _PICK_TYPE_DEFS[PickType.ACCUMULATE],
}


def pick(
        output_map: OutputMapType,
        _input: Any,
        list_handling_method: PickType = PickType.COMBINATORIAL
) -> list:
    return _pick(output_map, _input, *_PICK_TYPE_DEFS[list_handling_method])


def _pick_setup(
        output_map: OutputMapType,
        _input: Any
) -> Tuple[Optional[OutputMapType], Any, list, bool, Optional[PickType]]:
    if isinstance(output_map, list):
        # If the output_map is a list, that should mean the user specified a type of conversion to
        # enact on the input (as long as their output_map is valid).
        if isinstance(_input, list) and output_map[0] != 'e-list':
            # In the case that _input is a list, we should first check if the user specified e-list
            # since that means "expected list". If they did specify that, we'll want to consume it,
            # so this branch won't execute, and we'll move over to the next step. If they didn't, we
            # continue on our mary way, and don't move forward on the output_map yet. We want to
            # pass the non-mutated _input as well since there's no mutation to be performed on it.
            return output_map, _input, [], False, None

        else:
            # In the case that _input is not a list, we will just attempt to parse as the user
            # expected.
            try:
                if (t := output_map[0]) in _PICK_TYPE_NAMES:
                    # This should handle cases where the user specifies changing modes during
                    # parsing.
                    return output_map[-1], _input, [], False, _PICK_TYPE_NAMES[t]

                worker = parse_type_as(output_map[0], _input, output_map[1:-1])

            except Exception as e:
                main_logger.warning(f'User\'s expected parsing method failed. Exception raised: '
                                    f'{e}')
                return None, None, [], True, None

            return output_map[-1], worker, [], False, None

    elif isinstance(output_map, str):
        # Theoretically, we should never get here, but just in case, this line should catch
        # instances where a key is immediately requested. Who knows, maybe a change down the line
        # will cause this code to be needed.
        return None, None, [{output_map: _input}], False, None

    # If nothing caught, just pass everything back as-is.
    return output_map, _input, [], False, None


def _find_and_follow_first_path_in_pick(
        output_map_iter: Iterator,
        worker: Any,
        builder: list,
        static_builder: dict
) -> Tuple[Optional[OutputMapType], Any, bool]:
    while True:
        try:
            path, instruction = next(output_map_iter)
            if not isinstance(worker, dict):
                main_logger.warning(f'An unexpected value was encountered in pick attempt. a path '
                                    f'has now been skipped. value = {worker}')
                return None, None, False

            if path in worker:
                if isinstance(instruction, str):
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
                    if isinstance(worker, dict):
                        return instruction, worker[path], False

                    main_logger.warning(f'Path ended early. {repr(worker)} does not have keys.')
                    return None, None, False

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
    if type(worker) is dict:
        for path, instruction in output_map_iter:
            if path in worker:
                if isinstance(instruction, str):
                    static_builder[instruction] = worker[path]

                else:
                    # Rather than recursively calling a function from inside of this function, we
                    # pass back the values that the caller needs to use to call the function itself.
                    # This is done this way to limit how deep we go on the stack. It also means the
                    # caller can decide which function to call on the values.
                    # The caller should send the result of the function back to us here so that we
                    # can call func on it.
                    result = yield instruction, worker[path], False
                    try:
                        func(result, builder, static_builder)

                    except Exception as e:
                        main_logger.warning(f'There was an error when attempting to process a '
                                            f'result. Exception raised: {e}')

    else:
        main_logger.warning(f'Cannot follow a path in a non-dict. ({worker})')

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
    output_map, worker, builder, fail, new_mode = _pick_setup(output_map, _input)
    if fail or len(builder):
        return builder

    elif new_mode is not None:
        start_func, list_func, iter_func, final_func = new_mode

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


@converts_enums
def parse_type_as(_type: PickInstruction, data: Any, args: list) -> Union[dict, list]:
    switch = {
        PickInstruction.JSON: lambda x: json.loads(x),
        PickInstruction.JSONL: jsonl_to_json,
        PickInstruction.JSON_SINGLE_QUOTE: wonky_json_to_json,
        PickInstruction.XML: xml_to_json,
        PickInstruction.XMLSA: lambda x: xml_to_json(x, True),
        PickInstruction.ELIST: lambda x: x if isinstance(x, list) else [x],
        PickInstruction.CSV: csv_to_json,
        PickInstruction.LIST: lambda x: x.split(','),
        PickInstruction.YAML: yaml.safe_load,
        PickInstruction.FORM: parse_qs,
    }

    arg_switch = {
        PickInstruction.TUPLE_DICT: _parse_and_execute_tuplish,
    }

    if _type in switch:
        return switch[_type](data)

    elif _type in arg_switch:
        return arg_switch[_type](data, args)

    raise ValueError('Invalid type specified.')


def _parse_and_execute_tuplish(data: Union[dict, list], args: list) -> dict:
    if len(args):
        args = args[0]
        if isinstance(args, dict):
            return convert_tuplish_dict(data, args.get('pair_name'),
                                        args.get('key_name'), args.get('val_name'))

        else:
            raise ValueError('TUPLE_DICT given an invalid argument format.')

    else:
        return convert_tuplish_dict(data)


def fracture(
        data: List[dict],
        *keys: str,
        inplace: bool = True
) -> Generator[Tuple[dict, List[dict]], None, None]:
    """
    Separates a list of dictionaries into sets based on the values of a subset of keys and returns
    each set one at a time.

    :param data: The list to fracture.
    :type data: List[dict]
    :param keys: The subset of keys which should be used to differentiate between items in ``data``.
    :type keys: str
    :param inplace: Whether values returned should literally be the original values from the list or
        should be copies of those values, set to ``False`` if you wish to avoid mutating the
        original values in ``data``.
    :type inplace: bool
    :return: A ``Generator`` which iterates through each subset of ``data`` one at a time, basing
        the subsets off of ``keys``.
    """
    # Choose the function we use to append values based on inplace.
    # Choose it early since checking inplace inside the loop adds up on time.
    if inplace:
        def app_func(builder: List[dict], val: dict):
            return builder.append(val)

    else:
        def app_func(builder: List[dict], val: dict):
            return builder.append(deepcopy(val))

    # Then just generate.
    for subset in _iter_fracture(data, keys, app_func):
        yield subset


def _iter_fracture(
        data: List[dict],
        keys: Tuple[str, ...],
        app_func: Callable[[List[dict], dict], None]
) -> Generator[Tuple[dict, List[dict]], None, None]:
    # The following two objects will be used to reduce repetitive calculations.
    calc = [None] * len(data)
    done = [False] * len(data)
    source = iter(enumerate(data))
    try:
        i, val = next(source)

    except StopIteration:
        return

    builder = []
    def1 = get_subset_values(val, *keys) if calc[i] is None else calc[i]
    mark = get_subset(val, *keys)
    app_func(builder, val)
    for j, _val in enumerate(data[i + 1:]):
        j += i + 1
        calc[j] = def2 = get_subset_values(_val, *keys)
        if def1 == def2:
            app_func(builder, _val)
            done[j] = True

    yield mark, builder

    while True:
        try:
            i, val = next(source)

        except StopIteration:
            return

        if not done[i]:
            builder = []
            def1 = calc[i]
            mark = get_subset(val, *keys)
            app_func(builder, val)
            for j, _val in enumerate(data[i + 1:]):
                j += i + 1
                if def1 == calc[j]:
                    app_func(builder, _val)
                    done[j] = True

            yield mark, builder


# --------------------------------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------------------------------
_AA = 'ALWAYS_AGG'
_SA = 'SIMPLE_AGG'
_SC = 'SIMPLE_CHECK'
_CLC = 'COMPLEX_LIST_CHECK'
_CDC = 'COMPLEX_DICT_CHECK'
AGG_DEF_TYPES = (_SA, _SC, _CLC, _CDC)


class AggDef(CarrierEnum):
    """
    A :class:`funk_py.modularity.decoration.enums.CarrierEnum` used to represent aggregation
    definitions.

    Members:
    ^^^^^^^^^^^^^
    **True Aggregation Definitions:**

    The true aggregation definitions are definitions that strictly do real aggregation. They do not
    decide winners or losers in comparisons. If desired, may be put in a list also containing a
    dictionary of other keys mapped to check definitions (as defined in the next section) to set
    requirements for an item's value to actually be aggregated at the target key. it is important to
    note that if the conditions specified in such a dictionary disallow aggregating, but the item
    itself isn't completely ruled out, the current status of the aggregation will replace the value,
    and will not consider the new value.

    - ``SUM``: Sum the values at keys of these types.
    - ``AVG``: Average the values at keys of these types.
    - ``MAX``: Replace the value with the max of the key in the new item vs the old value.
    - ``MIN``: Replace the value with the min of the key in the new item vs the old value.
    - ``LAST``: Keep the last value encountered for a key.

    Each true aggregation definition has a corresponding *always* version. The *always* version of a
    true aggregation definition will be evaluated whether the checks pass or not. These *always*
    definitions are: ``SUM_ALWAYS``, ``AVG_ALWAYS``, ``MAX_ALWAYS``, ``MIN_ALWAYS``, and
    ``LAST_ALWAYS``.

    **Check Definitions:**

    The check definitions are definitions that decide whether values are actually aggregated. When
    used in a dictionary in a list with one of the true aggregation definitions, will only affect
    the behavior of that true aggregation definition; however, when they are used at the surface
    level in an overall aggregation definition, they determine whether an item will even be
    considered for aggregation at all.

    - ``GREATER``: Requires the related key to have a corresponding value greater than the current
      stored value in the aggregation. Will allow the first item to be added automatically, since
      there will be nothing to compare to.
    - ``LESSER``: Requires the related key to have a corresponding value less than the current
      stored value in the aggregation. Will allow the first item to be added automatically, since
      there will be nothing to compare to.
    - ``EXISTS``: Requires the related key to actually exist and have a non-``None`` value. Items
      will be ignored until an item meeting the criteria is encountered, and the rule will still
      apply to items after that.
    - ``NOT_EXISTS``: Requires the related key to not exist or to have a value of ``None``. Items
      will be ignored until an item meeting the criteria is encountered, and the rule will still
      apply to items after that.
    - ``ONE_OF``: Requires the related key to have a corresponding value *found* within a specified
      list of items in order to pass. Items will be ignored until an item meeting the criteria is
      encountered, and the rule will still apply to items after that. This definition is special
      insofar as it requires an argument representing a list of valid items.
    - ``NOT_ONE_OF``: Requires the related key to have a corresponding value *not found* within a
      specified list of items in order to pass. Items will be ignored until an item meeting the
      criteria is encountered, and the rule will still apply to items after that. This definition
      is special insofar as it requires an argument representing a list of valid items.
    - ``GREATER_OF``: Requires the related key to have a corresponding value that when checked in a
      specified mapping of items to integer values will have a value *higher* than the same check
      for the previous value. If for some reason, the key's value is not in the provided map, the
      item will be considered to lose. Will allow the first item to be added automatically, since
      there will be nothing to compare to. This definition is special insofar as it requires an
      argument representing a dictionary of items to integer values.
      Example:

          Given ``agg_def = GREATER_OF({'llama': 1, 'horse': 2, 'dog': 3})``:

          - If the current stored value for the key is ``'horse'`` and the new value is ``'llama'``,
            the new item will lose.
          - If the current stored value for the key is ``'horse'`` and the new value is ``'horse'``
            or ``'dog'``, the new item will win.

    - ``LESSER_OF``: Requires the related key to have a corresponding value that when checked in a
      specified mapping of items to integer values will have a value *lower* than the same check for
      the previous value. If for some reason, the key's value is not in the provided map, the item
      will be considered to lose. Will allow the first item to be added automatically, since there
      will be nothing to compare to. This definition is special insofar as it requires an argument
      representing a dictionary of items to integer values.
      Example:

          Given ``agg_def = GREATER_OF({'llama': 1, 'horse': 2, 'dog': 3})``:

          - If the current stored value for the key is ``'horse'`` and the new value is ``'horse'``
            or ``'dog'``, the new item will lose.
          - If the current stored value for the key is ``'horse'`` and the new value is ``'llama'``,
            the new item will win.

    """
    # True Aggregation:
    @ignore
    @staticmethod
    def _sum_func():
        def sum_(value, other_value):
            if other_value is None:
                return value

            elif value is None:
                return other_value

            return value + other_value

        return sum_

    SUM = special_member(type=_SA, eval=_sum_func, json='SUM')
    SUM_ALWAYS = special_member(type=_AA, eval=_sum_func, json='SUM_ALWAYS')

    @ignore
    @staticmethod
    def _avg_func():
        sum_ = 0
        count = 0

        def avg(value, other_value):
            nonlocal sum_
            nonlocal count
            count += 1
            if value is None:
                return sum_ / count

            sum_ += value
            return sum_ / count

        return avg

    AVG = special_member(type=_SA, eval=_avg_func, json='AVG')
    AVG_ALWAYS = special_member(type=_AA, eval=_avg_func, json='AVG_ALWAYS')

    @ignore
    @staticmethod
    def _max_func():
        def max_(value, other_value):
            if other_value is None:
                return value

            elif value is None:
                return other_value

            return max(value, other_value)

        return max_

    MAX = special_member(type=_SA, eval=_max_func, json='MAX')
    MAX_ALWAYS = special_member(type=_AA, eval=_max_func, json='MAX_ALWAYS')

    @ignore
    @staticmethod
    def _min_func():
        def min_(value, other_value):
            if other_value is None:
                return value

            elif value is None:
                return other_value

            return min(value, other_value)

        return min_

    MIN = special_member(type=_SA, eval=_min_func, json='MIN')
    MIN_ALWAYS = special_member(type=_AA, eval=_min_func, json='MIN_ALWAYS')

    @ignore
    @staticmethod
    def _last_func():
        def last(value, other_value):
            return other_value if value is None else value

        return last

    LAST = special_member(type=_SA, eval=_min_func, json='LAST')
    LAST_ALWAYS = special_member(type=_AA, eval=_last_func, json='LAST_ALWAYS')

    # Checks (Simple):
    @ignore
    @staticmethod
    def greater_func():
        def gt(value, other_value):
            if other_value is None:
                return True

            elif value is None:
                return False

            return value >= other_value

        return gt

    GREATER = special_member(type=_SC, eval=greater_func, json='GREATER')

    @ignore
    @staticmethod
    def lesser_func():
        def lt(value, other_value):
            if other_value is None:
                return True

            elif value is None:
                return False

            return value <= other_value

        return lt

    LESSER = special_member(type=_SC, eval=lesser_func, json='LESSER')

    @ignore
    @staticmethod
    def exists_func():
        return lambda value, other_value: value is not None

    EXISTS = special_member(type=_SC, eval=exists_func, json='EXISTS')

    @ignore
    @staticmethod
    def not_exists_func():
        return lambda value, other_value: value is None

    NOT_EXISTS = special_member(type=_SC, eval=not_exists_func, json='NOT_EXISTS')

    @staticmethod
    def ONE_OF(items: Union[list, set]):
        """
        Requires the related key to have a corresponding value *found* within a specified list of
        items in order to pass. Items will be ignored until an item meeting the criteria is
        encountered, and the rule will still apply to items after that. This definition is special
        insofar as it requires an argument representing a list of valid items.

        This can be represented in a JSON form by ``['ONE_OF', {key1: int, key2: int, ...}]``.

        :param items: The items to compare against.
        """
        _items = set(items)
        return {
            'type': _CLC,
            'eval': lambda: lambda value, other_value: value in _items,
            'json': ['ONE_OF', list(items)]
        }

    @staticmethod
    def NOT_ONE_OF(items: Union[list, set]):
        """
        Requires the related key to have a corresponding value *not found* within a specified list
        of items in order to pass. Items will be ignored until an item meeting the criteria is
        encountered, and the rule will still apply to items after that. This definition is special
        insofar as it requires an argument representing a list of valid items.

        This can be represented in a JSON form by ``['NOT_ONE_OF', {key1: int, key2: int, ...}]``.

        :param items: The items to compare against.
        """
        _items = set(items)
        return {
            'type': _CLC,
            'eval': lambda: lambda value, other_value: value not in _items,
            'json': ['NOT_ONE_OF', list(items)]
        }

    @staticmethod
    def GREATER_OF(mapping: Dict[Any, int]):
        """
        Requires the related key to have a corresponding value that when checked in a specified
        mapping of items to integer values will have a value *higher* than the same check for the
        previous value. If for some reason, the key's value is not in the provided map, the item
        will be considered to lose. Will allow the first item to be added automatically, since there
        will be nothing to compare to. This definition is special insofar as it requires an argument
        representing a dictionary of items to integer values.

        This can be represented in a JSON form by ``['GREATER_OF', {key1: int, key2: int, ...}]``.

        :param mapping: The mapping to use for evaluating values.
        """
        _min = min(mapping.values()) - 1

        def eval(value, other_value) -> bool:
            if other_value is None:
                return True

            # Maybe the user mapped None, so give it a shot.
            return mapping.get(value, _min) >= mapping.get(other_value, _min)

        return {'type': _CDC, 'eval': lambda: eval, 'json': ['GREATER_OF', mapping]}

    @staticmethod
    def LESSER_OF(mapping: Dict[Any, int]):
        """
        Requires the related key to have a corresponding value that when checked in a specified
        mapping of items to integer values will have a value *lower* than the same check for the
        previous value. If for some reason, the key's value is not in the provided map, the item
        will be considered to lose. Will allow the first item to be added automatically, since there
        will be nothing to compare to. This definition is special insofar as it requires an argument
        representing a dictionary of items to integer values.

        This can be represented in a JSON form by ``['LESSER_OF', {key1: int, key2: int, ...}]``.

        :param mapping: The mapping to use for evaluating values.
        :return:
        """
        _max = max(mapping.values()) + 1

        def eval(value, other_value) -> bool:
            if other_value is None:
                return True

            # Maybe the user mapped None, so give it a shot.
            return mapping.get(value, _max) <= mapping.get(other_value, _max)

        return {'type': _CDC, 'eval': lambda: eval, 'json': ['LESSER_OF', mapping]}


SimpAggDef = Literal['SUM', 'AVG', 'MAX', 'MIN', 'LAST']
AlwaysAggDef = Literal['SUM_ALWAYS', 'AVG_ALWAYS', 'MAX_ALWAYS', 'MIN_ALWAYS', 'LAST_ALWAYS']
SimpAggCheckDef = Literal['SUM', 'AVG', 'MAX', 'MIN', 'GREATER', 'LESSER', 'EXISTS', 'NOT_EXISTS']
SimpCheckDef = Literal['GREATER', 'LESSER', 'EXISTS', 'NOT_EXISTS']
CompCheckDef = Union[List[Union[Literal['ONE_OF', 'NOT_ONE_OF'], List[Any]]],
                     List[Union[Literal['GREATER_OF', 'LESSER_OF'], Dict[Hashable, int]]]]
CheckDef = Union[SimpCheckDef, CompCheckDef]
CompAggDef = List[Union[SimpAggDef, Dict[Hashable, CheckDef]]]
CompAlwaysAggDef = List[Union[AlwaysAggDef, Dict[Hashable, CheckDef]]]

PlainAggDef = Dict[Hashable, Union[SimpAggCheckDef, CompAggDef, CompAlwaysAggDef, CheckDef]]
TrueAggDef = Dict[Any, Union[AggDef, List[Union[AggDef, Dict[Any, AggDef]]]]]


AGG_DEF_MAP = {
    'SUM': AggDef.SUM,
    'AVG': AggDef.AVG,
    'MAX': AggDef.MAX,
    'MIN': AggDef.MIN,
    'LAST': AggDef.LAST,
    'SUM_ALWAYS': AggDef.SUM_ALWAYS,
    'AVG_ALWAYS': AggDef.AVG_ALWAYS,
    'MAX_ALWAYS': AggDef.MAX_ALWAYS,
    'MIN_ALWAYS': AggDef.MIN_ALWAYS,
    'LAST_ALWAYS': AggDef.LAST_ALWAYS,
    'GREATER': AggDef.GREATER,
    'LESSER': AggDef.LESSER,
    'EXISTS': AggDef.EXISTS,
    'NOT_EXISTS': AggDef.NOT_EXISTS,
    'ONE_OF': AggDef.ONE_OF,
    'NOT_ONE_OF': AggDef.NOT_ONE_OF,
    'GREATER_OF': AggDef.GREATER_OF,
    'LESSER_OF': AggDef.LESSER_OF,
}
SIMPLE_AGG_DEFS = {'SUM', 'AVG', 'MAX', 'MIN', 'LAST'}
ALWAYS_AGG_DEFS = {'SUM_ALWAYS', 'AVG_ALWAYS', 'MAX_ALWAYS', 'MIN_ALWAYS', 'LAST_ALWAYS'}
SIMPLE_CHECKS = {'GREATER', 'LESSER', 'EXISTS', 'NOT_EXISTS'}
COMPLEX_DICT_CHECKS = {'GREATER_OF', 'LESSER_OF'}
COMPLEX_LIST_CHECKS = {'ONE_OF', 'NOT_ONE_OF'}


def convert_to_agg_def_dict(agg_def: PlainAggDef) -> TrueAggDef:
    """
    Converts a ``PlainAggDef`` item to a ``TrueAggDef``. This is useful if you want to store an
    aggregation definition as JSON.
    """
    builder = {}
    for key, val in agg_def.items():
        if type(val) is str and val in SIMPLE_AGG_DEFS.union(SIMPLE_CHECKS).union(ALWAYS_AGG_DEFS):
            builder[key] = AGG_DEF_MAP[val]

        elif isinstance(val, list):
            builder[key] = _convert_comp_agg_def_or_check(val)

        else:
            raise TypeError('The given PlainAggDef includes an unknown AggDef string.')

    return builder


def _convert_comp_agg_def_or_check(
        agg_def: Union[CompAggDef, CompCheckDef]
) -> List[Union[AggDef, Dict[Hashable, AggDef]]]:
    if len(agg_def) != 2:
        raise TypeError('The given PlainAggDef has an invalid list. It\'s too long or too short.')

    if agg_def[0] in SIMPLE_AGG_DEFS.union(ALWAYS_AGG_DEFS):
        return _convert_comp_agg_def(agg_def)

    elif agg_def[0] in COMPLEX_LIST_CHECKS.union(COMPLEX_DICT_CHECKS):
        return _convert_comp_check(agg_def)

    raise TypeError('The given PlainAggDef has an invalid list. It does not start with a '
                    'simple aggregator or with a complex checker.')


def _convert_comp_agg_def(
        agg_def: Union[CompAggDef, CompAlwaysAggDef]
) -> List[Union[AggDef, Dict[Hashable, AggDef]]]:
    builder = {}
    if isinstance(agg_def[1], dict):
        for key, val in agg_def[1].items():
            builder[key] = _convert_check(val)

    else:
        raise TypeError('The given PlainAggDef includes at least one broken CompAggDef.')

    return [AGG_DEF_MAP[agg_def[0]], builder]


def _convert_check(check: CheckDef):
    if isinstance(check, list):
        if len(check) != 2:
            raise TypeError('The given PlainAggDef has an invalid list in a CompAggDef. It\'s too '
                            'long or too short.')

        if check[0] not in COMPLEX_DICT_CHECKS.union(COMPLEX_LIST_CHECKS):
            raise TypeError('The given PlainAggDef has an invalid list in a CompAggDef.')

        return _convert_comp_check(check)

    elif check in SIMPLE_CHECKS:
        return AGG_DEF_MAP[check]

    raise TypeError('The given PlainAggDef has an unrecognized type of check.')


def _convert_comp_check(check: CompCheckDef):
    if check[0] in COMPLEX_LIST_CHECKS:
        if isinstance(check[1], list):
            return _safe_hash_for_comp_check(check)

        raise TypeError('The given PlainAggDef has an invalid complex list check.')

    elif isinstance(check[1], dict):
        return _safe_hash_for_comp_check(check)

    raise TypeError('The given PlainAggDef has an invalid complex dict check.')


def _safe_hash_for_comp_check(check: CompCheckDef):
    try:
        return AGG_DEF_MAP[check[0]](check[1])

    except TypeError as e:
        # If there is an unhashable item in the list or unhashable key in the dict, it will raise
        # an error (due to the inner workings of the complex list checks or dicts). Catch this case
        # and return a more useful error.
        if e.message.startswith('unhashable type:'):
            raise TypeError('The given PlainAggDef has an invalid complex list or dict check '
                            'containing an unhashable type.')

        # If it wasn't an error due to hashing, just re-raise the same error.
        raise e


def convert_from_agg_def_dict(agg_def: TrueAggDef) -> PlainAggDef:
    builder = {}
    for key, _agg_def in agg_def.items():
        if isinstance(_agg_def, list):
            builder[key] = _convert_from_comp_agg_def_dict(_agg_def)
            continue

        try:
            builder[key] = _agg_def.json

        except AttributeError:
            raise TypeError('An AggDef in a TrueAggDef did not have a json attribute.')

    return builder


def _convert_from_comp_agg_def_dict(agg_def: CompAggDef):
    builder = {}
    if len(agg_def) != 2:
        raise TypeError('A TrueAggDef shouldn\'t have a list of length greater than two.')

    if type(agg_def[0]) is not AggDef:
        raise TypeError('The provided TrueAggDef had a non-AggDef element where an AggDef '
                        'should have been.')

    elif agg_def[0].type not in (_SA, _AA):
        raise TypeError('The provided TrueAggDef had a check as the first part of a complex '
                        'aggregate definition.')

    _agg_def, mapping = agg_def
    for key, _agg_def in mapping.items():
        if type(_agg_def) is not AggDef:
            raise TypeError('The provided TrueAggDef had a non-AggDef element where an AggDef '
                            'should have been.')

        elif _agg_def.type not in (_CDC, _CLC, _SC):
            raise TypeError('The provided TrueAggDef had an aggregator in a complex aggregate '
                            'definition.')

        try:
            builder[key] = _agg_def.json
            continue

        except AttributeError:
            raise TypeError('An AggDef in the provided TrueAggDef did not have a json attribute.')

    try:
        return [agg_def[0].json, builder]

    except AttributeError:
        raise TypeError('An AggDef in the provided TrueAggDef did not have a json attribute.')


class _AggregationDefinition:
    invalid_error = TypeError('An invalid agg_def was provided.')

    def __init__(self, agg_def: TrueAggDef = None):
        self.simple_agg_defs = {}
        self.complex_agg_defs = {}
        self.check_defs = {}
        self.mutating_keys = set()

        if agg_def is not None:
            if not isinstance(agg_def, dict):
                raise self.invalid_error

            for key, _agg_def in agg_def.items():
                self.add(key, _agg_def)

    def _exists(self, agg_def: AggDef) -> str:
        if agg_def.type not in AGG_DEF_TYPES:
            raise ValueError('agg_def has an unknown AggDef type in it. It cannot be processed.')

        return agg_def.type

    def add(self, key: Any, agg_def: Union[AggDef, List[Union[AggDef, Dict[Any, AggDef]]]]):
        if type(agg_def) is AggDef:
            ad = self._exists(agg_def)
            if ad == _SA:
                self.simple_agg_defs[key] = agg_def.eval()
                self.mutating_keys.add(key)

            else:
                self.check_defs[key] = agg_def.eval()

        elif isinstance(agg_def, list):
            if (len(agg_def) != 2 or type(agg_def_ := agg_def[0]) is not AggDef
                    or not isinstance(agg_def[1], dict)):
                raise self.invalid_error

            ad = self._exists(agg_def_)  # noqa: agg_def_ cannot be referenced before its
                                         # assignment. An error would be raised before getting here
                                         # if it wasn't assigned.
            if ad != _SA:
                raise self.invalid_error

            # Rely on the builder's type_checking to verify whether the inner agg_def is okay.
            builder = _AggregationDefinition()
            for _key, _agg_def in agg_def[1].items():
                builder._add_inner(_key, _agg_def)

            self.complex_agg_defs[key] = (agg_def_.eval(), builder)
            self.mutating_keys.add(key)

        else:
            raise self.invalid_error

    def _add_inner(self, key: Any, agg_def: AggDef):
        if type(agg_def) is AggDef:
            ad = self._exists(agg_def)
            if ad == _SA:
                raise self.invalid_error

            else:
                self.check_defs[key] = agg_def.eval()

        else:
            raise self.invalid_error

    def _eval_item(self, item: dict, current: dict) -> bool:
        _pass = True
        for key, eval in self.check_defs.items():
            _pass = eval(item.get(key), current.get(key))
            if not _pass:
                break

        return _pass

    def process_items(self, items: List[dict]):
        """
        Processes a list of items based on the ``_AggregationDefinition``'s setup.

        :param items: The item list to process.
        :return: The resulting dictionary.
        """
        current = None
        for item in items:
            current = self._process_item(item, current)

        return current

    def _process_item(self, item: dict, current: dict = None) -> dict:
        """
        Processes an item based on the ``_AggregationDefinition``'s setup.

        :param item: The item to process.
        :param current: The current builder. If ``None``, an empty dictionary will be generated.
        :return: The resulting current dictionary.
        """
        if current is None:
            current = {}

        if self._eval_item(item, current):
            for key, data in self.complex_agg_defs.items():
                eval, checker = data
                if checker._eval_item(item, current):
                    current[key] = eval(item.get(key), current.get(key))

            for key, eval in self.simple_agg_defs.items():
                current[key] = eval(item.get(key), current.get(key))

            # Make a copy of the mutating keys so that it can be expanded to contain any non-mutated
            # keys in item. We don't simply want to copy item's items in case it is missing any of
            # the mutated values, which mustn't be deleted.
            new_keys = self.mutating_keys.copy()
            new_keys.update(item.keys())

            # Go through the items in item and if they aren't a member of mutating keys, update
            # current with them.
            for key, val in item.items():
                if key not in self.mutating_keys:
                    new_keys.add(key)
                    current[key] = val

            # Remove the keys that should no longer exist from current.
            for key in list(current.keys()):
                if key not in new_keys:
                    del current[key]

        return current


DataSourceOrProvider = Union[dict, Iterable[dict], Callable[[dict], Union[dict, Ldct, None]]]


def aggregate(
        data: Ldct,
        identifiers: Ls,
        agg_def: TrueAggDef,
        other_data: DataSourceOrProvider = None,
) -> List[dict]:
    """
    Aggregate values in data based on the provided unique identifiers and aggregation definition.

    :param data: Dictionaries to aggregate.
    :param identifiers: Unique identifiers that data should be aggregated across.
    :param agg_def: The definition for aggregation.
    :param other_data: Either another set of data to evaluate against or a provider of other items
        to compare to. Can be useful when needing to compare against items in a database. If an
        iterable of dictionaries is provided, those dictionaries will be appended to each subset of
        dictionaries for evaluation. If a function is provided, it should accept a dictionary
        representing the id (unique fingerprint) of each subset. For instance, if ``identifiers`` is
        ``['name', 'time']``, then the function should be built to expect a dictionary of the form
        ``{'name': value1, 'time': value2}``. This function can return either a single dictionary,
        which would be appended to the end of its corresponding subset before evaluation, or it may
        return a list of dictionaries, which would be used to extend its corresponding subset before
        evaluation. Returning ``None`` from this function would be treated as no extra results, and
        the corresponding subset wouldn't have any extra items added for evaluation.
    """
    builder = []
    if other_data is None:
        for _, subset in fracture(data, *identifiers, inplace=False):
            result = _AggregationDefinition(agg_def).process_items(subset)
            if len(result):
                builder.append(result)

        return builder

    for id_, subset in fracture(data, *identifiers, inplace=False):
        subset = subset + _get_other_data_for_aggregation(id_, other_data)
        result = _AggregationDefinition(agg_def).process_items(subset)
        result.update(id_)
        if len(result):
            builder.append(result)

    return builder


def _get_other_data_for_aggregation(id_: dict, other_data: DataSourceOrProvider) -> Ldct:
    if callable(other_data):
        ans = other_data(id_)
        if ans is None:
            return []

        elif isinstance(ans, list):
            return ans

        return [ans]

    elif isinstance(other_data, dict):
        return [other_data]

    return list(other_data)


def translate(data: List[dict], translators: Mapping[Any, Callable[[dict], Any]],
              default: Any = ..., inplace: bool = True) -> List[dict]:
    """
    Translate values in data based on given translators.

    :param data: Dictionaries to translate.
    :type data: List[dict]
    :param translators: A dictionary of keys and functions used to translate values at those keys.
    :type translators: Mapping[Any, Callable[[dict], Any]]
    :param default: A default value to use for keys that don't exist. If this is not specified,
        missing keys will simply be ignored.
    :type default: Any
    :param inplace: Whether to mutate ``data`` or not. Defaults to ``True``.
    :type inplace: bool
    :return: A list of the dictionaries in ``data`` mutated based on the functions in
        ``translators``.
    """
    # Much more efficient to check inplace outside the loop.
    if inplace:
        for v in data:
            for k, trans in translators.items():
                if k in v:
                    v[k] = trans(v[k])

                elif default is not ...:
                    v[k] = default

        return data

    output = []
    for v in data:
        output.append(builder := deepcopy(v))
        for k, trans in translators.items():
            if k in v:
                builder[k] = trans(v[k])

            elif default is not ...:
                builder[k] = default

    return output
