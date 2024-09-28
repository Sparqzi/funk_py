from collections import namedtuple

import pytest

from funk_py.modularity.type_matching import thoroughly_check_equality
from funk_py.sorting.pieces import convert_to_agg_def_dict, AggDef, _AggregationDefinition, \
    aggregate, convert_from_agg_def_dict


KEY1 = 'key1'
KEY2 = 'key2'
KEY3 = 'key3'
KEY4 = 'key4'
COUNT = 'count'
TOTAL = 'total'
INVALID = 'invalid'
ID = 'id'

AggDefDef = namedtuple('AggDefDef', ('name', 'value'))


@pytest.fixture
def sum_(): return AggDefDef('SUM', AggDef.SUM)


@pytest.fixture
def avg(): return AggDefDef('AVG', AggDef.AVG)


@pytest.fixture
def gtr(): return AggDefDef('GREATER', AggDef.GREATER)


@pytest.fixture
def exist(): return AggDefDef('EXISTS', AggDef.EXISTS)


@pytest.fixture
def one_of(): return AggDefDef('ONE_OF', AggDef.ONE_OF)


@pytest.fixture
def gtr_of(): return AggDefDef('GREATER_OF', AggDef.GREATER_OF)


class TestConvertFromJson:
    def test_convert_agg_def_dict_simple_agg_def(self, sum_, avg):
        input_data = {KEY1: sum_.name, KEY2: avg.name}
        expected_output = {KEY1: sum_.value, KEY2: avg.value}
        assert convert_to_agg_def_dict(input_data) == expected_output

    def test_convert_agg_def_dict_comp_agg_def(self, sum_, gtr, exist):
        input_data = {KEY1: [sum_.name, {KEY3: gtr.name, KEY4: exist.name}]}
        expected_output = {KEY1: [sum_.value, {KEY3: gtr.value, KEY4: exist.value}]}
        assert convert_to_agg_def_dict(input_data) == expected_output

    def test_convert_agg_def_dict_invalid_string(self):
        input_data = {KEY1: INVALID}
        with pytest.raises(TypeError,
                           match='The given PlainAggDef includes an unknown AggDef string.'):
            convert_to_agg_def_dict(input_data)

    def test_convert_agg_def_dict_invalid_list_length(self, sum_):
        input_data = {KEY1: [sum_.name]}  # Should have a second element on the list.
        with pytest.raises(TypeError,
                           match='The given PlainAggDef has an invalid list. It\'s too long or too '
                                 'short.'):
            convert_to_agg_def_dict(input_data)

    def test_convert_agg_def_dict_invalid_comp_check(self, one_of):
        input_data = {KEY1: [one_of.name, INVALID]}
        with pytest.raises(TypeError,
                           match='The given PlainAggDef has an invalid complex list check.'):
            convert_to_agg_def_dict(input_data)

    def test_convert_agg_def_dict_invalid_check_type(self, sum_):
        input_data = {KEY1: [sum_.name, {KEY3: INVALID}]}
        with pytest.raises(TypeError,
                           match='The given PlainAggDef has an unrecognized type of check.'):
            convert_to_agg_def_dict(input_data)

    def test_convert_agg_def_dict_complex_dict_check(self, gtr_of):
        input_data = {KEY1: [gtr_of.name, {'item1': 1, 'item2': 2}]}
        expected_output = {KEY1: gtr_of.value({'item1': 1, 'item2': 2})}
        assert thoroughly_check_equality(convert_to_agg_def_dict(input_data), expected_output)


class TestConvertToJson:
    def test_convert_agg_def_dict_simple_agg_def(self, sum_, avg):
        input_data = {KEY1: sum_.value, KEY2: avg.value}
        expected_output = {KEY1: sum_.name, KEY2: avg.name}
        assert convert_from_agg_def_dict(input_data) == expected_output

    def test_convert_agg_def_dict_comp_agg_def(self, sum_, gtr, exist):
        input_data = {KEY1: [sum_.value, {KEY3: gtr.value, KEY4: exist.value}]}
        expected_output = {KEY1: [sum_.name, {KEY3: gtr.name, KEY4: exist.name}]}
        assert convert_from_agg_def_dict(input_data) == expected_output

    def test_convert_agg_def_dict_invalid_list_length(self, sum_):
        input_data = {KEY1: [sum_.value]}  # Should have a second element on the list.
        with pytest.raises(TypeError,
                           match='A TrueAggDef shouldn\'t have a list of length greater than two.'):
            convert_from_agg_def_dict(input_data)

    def test_convert_agg_def_dict_complex_dict_check(self, gtr_of):
        input_data = {KEY1: gtr_of.value({'item1': 1, 'item2': 2})}
        expected_output = {KEY1: [gtr_of.name, {'item1': 1, 'item2': 2}]}
        assert convert_from_agg_def_dict(input_data), expected_output


