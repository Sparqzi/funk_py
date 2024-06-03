import json
import os
import inspect
import pickle
from copy import deepcopy
from datetime import datetime, date, time
from enum import Enum, IntEnum
from functools import wraps
from io import TextIOWrapper
from typing import Union, Any, Callable, BinaryIO, TextIO, Optional, List

from funk_py.modularity.basic_structures import pass_
from funk_py.modularity.decoration.method_modifiers import has_alternatives
from funk_py.modularity.logging import make_logger, logs_vars
from funk_py.modularity.type_matching import check_iterable_not_string

main_logger = make_logger('special_modifiers', 'SPECIAL_MODIFIER_LOG_LEVEL',
                          default_level='warning')


DiskCacheType = Any
DiskCacheIO = Union[BinaryIO, TextIO]


class DiskCacheMethod(IntEnum):
    WUNC = 0
    LFU = 1
    LRU = 2
    CUSTOM = 3


class _ResultFile:
    def __init__(self, target_dir: Union[str, bytes, os.PathLike],
                 filename: str,
                 true_filename: str,
                 allow_mutation: bool,
                 in_bytes: bool,
                 write_converter: Callable[[DiskCacheType, DiskCacheIO], None],
                 read_converter: Callable[[DiskCacheIO], DiskCacheType],
                 index: dict):
        main_logger.info('Initializing a new instance of _ResultFile...')
        self._filename = filename
        self._true_filename = true_filename
        self._allow_mutation = allow_mutation
        self._write_converter = write_converter
        self._read_converter = read_converter
        self._target_dir = target_dir
        self._index = index
        self._path = _path = os.path.join(target_dir, true_filename)

        b = 'b' if in_bytes else ''
        self._read_method = 'r' + b
        self._write_method = 'w' + b
        self._create_method = 'x' + b

        if filename in index:
            self.__has_result = True
            with open(_path, self._read_method) as reader:
                self.__result = read_converter(reader)

        else:
            self.__has_result = False

        main_logger.info('Instance of _ResultFile initialized.')

    @property
    def has_result(self) -> bool:
        return self.__has_result

    def get(self) -> DiskCacheType:
        if not self.__has_result:
            msg = 'Tried to get a result before it existed!'
            main_logger.error(msg)
            raise TypeError(msg)

        if self._allow_mutation:
            return self.__result

        return deepcopy(self.__result)

    def set(self, value: DiskCacheType = ...):
        # ... represents that the desired operation is to update the saved file with the current
        # state of the object.
        if value is ...:
            with open(self._path, self._write_method) as writer:
                writer.truncate()
                self._write_converter(self.__result, writer)

        self.__result = value
        if not self.__has_result:
            _dir = '\\'.join(self._path.split('\\')[:-1])
            if not os.path.exists(_dir):
                os.makedirs(_dir)

            try:
                with open(self._path, self._create_method) as writer:
                    self._write_converter(value, writer)
                    self.__has_result = True
                    return

            except FileExistsError:
                with open(self._path, self._write_method) as writer:
                    writer.truncate()
                    self._write_converter(value, writer)
                    self.__has_result = True
                    return

        with open(self._path, self._write_method) as writer:
            writer.truncate()
            self._write_converter(value, writer)

        self.__has_result = True

    # Don't override the __del__ method since that would guarantee the cache was deleted after the
    # program was done. The assumption is that the user wants future executions to have the cache
    # built already.
    def delete(self):
        # It is important to remove the file from the drive when it becomes irrelevant.
        os.remove(self._path)
        # We also want to delete it from the index, since it's no longer relevant.
        del self._index[self._filename]
        # As well, we should make sure the index file is updated.
        _set_index(self._target_dir, self._index)


