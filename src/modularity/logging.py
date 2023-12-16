import logging
from os import getenv
import sys
from typing import Union


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

    format_str = '%(levelname)-' + max_length + 's: %(name)s - '
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