class TestAggregationDefinition:
    def test_init_with_valid_dict(self, sum_, avg):
        agg_def = {KEY1: sum_.value, KEY2: avg.value}
        aggregator = _AggregationDefinition(agg_def)
        # These functions cannot be effectively compared since one is a static method and one is
        # not. As such, test their effects are correct.
        assert aggregator.simple_agg_defs[KEY1](1, 2) == 3
        assert aggregator.simple_agg_defs[KEY1](1, 2) == 3
        assert aggregator.simple_agg_defs[KEY1](3, 8) == 11
        assert aggregator.simple_agg_defs[KEY1](8, 3) == 11
        assert aggregator.simple_agg_defs[KEY2](1, None) == 1
        assert aggregator.simple_agg_defs[KEY2](2, 1) == 1.5
        assert aggregator.simple_agg_defs[KEY2](3, 1.5) == 2
        assert aggregator.simple_agg_defs[KEY2](8, 2) == 3.5

    def test_init_with_invalid_type(self):
        with pytest.raises(TypeError, match='An invalid agg_def was provided.'):
            _AggregationDefinition(INVALID)

    def test_add_simple_agg_def(self, sum_):
        aggregator = _AggregationDefinition()
        aggregator.add(KEY1, sum_.value)
        assert KEY1 in aggregator.simple_agg_defs

    def test_add_invalid_agg_def_type(self):
        aggregator = _AggregationDefinition()
        with pytest.raises(TypeError, match='An invalid agg_def was provided.'):
            aggregator.add(KEY1, INVALID)

    def test_add_complex_agg_def(self, sum_, gtr):
        complex_def = [sum_.value, {KEY2: gtr.value}]
        aggregator = _AggregationDefinition()
        aggregator.add(KEY1, complex_def)
        assert KEY1 in aggregator.complex_agg_defs

    def test_add_invalid_complex_def_length(self, sum_):
        aggregator = _AggregationDefinition()
        with pytest.raises(TypeError, match='An invalid agg_def was provided.'):
            aggregator.add(KEY1, [sum_.value])

    def test_process_items_with_valid_data(self, sum_, avg):
        agg_def = {TOTAL: sum_.value, COUNT: avg.value}
        aggregator = _AggregationDefinition(agg_def)

        items = [{TOTAL: 10, COUNT: 2}, {TOTAL: 20, COUNT: 3}]
        result = aggregator.process_items(items)

        assert result[TOTAL] == 30
        assert result[COUNT] == 2.5

    def test_process_items_with_invalid_data(self, sum_):
        agg_def = {TOTAL: sum_.value}
        aggregator = _AggregationDefinition(agg_def)

        items = [{TOTAL: 10}, {COUNT: 3}]  # Missing key
        result = aggregator.process_items(items)

        assert result == {TOTAL: 10, COUNT: 3}

    def test_process_items_with_checks(self, sum_, avg, exist):
        agg_def = {TOTAL: sum_.value, COUNT: [avg.value, {KEY1: exist.value}]}
        aggregator = _AggregationDefinition(agg_def)

        items = [{TOTAL: 10, COUNT: 2}, {TOTAL: 20, COUNT: None}]
        result = aggregator.process_items(items)

        assert result[TOTAL] == 30
        assert COUNT not in result

    def test_eval_item_with_success(self, sum_, avg):
        agg_def = {TOTAL: sum_.value, COUNT: avg.value}
        aggregator = _AggregationDefinition(agg_def)

        item = {TOTAL: 10, COUNT: 5}
        current = {}

        assert aggregator._eval_item(item, current) is True

    def test_eval_item_with_failure(self, gtr):
        agg_def = {COUNT: gtr.value}
        aggregator = _AggregationDefinition(agg_def)

        item = {COUNT: 5}
        current = {COUNT: 10}

        assert aggregator._eval_item(item, current) is False