class _DiskCacheResults:
    def __init__(self, target_dir: Union[str, bytes, os.PathLike],
                 maxsize: int,
                 allow_mutation: bool,
                 in_bytes: bool,
                 write_converter: Callable[[DiskCacheType, DiskCacheIO], None],
                 read_converter: Callable[[DiskCacheIO], DiskCacheType],
                 funk: Callable,
                 cache_method: DiskCacheMethod,
                 cache_arg: Any):
        main_logger.info('Initializing a new instance of _DictCacheResults...')
        self._target_dir = target_dir
        self._maxsize = maxsize
        self._allow_mutation = allow_mutation
        self._in_bytes = in_bytes
        self._write_converter = write_converter
        self._read_converter = read_converter
        self._funk = funk
        self._cache_arg = cache_arg
        self._index = _get_index(target_dir)
        used = [v[0] for v in self._index.values()]
        self.__unused = [str(v) for v in range(maxsize) if str(v) not in used]
        self.__results = {}

        self._bget.set_alternative(cache_method)
        self._drop_worst_candidate.set_alternative(cache_method)
        self._aget.set_alternative(cache_method)

        main_logger.info('Instance of _DictCacheResults initialized.')

    def _create_result_file(self, filename: str, true_filename: str) -> _ResultFile:
        return _ResultFile(self._target_dir, filename, true_filename, self._allow_mutation,
                           self._in_bytes, self._write_converter, self._read_converter, self._index)

    def get(self, filename: str, *args, **kwargs) -> DiskCacheType:
        index = self._index
        self._bget(filename)
        self._aget(filename, self._get(filename, args, kwargs))
        _set_index(self._target_dir, index)
        return self.__results[filename].get()

    @has_alternatives(DiskCacheMethod.WUNC)
    def _bget(self, filename: str):
        index = self._index
        if filename not in index:
            for v in index.values():
                v[2] += 1

        else:
            for _filename, v in index.items():
                if filename != _filename:
                    v[2] += 1

    @_bget.alternative(DiskCacheMethod.LFU, DiskCacheMethod.LRU)
    def _bget2(self, filename: str): ...

    @_bget.alternative(DiskCacheMethod.CUSTOM)
    def _bget3(self, filename: str):
        self._cache_arg[0](self._maxsize, self._index, filename)

    @has_alternatives(DiskCacheMethod.WUNC)
    def _aget(self, filename: str, true_filename: str):
        index = self._index
        cur = index.get(filename, [true_filename, 0, 0])
        index[filename] = [cur[0], cur[1] + 1, cur[2]]

    @_aget.alternative(DiskCacheMethod.LFU)
    def _aget2(self, filename: str, true_filename: str):
        index = self._index
        cur = index.get(filename, [true_filename, 0])
        index[filename] = [cur[0], cur[1] + 1]

    @_aget.alternative(DiskCacheMethod.LRU)
    def _aget3(self, filename: str, true_filename: str):
        index = self._index
        if filename not in index:
            index[filename] = true_filename

        else:
            copier = index.pop(filename)
            index[filename] = copier

    @_aget.alternative(DiskCacheMethod.CUSTOM)
    def _aget4(self, filename: str, true_filename: str):
        self._cache_arg[2](self._maxsize, self._index, filename, true_filename)

    def _get(self, filename: str, args: tuple, kwargs: dict) -> Optional[str]:
        true_filename = None
        if filename not in self._index:
            # When not in the index already, calculate the result of func, then add it to the index.
            true_filename = self._set(filename, self._funk(*args, **kwargs))

        elif filename not in self.__results:
            self.__results[filename] = self._create_result_file(filename, self._index[filename][0])

        return true_filename

    def set(self):
        for result in self.__results.values():
            result.set()

    def _set(self, filename: str, value: DiskCacheType) -> str:
        index = self._index
        if filename not in index:
            if len(self.__unused) == 0:
                _next = self._drop_worst_candidate()

            else:
                _next = self.__unused.pop()

            result = self.__results[filename] = self._create_result_file(filename, _next)
            result.set(value)
            return _next

        self.__results[filename].set(value)
        return index[filename][0]

    def _find_and_drop_worst(
            self,
            calc_funk: Callable[[List[Union[str, int]]], Union[int, float]]
    ) -> str:
        index = self._index
        _min = min([calc_funk(v) for v in index.values()])
        for _filename, val in index.items():
            if calc_funk(val) == _min:
                _next = val[0]
                if _filename in self.__results:
                    self.__results[_filename].delete()
                    del self.__results[_filename]
                    return _next

                result = self._create_result_file(_filename, _next)
                result.delete()
                return _next

    @has_alternatives(DiskCacheMethod.WUNC)
    def _drop_worst_candidate(self) -> str:
        maxsize = (1 if self._cache_arg is None else self._cache_arg) * self._maxsize
        return self._find_and_drop_worst(lambda v: v[1] - (v[2] / maxsize))

    @_drop_worst_candidate.alternative(DiskCacheMethod.LFU)
    def _drop_worst_candidate2(self) -> str:
        return self._find_and_drop_worst(lambda v: v[1])

    @_drop_worst_candidate.alternative(DiskCacheMethod.LRU)
    def _drop_worst_candidate3(self) -> str:
        index = self._index
        filename = next(iter(index.keys()))
        _next = index[filename][0]
        if filename not in self.__results:
            self.__results[filename] = self._create_result_file(filename, index[filename])

        self.__results[filename].delete()
        del self.__results[filename]
        return _next

    @_drop_worst_candidate.alternative(DiskCacheMethod.CUSTOM)
    def _drop_worst_candidate4(self) -> str:
        _next, filename = self._cache_arg[1](self._maxsize, self._index)
        if filename in self.__results:
            self.__results[filename].delete()
            del self.__results[filename]
            return _next

        result = self._create_result_file(filename, _next)
        result.delete()
        return _next


    def clear(self):
        for filename, result in list(self.__results.items()):
            result.delete()
            del self.__results[filename]


