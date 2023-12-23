import inspect
import logging
from functools import wraps
from os import getenv
import sys
from typing import Union, Callable


def __make_log_at_level_func(level_value: int):
    def log_at_level(logger: logging.Logger, message, *args, **kwargs):
        if logger.isEnabledFor(level_value):
            logger._log(level_value, message, args, **kwargs)

    return log_at_level


def make_logger(name: str, /, env_var: str = 'LOG_LEVEL', *,
                log_to_file: str = None,
                default_level: Union[str, int] = logging.INFO,
                show_function: bool = False,
                **custom_levels: int) -> logging.Logger:
    r"""
    This creates a logger with a few default settings as well as some custom
    levels, if specified. The format of messages for this logger should be
    '

    :param name: The name of the logger.
    :param env_var: The environment variable it should be linked to.
    :param log_to_file: If this is specified, it should be the full file name
        for the logger to log to.
    :param default_level: This may be either a str or an int representing the
        desired log level.
        `per python docs <https://docs.python.org/3/library/logging.html#levels>`__,
        the default available levels are: logging.notset = 0,
        logging.debug = 10, logging.info = 20, logging.warning = 30,
        logging.error = 40, and logging.CRITICAL = 50.
    :param show_function: Whether you want the function name that is being
        logged from to show up in the info.
    :param custom_levels: *Please note that this is global. If you define it for
        one logger, it exists for all loggers. Those loggers may not be set up
        to use it by default, though.*
    :return:
    """
    logger = logging.getLogger(name)

    max_length = 8

    if len(custom_levels):
        for levelname, value in custom_levels.items():
            logging.addLevelName(value, levelname.upper())
            log_at_level = __make_log_at_level_func(value)
            setattr(logging.Logger, levelname.lower(), log_at_level)
            if t := len(levelname) > max_length:
                max_length = t

    level = getenv(env_var, default_level)
    logger.setLevel(level if type(level) is int else level.upper())

    format_str = '%(levelname)-' + str(max_length) + 's: %(name)s - '
    if show_function:
        format_str += '%funcName)s - %(message)s'
        formatter = logging.Formatter(format_str)

    else:
        format_str += '%(message)s'
        formatter = logging.Formatter(format_str)

    primary_handler = logging.StreamHandler(sys.stdout)
    primary_handler.setFormatter(formatter)
    logger.addHandler(primary_handler)

    if log_to_file is not None:
        file_handler = logging.FileHandler(log_to_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _get_log_level_func(logger: logging.Logger, log_level: Union[str, int]):
    if type(log_level) is int:
        return getattr(logger, logging.getLevelName(log_level).lower())

    return getattr(logger, log_level.lower())


def _extract_and_log_values_message(log_call: Callable, sig: inspect.Signature,
                                    args, kwargs, names: list):
    arg_result = sig.bind(*args, **kwargs)
    log_call('Arguments:')
    for name, value in arg_result.arguments.items():
        if name in names:
            log_call(name + ' = ' + repr(value))


def logs_vars(logger: logging.Logger, *ignore: str, start_message: str = None,
              start_message_level: Union[str, int] = logging.DEBUG,
              end_message: str = None,
              end_message_level: Union[str, int] = logging.DEBUG,
              var_message_level: Union[str, int] = logging.DEBUG):
    """
    A decorator which will log the variables of a function at the given level
    when the function is called. In the event that the wrapped function raises
    an exception, this decorator will log an error in the provided logger, and
    pass the exception up to the caller.

    :param logger: The Logger to log with.
    :param ignore: Any parameters that should not be logged.
    :param start_message: A message that gets logged before the function even
        starts executing
    :param start_message_level: The level at which start_message should log.
        This defaults to logging.DEBUG.
    :param end_message: A message that gets logged after the function stops
        executing (assuming no unexpected errors).
    :param end_message_level: The level at which the end_message should log.
        This defaults to logging.DEBUG.
    :param var_message_level: The level at which the variables should log. This
        defaults to logging.DEBUG.
    """
    def wrap(func):
        sig = inspect.signature(func)
        parameters = sig.parameters

        names = []
        for name, parameter in parameters.items():
            names.append(name)

        if len(ignore):
            for i in range(len(names) - 1, -1, -1):
                if names[i] in ignore:
                    del names[i]

        if start_message is not None:
            start_log = _get_log_level_func(logger, start_message_level)

        else:
            # Need function to do nothing if there's no start_message.
            def start_log(msg: str): pass

        if end_message is not None:
            end_log = _get_log_level_func(logger, end_message_level)

        else:
            # Need function to do nothing if there's no end_message.
            def end_log(msg: str): pass

        var_log = _get_log_level_func(logger, var_message_level)

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_log(start_message)
            _extract_and_log_values_message(var_log, sig, args, kwargs, names)
            try:
                ans = func(*args, **kwargs)

            except Exception as e:
                logger.error('A variable-logged function failed to execute'
                             ' completely.')
                logger.error(e)
                raise e

            end_log(end_message)

            return ans

        return wrapper

    return wrap
