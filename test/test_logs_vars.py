import logging
from logging import getLogger

import pytest

from t_support import cov, cov_counter
from funk_py.modularity.logging import logs_vars


# The following manages whether the generated coverage instance from t_support should report. This
# method of coverage is used so that coverage can be turned off to not interfere in timed tests.
@pytest.fixture(scope='session', autouse=True)
def c():
    if not cov_counter.value:
        # We don't want to start coverage more than once
        cov.start()

    cov_counter.value += 1

    yield cov

    cov_counter.value -= 1

    # We don't want to report till all test modules are completed...
    if not cov_counter.value:
        cov.stop()
        cov.save()
        cov.report()

ARGUMENTS = 'Arguments:'
LOGGER = getLogger('testy')
ANSWER = 42
LIFE = 'Bobbert'
NAME = 'Stapler'
BAD_NAME = 45
AGE = 300


LOG_NAME_LOOKUP = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING,
                   'error': logging.ERROR, 'critical': logging.CRITICAL}


# Given this is testing a logging decorator, multiple thousands of tests are run with slight
# differences, not just edge cases. If this breaks, it could mean endless headaches. It may be worth
# it to later re-locate the logic for determining log level out of the decorator so that it can be
# tested, separately, but to prevent silly mistakes like accidentally hard-coding a log level, it is
# best to keep these tests.


@pytest.fixture(params=['debug', 'info', 'warning', 'error', 'critical'])
def different_str_levels(request): return request.param


@pytest.fixture(params=['upper', 'lower'])
def all_different_str_levels(request, different_str_levels):
    return getattr(different_str_levels, request.param)()


@pytest.fixture(params=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
                        logging.CRITICAL])
def different_int_levels(request): return request.param


@pytest.fixture(params=[None, 'This is a start message.', 42])
def different_start_messages(request): return request.param


class MessageState:
    def __init__(self, start_message, end_message):
        self.start_message = start_message
        self.end_message = end_message


@pytest.fixture(params=[None, 'This is an end message.', 24])
def different_message_combos(request, different_start_messages):
    c = MessageState(different_start_messages, request.param)
    return c


@pytest.fixture(params=[(), ('inner_self',)])
def ignore_class(request): return request.param


def append_class_args(builder, use_self):
    builder.append(ARGUMENTS)
    if not use_self:
        builder.append(lambda x: f'inner_self = {x}')

    builder.append(f'answer = {repr(ANSWER)}')
    builder.append(f'life = {repr(LIFE)}')