DISK_CACHE_INDEX_NAME = 'disk_cache_index'


def _get_index(target_dir: Union[str, bytes, os.PathLike]) -> dict:
    if os.path.exists(_path := os.path.join(target_dir, DISK_CACHE_INDEX_NAME)):
        with open(_path, 'r') as reader:
            return json.load(reader)

    return {}


def _set_index(target_dir: Union[str, bytes, os.PathLike], index: dict):
    if os.path.exists(_path := os.path.join(target_dir, DISK_CACHE_INDEX_NAME)):
        with open(_path, 'w') as writer:
            writer.truncate()
            json.dump(index, writer)
            return

    with open(_path, 'x') as writer:
        json.dump(index, writer)


class _DiskCacheNameConverters:
    _strict_types = (float, int, str)
    _strict_type_tags = {
        float: ';float;',
        int: ';int;',
        str: ';str;'
    }

    FINISH_ITER_MSG = 'Finished iterating through items. Generating result...'

    @staticmethod
    def _file_str(value: Any) -> str:
        main_logger.debug('Making a value into a string...')
        # Replace any characters that don't work well in file names.
        ans = str(value)
        main_logger.debug(f'Successfully made string: {ans}')
        main_logger.debug('Checking if value inherits from one of the base types...')
        for t, tag in _DiskCacheNameConverters._strict_type_tags.items():
            # Don't check if type is, instead check if instance of. Most functions will not be
            # are designed to expect any type of string/in/float. It may be possible to make this
            # behavior optional in the future, but for now design for the most probable case.
            if isinstance(value, t):
                main_logger.debug(f'Value inherits from {str(t)}, using appropriate tag...')
                ans = tag + ans
                main_logger.debug(f'Result is {ans}')
                return ans

        main_logger.debug('Value does not inherit from one of the base types. Creating and adding '
                          'a tag...')
        ans = f';{type(value)};' + ans
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _datetime_str(value: datetime) -> str:
        main_logger.debug('Making a datetime into a string...')
        ans = ';datetime;' + value.strftime('%Y-%m-%d--%H-%M-%S--%Z')
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _date_str(value: date) -> str:
        main_logger.debug('Making a date into a string...')
        ans = ';date;' + value.strftime('%Y-%m-%d')
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _time_str(value: time) -> str:
        main_logger.debug('Making a date into a string...')
        ans = ';time;' + value.strftime('%H-%M-%S--%Z')
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _list_to_str(value: list) -> str:
        main_logger.debug('Converting a list to a string...')
        builder = []
        for val in value:
            builder.append(_DiskCacheNameConverters.to_str(val))

        main_logger.debug(_DiskCacheNameConverters.FINISH_ITER_MSG)
        ans = ';list;' + ','.join(builder) + ';end-list;'
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _tuple_to_str(value: tuple) -> str:
        main_logger.debug('Converting a tuple to a string...')
        builder = []
        for val in value:
            builder.append(_DiskCacheNameConverters.to_str(val))

        main_logger.debug(_DiskCacheNameConverters.FINISH_ITER_MSG)
        ans = ';tuple;' + ','.join(builder) + ';end-tuple;'
        main_logger.debug(f'Result is {ans}')
        return ans

    @staticmethod
    def _dict_to_str(value: dict) -> str:
        main_logger.debug('Converting a dict to a string...')
        builder = []
        for key, val in value.items():
            builder.append(_DiskCacheNameConverters.to_str(key) + ':'
                           + _DiskCacheNameConverters.to_str(val))

        main_logger.debug(_DiskCacheNameConverters.FINISH_ITER_MSG)
        ans = ';dict;' + ','.join(builder) + ';end-dict;'
        main_logger.debug(f'Result is {ans}')
        return ans

    _converters = {
        float: _file_str,
        str: _file_str,
        int: _file_str,
        datetime: _datetime_str,
        date: _date_str,
        time: _time_str,
        list: _list_to_str,
        tuple: _tuple_to_str,
        dict: _dict_to_str,
    }

    @staticmethod
    def to_str(value: Any) -> str:
        # Don't check if type is, instead check if instance of. Most functions will not be are
        # designed to expect any type of string/in/float. It may be possible to make this behavior
        # optional in the future, but for now design for the most probable case.
        for t, converter in _DiskCacheNameConverters._converters.items():
            if isinstance(value, t):
                return converter(value)

        return _DiskCacheNameConverters._file_str(value)


