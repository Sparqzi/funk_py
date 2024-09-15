from collections import namedtuple
from xml.etree import ElementTree as ET

import pytest

from funk_py.modularity.basic_structures import Speed
from funk_py.sorting.converters import csv_to_json, xml_to_json


XmlTDef = namedtuple('XmlTDef', ('sans_attributes', 'input', 'output', 'speed'))
OTDef = namedtuple('OTDef', ('input', 'output', 'speed'))


T_MAX = 100
KEYS = ['k' + str(i) for i in range(T_MAX)]
VALS = ['v' + str(i) for i in range(T_MAX)]

ROOT = KEYS[0]
TEXT = 'text'

PS_55_000 = Speed(27_500, 0.5)
PS_45_000 = Speed(9_000, 0.2)
PS_40_000 = Speed(10_000, 0.25)
PS_35_000 = Speed(15_000, 0.5)
PS_5_000 = Speed(2_500, 0.5)
PS_6_000 = Speed(3_000, 0.5)
PS_8_000 = Speed(4_000, 0.5)


class TestXmlToJson:
    @pytest.fixture
    def xml_builder(self):
        return ET.Element(ROOT)

    ROOT_OF_NONE = {ROOT: {}}

    @pytest.fixture(params=((False, PS_40_000), (True, PS_40_000)),
                    ids=('with attributes', 'sans attributes'))
    def empty_xml(self, request, xml_builder):
        sans_attributes, speed = request.param

        _input = ET.tostring(xml_builder, encoding='utf8')

        output = self.ROOT_OF_NONE if sans_attributes else self.ROOT_OF_NONE

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_empty_xml_benchmark(self, empty_xml, benchmark):
        benchmark(xml_to_json, empty_xml.input, empty_xml.sans_attributes)

    V1 = VALS[0]
    ROOT_OF_VAL = {ROOT: V1}

    @pytest.fixture(params=((False, PS_40_000), (True, PS_40_000)),
                    ids=('with attributes', 'sans attributes'))
    def s_xml(self, request, xml_builder):
        """simple"""
        sans_attributes, speed = request.param

        xml_builder.text = self.V1
        _input = ET.tostring(xml_builder, encoding='utf8')

        if sans_attributes:
            output = self.ROOT_OF_VAL

        else:
            output = self.ROOT_OF_VAL

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_xml_benchmark(self, s_xml, benchmark):
        benchmark(xml_to_json, s_xml.input, s_xml.sans_attributes)

    V2 = VALS[1]
    K1 = KEYS[1]
    K2 = KEYS[2]

    @pytest.fixture
    def basic_attributes(self): return {self.K1: self.V1, self.K2: self.V2}

    @pytest.fixture
    def sa_xml_builder(self, basic_attributes): return ET.Element(ROOT, basic_attributes)

    @pytest.fixture(params=((False, PS_40_000), (True, PS_40_000)),
                    ids=('with attributes', 'sans attributes'))
    def sao_xml(self, request, basic_attributes, sa_xml_builder):
        """simple attribute-only"""
        sans_attributes, speed = request.param

        _input = ET.tostring(sa_xml_builder, encoding='utf8')

        output = {ROOT: basic_attributes}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_attribute_only_benchmark(self, sao_xml, benchmark):
        benchmark(xml_to_json, sao_xml.input, sao_xml.sans_attributes)

    KV1 = {KEYS[i]: VALS[i - 1] for i in range(1, T_MAX)}

    @pytest.fixture(params=((False, PS_5_000), (True, PS_5_000)),
                    ids=('with attributes', 'sans attributes'))
    def sna_xml(self, request, xml_builder):
        """simple no-attribute"""
        sans_attributes, speed = request.param
        for i in range(1, T_MAX):
            _builder = ET.SubElement(xml_builder, KEYS[i])
            _builder.text = VALS[i - 1]

        _input = ET.tostring(xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: self.KV1}

        else:
            output = {}
            _builder = output[ROOT] = {}
            _builder.update(self.KV1)

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_no_attribute_benchmark(self, sna_xml, benchmark):
        benchmark(xml_to_json, sna_xml.input, sna_xml.sans_attributes)

    KV2 = {KEYS[i]: VALS[i - 1] for i in range(3, T_MAX)}

    @pytest.fixture(params=((False, PS_5_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def sat_xml(self, request, basic_attributes, sa_xml_builder):
        """simple attribute-and-tag"""
        sans_attributes, speed = request.param

        for k, v in self.KV2.items():
            _builder = ET.SubElement(sa_xml_builder, k)
            _builder.text = v

        _input = ET.tostring(sa_xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: self.KV2}

        else:
            basic_attributes.update(self.KV2)
            output = {ROOT: basic_attributes}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_attribute_and_tag_benchmark(self, sat_xml, benchmark):
        benchmark(xml_to_json, sat_xml.input, sat_xml.sans_attributes)

    L1 = [VALS[i] for i in range(T_MAX)]

    @pytest.fixture(params=((False, PS_6_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def snalna_xml(self, request, xml_builder):
        """simple no-attribute -> list no-attribute"""
        sans_attributes, speed = request.param

        for v in self.L1:
            _builder = ET.SubElement(xml_builder, self.K1)
            _builder.text = v

        _input = ET.tostring(xml_builder, encoding='utf8')

        output = {ROOT: {self.K1: self.L1}}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_no_attribute_list_no_attribute_benchmark(self, snalna_xml, benchmark):
        benchmark(xml_to_json, snalna_xml.input, snalna_xml.sans_attributes)

    L2 = [{KEYS[i]: VALS[i - 2], KEYS[i + 1]: VALS[i - 1]} for i in range(2, T_MAX - 2, 2)]

    @pytest.fixture(params=((False, PS_6_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def snalao_xml(self, request, xml_builder):
        """simple no-attribute -> list attribute-only"""
        sans_attributes, speed = request.param

        for v in self.L2:
            ET.SubElement(xml_builder, self.K1, v)

        _input = ET.tostring(xml_builder, encoding='utf8')

        output = {ROOT: {self.K1: self.L2}}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_no_attribute_list_attribute_only_benchmark(self, snalao_xml, benchmark):
        benchmark(xml_to_json, snalao_xml.input, snalao_xml.sans_attributes)

    L3 = [{TEXT: VALS[i],
           KEYS[i]: VALS[i - 2],
           KEYS[i + 1]: VALS[i - 1]} for i in range(2, T_MAX - 3, 3)]

    @pytest.fixture(params=((False, PS_6_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def snalat_xml(self, request, xml_builder):
        """simple no-attribute -> list attribute-and-tag"""
        sans_attributes, speed = request.param

        for v in self.L3:
            _builder = ET.SubElement(xml_builder, self.K1,
                                     {k: _v for k, _v in v.items() if k != TEXT})
            _builder.text = v[TEXT]

        _input = ET.tostring(xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: {self.K1: [v[TEXT] for v in self.L3]}}

        else:
            output = {ROOT: {self.K1: self.L3}}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_no_attribute_list_attribute_and_tag_benchmark(self, snalat_xml, benchmark):
        benchmark(xml_to_json, snalat_xml.input, snalat_xml.sans_attributes)

    L4 = [VALS[i - 4] for i in range(4, T_MAX)]
    K3 = KEYS[3]

    @pytest.fixture(params=((False, PS_6_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def salna_xml(self, request, basic_attributes, sa_xml_builder):
        """simple attribute -> list no-attribute"""
        sans_attributes, speed = request.param

        for v in self.L4:
            _builder = ET.SubElement(sa_xml_builder, self.K3)
            _builder.text = v

        _input = ET.tostring(sa_xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: {self.K3: self.L4}}

        else:
            basic_attributes[self.K3] = self.L4
            output = {ROOT: basic_attributes}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_attribute_list_no_attribute_benchmark(self, salna_xml, benchmark):
        benchmark(xml_to_json, salna_xml.input, salna_xml.sans_attributes)

    L5 = [{KEYS[i]: VALS[i - 4], KEYS[i + 1]: VALS[i - 3]} for i in range(4, T_MAX - 2, 2)]

    @pytest.fixture(params=((False, PS_8_000), (True, PS_8_000)),
                    ids=('with attributes', 'sans attributes'))
    def salao_xml(self, request, basic_attributes, sa_xml_builder):
        """simple attribute -> list attribute-only"""
        sans_attributes, speed = request.param

        for v in self.L5:
            ET.SubElement(sa_xml_builder, self.K3, v)

        _input = ET.tostring(sa_xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: {self.K3: self.L5}}

        else:
            basic_attributes[self.K3] = self.L5
            output = {ROOT: basic_attributes}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_attribute_list_attribute_only_benchmark(self, salao_xml, benchmark):
        benchmark(xml_to_json, salao_xml.input, salao_xml.sans_attributes)

    L6 = [{TEXT: VALS[i - 2],
           KEYS[i]: VALS[i - 4],
           KEYS[i + 1]: VALS[i - 3]} for i in range(4, T_MAX - 3, 3)]

    @pytest.fixture(params=((False, PS_6_000), (True, PS_6_000)),
                    ids=('with attributes', 'sans attributes'))
    def salat_xml(self, request, basic_attributes, sa_xml_builder):
        """simple attribute -> list attribute-and-tag"""
        sans_attributes, speed = request.param

        for v in self.L6:
            _builder = ET.SubElement(sa_xml_builder, self.K3,
                                     {k: _v for k, _v in v.items() if k != TEXT})
            _builder.text = v[TEXT]

        _input = ET.tostring(sa_xml_builder, encoding='utf8')

        if sans_attributes:
            output = {ROOT: {self.K3: [v[TEXT] for v in self.L6]}}

        else:
            basic_attributes[self.K3] = self.L6
            output = {ROOT: basic_attributes}

        return XmlTDef(sans_attributes, _input, output, speed)

    @pytest.mark.benchmark
    def test_simple_attribute_list_attribute_and_tag_benchmark(self, salat_xml, benchmark):
        benchmark(xml_to_json, salat_xml.input, salat_xml.sans_attributes)


class TestCsvToJson:
    @pytest.fixture
    def simple_csv(self):
        _input = ','.join(KEYS[:5])
        output = []
        for i in range(0, 10):
            _input += '\n' + ','.join(VALS[i * 5:i * 5 + 5])
            output.append({k: v for k, v in zip(KEYS[:5], VALS[i * 5:i * 5 + 5])})

        return OTDef(_input, output, PS_55_000)

    @pytest.mark.benchmark
    def test_simple_csv_benchmark(self, simple_csv, benchmark):
        benchmark(csv_to_json, simple_csv.input)

    @pytest.fixture
    def quoted_csv(self):
        _input = ','.join(f'"{k}"' for k in KEYS[:5])
        output = []
        for i in range(0, 10):
            _input += '\n' + ','.join(f'"{v}"' for v in VALS[i * 5:i * 5 + 5])
            output.append({k: v for k, v in zip(KEYS[:5], VALS[i * 5:i * 5 + 5])})

        return OTDef(_input, output, PS_55_000)

    @pytest.mark.benchmark
    def test_quoted_csv_benchmark(self, quoted_csv, benchmark):
        benchmark(csv_to_json, quoted_csv.input)

    @pytest.fixture
    def quoted_csv_commas_inside(self):
        k = [f'{KEYS[i]},{KEYS[i + 1]}' for i in range(0, 10, 2)]
        _input = ','.join(f'"{_k}"' for _k in k)
        output = []
        for i in range(0, 10):
            v = [f'{VALS[i * 10 + j]},{VALS[i * 10 + 1 + j]}' for j in range(5)]
            _input += '\n' + ','.join(f'"{_v}"' for _v in v)
            output.append({_k: _v for _k, _v in zip(k, v)})
            
        return OTDef(_input, output, PS_35_000)

    @pytest.mark.benchmark
    def test_quoted_csv_commas_inside_benchmark(self, quoted_csv_commas_inside, benchmark):
        benchmark(csv_to_json, quoted_csv_commas_inside.input)

    @pytest.fixture
    def quoted_csv_quotes_inside(self):
        k = [f'{KEYS[i]}""{KEYS[i + 1]}' for i in range(0, 10, 2)]
        _input = ','.join(f'"{_k}"' for _k in k)
        output = []
        for i in range(1, 10):
            v = [f'{VALS[i * 10 + j]}""{VALS[i * 10 + 1 + j]}' for j in range(5)]
            _input += '\n' + ','.join(f'"{_v}"' for _v in v)
            output.append({_k.replace('""', '"'): _v.replace('""', '"') for _k, _v in zip(k, v)})

        return OTDef(_input, output, PS_45_000)

    @pytest.mark.benchmark
    def test_quoted_csv_quotes_inside_benchmark(self, quoted_csv_quotes_inside, benchmark):
        benchmark(csv_to_json, quoted_csv_quotes_inside.input)