class TestOnClassStr:
    @pytest.fixture
    def t_class(self, different_str_levels, different_message_combos, ignore_class):
        class Testy:
            @logs_vars(LOGGER, *ignore_class,
                       start_message=different_message_combos.start_message,
                       end_message=different_message_combos.end_message,
                       var_message_level=different_str_levels)
            def __init__(inner_self, answer, life):
                inner_self.answer = answer
                inner_self.life = life

        return Testy, different_str_levels, different_message_combos, ignore_class

    # Just making sure that it applies the decorator at least once.
    def test_not_break(self, t_class): pass

    @pytest.fixture(params=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
                            logging.CRITICAL])
    def t_runs(self, request, t_class):
        if request.param == logging.DEBUG:
            builder = []
            if (t := t_class[2].start_message) is not None:
                builder.append(t)

            append_class_args(builder, t_class[3])
            if (t := t_class[2].end_message) is not None:
                builder.append(t)

            return t_class[0], request.param, builder

        builder = []
        if request.param <= LOG_NAME_LOOKUP[t_class[1].lower()]:
            append_class_args(builder, t_class[3])

        return t_class[0], request.param, builder

    def test_logs_correctly(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(t_runs[1])
        testy = t_runs[0](ANSWER, LIFE)

        assert len(caplog.records) == len(t_runs[2])

        for i in range(len(t_runs[2])):
            if callable(t_runs[2][i]):
                assert caplog.records[i].msg == t_runs[2][i](testy)

            else:
                assert caplog.records[i].msg == t_runs[2][i]

    def test_result_unvoided(self, t_runs):
        LOGGER.setLevel(t_runs[1])
        testy = t_runs[0](ANSWER, LIFE)

        assert testy is not None
        assert testy.life == LIFE
        assert testy.answer == ANSWER


class TestOnClassInt:
    @pytest.fixture
    def t_class(self, different_int_levels, different_message_combos, ignore_class):
        class Testy:
            @logs_vars(LOGGER, *ignore_class,
                       start_message=different_message_combos.start_message,
                       end_message=different_message_combos.end_message,
                       var_message_level=different_int_levels)
            def __init__(inner_self, answer, life):
                inner_self.answer = answer
                inner_self.life = life

        return Testy, different_int_levels, different_message_combos, ignore_class

    # Just making sure that it applies the decorator at least once.
    def test_not_break(self, t_class): pass

    @pytest.fixture(params=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
                            logging.CRITICAL])
    def t_runs(self, request, t_class):
        if request.param == logging.DEBUG:
            builder = []
            if (t := t_class[2].start_message) is not None:
                builder.append(t)

            append_class_args(builder, t_class[3])
            if (t := t_class[2].end_message) is not None:
                builder.append(t)

            return t_class[0], request.param, builder

        builder = []
        if request.param <= t_class[1]:
            append_class_args(builder, t_class[3])

        return t_class[0], request.param, builder

    def test_logs_correctly(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(t_runs[1])
        testy = t_runs[0](ANSWER, LIFE)

        assert len(caplog.records) == len(t_runs[2])

        for i in range(len(t_runs[2])):
            if callable(t_runs[2][i]):
                assert caplog.records[i].msg == t_runs[2][i](testy)

            else:
                assert caplog.records[i].msg == t_runs[2][i]

    def test_result_unvoided(self, t_runs):
        LOGGER.setLevel(t_runs[1])
        testy = t_runs[0](ANSWER, LIFE)

        assert testy is not None
        assert testy.life == LIFE
        assert testy.answer == ANSWER


def append_function_args(builder):
    builder.append(ARGUMENTS)
    builder.append(f'name = {repr(NAME)}')
    builder.append(f'age = {repr(AGE)}')


class TestFunctionStr:
    @pytest.fixture
    def t_func(self, different_str_levels, different_message_combos, ignore_class):
        @logs_vars(LOGGER, *ignore_class,
                   start_message=different_message_combos.start_message,
                   end_message=different_message_combos.end_message,
                   var_message_level=different_str_levels)
        def testy(name, age): return 'Hi, I\'m ' + name + ' and I\'m ' + str(age) + ' years old.'

        return testy, different_str_levels, different_message_combos

    # Just making sure that it applies the decorator at least once.
    def test_not_break(self, t_func): pass

    @pytest.fixture(params=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
                            logging.CRITICAL])
    def t_runs(self, request, t_func):
        if request.param == logging.DEBUG:
            builder = []
            if (t := t_func[2].start_message) is not None:
                builder.append(t)

            append_function_args(builder)
            if (t := t_func[2].end_message) is not None:
                builder.append(t)

            return t_func[0], request.param, builder

        builder = []
        if request.param <= LOG_NAME_LOOKUP[t_func[1].lower()]:
            append_function_args(builder)

        return t_func[0], request.param, builder

    def test_logs_correctly(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(t_runs[1])
        t_runs[0](NAME, AGE)

        assert len(caplog.records) == len(t_runs[2])

        for i in range(len(t_runs[2])):
            assert caplog.records[i].msg == t_runs[2][i]

    def test_result_unvoided(self, t_runs):
        LOGGER.setLevel(t_runs[1])
        ans = t_runs[0](NAME, AGE)

        assert ans == f'Hi, I\'m {NAME} and I\'m {AGE} years old.'

    def test_logs_error(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(logging.DEBUG)
        try:
            t_runs[0](BAD_NAME, AGE)

        except Exception as e:
            assert len(caplog.records) >= 2
            assert caplog.records[-2].msg == ('A variable-logged function failed to execute '
                                              'completely.')
            assert caplog.records[-1].msg == e


class TestFunctionInt:
    @pytest.fixture
    def t_func(self, different_int_levels, different_message_combos,
               ignore_class):
        @logs_vars(LOGGER, *ignore_class,
                   start_message=different_message_combos.start_message,
                   end_message=different_message_combos.end_message,
                   var_message_level=different_int_levels)
        def testy(name, age): return 'Hi, I\'m ' + name + ' and I\'m ' + str(age) + ' years old.'

        return testy, different_int_levels, different_message_combos

    # Just making sure that it applies the decorator at least once.
    def test_not_break(self, t_func): pass

    @pytest.fixture(params=[logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
                            logging.CRITICAL])
    def t_runs(self, request, t_func):
        if request.param == logging.DEBUG:
            builder = []
            if (t := t_func[2].start_message) is not None:
                builder.append(t)

            append_function_args(builder)
            if (t := t_func[2].end_message) is not None:
                builder.append(t)

            return t_func[0], request.param, builder

        builder = []
        if request.param <= t_func[1]:
            append_function_args(builder)

        return t_func[0], request.param, builder

    def test_logs_correctly(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(t_runs[1])
        t_runs[0](NAME, AGE)

        assert len(caplog.records) == len(t_runs[2])

        for i in range(len(t_runs[2])):
            assert caplog.records[i].msg == t_runs[2][i]

    def test_result_unvoided(self, t_runs):
        LOGGER.setLevel(t_runs[1])
        ans = t_runs[0](NAME, AGE)

        assert ans == f'Hi, I\'m {NAME} and I\'m {AGE} years old.'

    def test_logs_error(self, t_runs, caplog):
        caplog.set_level(logging.DEBUG)

        LOGGER.setLevel(logging.DEBUG)
        try:
            t_runs[0](BAD_NAME, AGE)

        except Exception as e:
            assert len(caplog.records) >= 2
            assert caplog.records[-2].msg == ('A variable-logged function failed to execute '
                                              'completely.')
            assert caplog.records[-1].msg == e