class TestAggregate:
    @pytest.fixture
    def common_agg_def(self, sum_, avg): return {TOTAL: sum_.value, COUNT: avg.value}

    def test_aggregate_with_valid_data(self, sum_, avg):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2}, {ID: 1, TOTAL: 20, COUNT: 3},
            {ID: 2, TOTAL: 15, COUNT: 5}, {ID: 2, TOTAL: 25, COUNT: 10}
        ]
        identifiers = [ID]
        agg_def = {TOTAL: sum_.value, COUNT: avg.value}

        result = aggregate(data, identifiers, agg_def)

        expected_result = [{ID: 1, TOTAL: 30, COUNT: 2.5}, {ID: 2, TOTAL: 40, COUNT: 7.5}]
        assert result == expected_result

    def test_aggregate_with_no_data(self, common_agg_def):
        data = []
        identifiers = [ID]
        result = aggregate(data, identifiers, common_agg_def)
        assert result == []

    def test_aggregate_with_missing_keys(self, common_agg_def):
        data = [{ID: 1, TOTAL: 10}, {ID: 1, COUNT: 3}, {ID: 2, TOTAL: 15}]
        identifiers = [ID]
        result = aggregate(data, identifiers, common_agg_def)
        expected_result = [{ID: 1, TOTAL: 10, COUNT: 1.5}, {ID: 2, TOTAL: 15, COUNT: 0.0}]
        assert result == expected_result

    def test_aggregate_with_invalid_identifiers(self, common_agg_def):
        data = [{ID: 1, TOTAL: 10, COUNT: 2}, {ID: 2, TOTAL: 20, COUNT: 3}]
        identifiers = [INVALID]
        result = aggregate(data, identifiers, common_agg_def)
        assert result == [{ID: 2, TOTAL: 30, COUNT: 2.5}]

    def test_aggregate_with_complex_definition(self, sum_, avg, exist):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2, KEY1: 'llama'}, {ID: 1, TOTAL: 20, COUNT: 3},
            {ID: 1, TOTAL: 5, COUNT: 1}, {ID: 2, TOTAL: 15, COUNT: 5}
        ]
        identifiers = [ID]
        agg_def = {TOTAL: sum_.value, COUNT: [avg.value, {KEY1: exist.value}]}

        result = aggregate(data, identifiers, agg_def)
        expected_result = [{ID: 1, TOTAL: 35, COUNT: 2.0}, {ID: 2, TOTAL: 15}]
        assert result == expected_result

    def test_aggregate_with_empty_subsets(self, common_agg_def):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2}, {ID: 1, TOTAL: 20, COUNT: None},
            {ID: 2, TOTAL: None, COUNT: None}
        ]
        identifiers = [ID]
        result = aggregate(data, identifiers, common_agg_def)
        expected_result = [{ID: 1, TOTAL: 30, COUNT: 1.0}, {ID: 2, TOTAL: None, COUNT: 0.0}]
        assert result == expected_result

    def test_aggregate_with_other_data_as_dict(self, common_agg_def):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2}, {ID: 1, TOTAL: 20, COUNT: 3},
            {ID: 2, TOTAL: 15, COUNT: 5}
        ]
        identifiers = [ID]
        other_data = {TOTAL: 5, COUNT: 1}
        result = aggregate(data, identifiers, common_agg_def, other_data)
        expected_result = [{ID: 1, TOTAL: 35, COUNT: 2.0}, {ID: 2, TOTAL: 20, COUNT: 3.0}]
        assert result == expected_result

    def test_aggregate_with_other_data_as_iterable(self, common_agg_def):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2}, {ID: 1, TOTAL: 20, COUNT: 3},
            {ID: 2, TOTAL: 15, COUNT: 5}
        ]
        identifiers = [ID]
        other_data = [{TOTAL: 5, COUNT: 1}, {TOTAL: 3, COUNT: 2}]
        result = aggregate(data, identifiers, common_agg_def, other_data)
        expected_result = [{ID: 1, TOTAL: 38, COUNT: 2.0}, {ID: 2, TOTAL: 23, COUNT: 8 / 3}]
        assert result == expected_result

    def test_aggregate_with_other_data_as_callable(self, common_agg_def):
        data = [
            {ID: 1, TOTAL: 10, COUNT: 2}, {ID: 1, TOTAL: 20, COUNT: 3},
            {ID: 2, TOTAL: 15, COUNT: 5}, {ID: 3, TOTAL: 7, COUNT: 4},
        ]
        identifiers = [ID]

        def other_data_provider(item_id):
            if item_id.get(ID) == 1:
                return [{TOTAL: 5, COUNT: 1}, {TOTAL: 3, COUNT: 2}]

            elif item_id.get(ID) == 2:
                return {TOTAL: 2, COUNT: 1}

            return None

        result = aggregate(data, identifiers, common_agg_def, other_data_provider)

        expected_result = [
            {ID: 1, TOTAL: 38, COUNT: 2.0}, {ID: 2, TOTAL: 17, COUNT: 3.0},
            {ID: 3, TOTAL: 7, COUNT: 4}
        ]
        assert result == expected_result