def disk_cache(target_dir: Union[str, bytes, os.PathLike],
               maxsize: int = 16,
               allow_mutation: bool = False,
               case_matters: bool = False,
               in_bytes: bool = True,
               write_converter: Callable[[DiskCacheType, DiskCacheIO], None] = None,
               read_converter: Callable[[DiskCacheIO], DiskCacheType] = None,
               cache_method: DiskCacheMethod = DiskCacheMethod.LFU,
               cache_arg: Any = None,
               **override_name_converters: Callable[[...], str]):
    """
    A decorator which caches results of a function in the form of files. It has multiple ways to
    customize behavior.

    :param target_dir: The directory where results of calling the decorated function should be.
        stored.
    :type target_dir: Union[str, bytes, os.PathLike]
    :param maxsize: The maximum number of results to cache. This must be a positive number greater
        than or equal to 0.
    :type maxsize: int
    :param allow_mutation: Whether mutation on the returned result should be allowed. If ``True``,
        it is guaranteed that the same instance of the result is used throughout execution. If
        ``False``, :func:`copy.deepcopy` will be used each time the function is called, and a
        deepcopy of the result will be returned. Using this can allow for a previously-saved
        object to be mutated if the function is used for a with statement, or if the function's
        ``mutate`` method is used.

        Example of effect:

        .. code-block:: python

            # Given the following function definition...
            @disk_cache('llamas/hares', allow_mutation=True)
            def func(a: str, b: int, c: list) -> dict:
                return dict(a=a, b=b, c=c)

            # and the following call being the first...
            a = func('d', 25, ['e', 'f'])

            # a should be {'a': 'd', 'b': 25, 'c': ['e', 'f']} and the object stored on the disk
            # should be {'a': 'd', 'b': 25, 'c': ['e', 'f']}.

            # If the function is called again with the same inputs and stored into a different
            # variable, it will still be the same object as a.
            b = func('d', 25, ['e', 'f'])

            # a is b should return True.
            # Also the following behavior should be expected if either is mutated...

            b['c'].append('g')

            # a is b and b == {'a': 'd', 'b': 25, 'c': ['e', 'f', 'g']} should be True. However, the
            # object stored on the disk should still be {'a': 'd', 'b': 25, 'c': ['e', 'f']}.

            # If it is desired to propagate the mutations to the saved object, the following
            # notation should be used...
            with func:
                c = func('d', 25, ['e', 'f'])
                c['c'].append('h')

            # more code...

            # The object stored on the disk after this should be
            # {'a': 'd', 'b': 25, 'c': ['e', 'f', 'g', 'h']}. c should also be equivalent to the
            # same object.

            # Alternatively, at the end of execution, the following can be called with the same
            # results...
            func.mutate()

    :type allow_mutation: bool
    :param case_matters: Whether upper/lower case in file names matters. If it does not matter, all
        stored values will be in lower case.
    :type case_matters: bool
    :param in_bytes: Whether the storage method of the data requires reading/writing in bytes.
        Defaults to ``True`` since the default serialization method is pickling.
    :type in_bytes: bool
    :param write_converter: The converter that should be used to write objects to the disk. Should
        accept the expected type of object to be stored and the IO stream which will write to the
        disk.
    :type write_converter: Optional[Callable[[DiskCacheType, DiskCacheIO], None]]
    :param read_converter: The converter that should be used to read objects from the disk. Should
        accept the IO stream which will read from the disk.
    :type read_converter: Optional[Callable[[DiskCacheIO], DiskCacheType]]
    :param cache_method: The cache method to use for the disk-cached function. Available options
        are:

        1. ``DiskCacheMethod.LRU`` - Uses an LRU caching style, which equates to the
           least-recently-used result being removed from the cache when making space for a new
           result.
        2. ``DiskCacheMethod.LFU`` - Uses an LFU caching style, which equates to the
           least-frequently-used result being removed from the cache when making space for a new
           result.
        3. ``DiskCacheMethod.WUNC`` - Uses a weighted-use-and-neglect caching style, which is a bit
           more complex than the other available methods. Essentially, it uses both the number of
           hits and the number of misses on a result to calculate how like the value is to be needed
           again. Misses are divided by ``maxsize``, which will be multiplied by ``cache_arg`` (if
           given), then they are subtracted from hits to get the weight of a result. This can be
           represented as ``hits - (misses / (maxsize * cache_arg))``.
        4. ``DiskCacheMethod.CUSTOM`` - Uses a custom user-defined method to determine caching
           style. When this is used, ``cache_arg`` must be specified, and should consist of an
           iterable with three functions. For each of these functions, the following parameters will
           be passed:

           *maxsize* - ``int``: The maximum size of the cache.

           *index* - ``Dict[str, list]``: The cache's index, which should be used to store a list
           for each function where the true name of the file (determined by the ``DiskCache``
           itself) is the first element and any info used for decision-making should be stored in
           further elements.

           These functions are used in the following way:

           **Function 1 -**

           ``(maxsize: int, index: Dict[str, List[Any]], filename: str)``

           *filename* - ``str``: The name of the result being requested. Can be used to search
           index.

           This function should be used to make any changes desired *before* the target file is
           determined. It does not need to return anything.

           **Function 2 -**

           ``self._cache_arg[1](maxsize: int, index: Dict[str, List[Any]]) -> Tuple[str, str]``

           This function should select the correct filename to be replaced when at ``maxsize``. It
           should return this as well as the corresponding true filename from index in the order
           ``true_filename``, ``filename``.

           .. note::

            This function will only be called if the cache is definitely at ``maxsize``.

           **Function 3 -**

           ``(maxsize: int, index: Dict[str, List[Any]], filename: str, true_filename: str)``

           *filename* - ``str``: The name of the result being requested. Can be used to search
           index.

           *true_filename* - ``str``: The actual file name of the file, generated by the cache and
           meant to be used if filename is not already in the index.

           This function should be used to perform changes to the index after all other steps are
           completed. It does not need to return anything.
    :type cache_method: The method to use for caching.
    :param cache_arg: An extra argument consumed by some cache methods.
    :type cache_arg: Any
    :param override_name_converters: Any custom methods to override how parameter values are written
        to the string.
    :type override_name_converters: Callable[[...], str]
    """
    if write_converter is None:
        write_converter = pickle.dump

    if read_converter is None:
        read_converter = pickle.load

    if case_matters:
        formatter = _DiskCacheNameConverters.to_str

    else:
        formatter = lambda x: _DiskCacheNameConverters.to_str(x).lower()

    # Custom does not have built-in handling for an empty cache_arg. Check if cache_arg is valid
    # here.
    if cache_method == DiskCacheMethod.CUSTOM:
        if (cache_arg is None or not check_iterable_not_string(cache_arg)
                or len(cache_arg) < 3 or not callable(cache_arg[0])
                or not callable(cache_arg[1]) or not callable(cache_arg[2])):
            raise TypeError('cache_arg should be specified as an iterable of at least three '
                            'callables when using DiskCacheMethod.CUSTOM.')

    def wrapper(funk: callable) -> callable:
        results = _DiskCacheResults(target_dir, maxsize, allow_mutation, in_bytes, write_converter,
                                    read_converter, funk, cache_method, cache_arg)
        funk_sig = inspect.signature(funk)

        class DiskCache:
            @wraps(funk)
            def __call__(self, *args, **kwargs):
                main_logger.debug('Binding args and kwargs to internal function...')
                _args = funk_sig.bind(*args, **kwargs)
                _args.apply_defaults()
                main_logger.debug('Arguments bound.')
                main_logger.debug('Building file name for arguments...')
                builder = []
                for name, arg in _args.arguments.items():
                    main_logger.debug(f'Arg {arg} encountered. Converting to string...')
                    if name in override_name_converters:
                        main_logger.debug('An overriding arg converter exists for the current arg. '
                                          'Using converter...')
                        builder.append(override_name_converters[name](arg))

                    else:
                        builder.append(t := formatter(arg))

                    main_logger.debug(f'Converted. Result is {t}.')

                main_logger.debug('All args interpreted. Making full name...')
                file_name = '\\'.join(builder)
                main_logger.debug(f'Full name made. Result is {file_name}.')

                return results.get(file_name, *args, **kwargs)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.mutate()

            @staticmethod
            def mutate():
                results.set()

            @staticmethod
            def cache_clear():
                results.clear()

            @property
            def __index(self):
                return results._index

        return DiskCache()

    return wrapper
