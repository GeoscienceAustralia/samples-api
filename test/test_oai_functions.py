import unittest
import requests
from lxml import etree
from io import StringIO
from routes.oai_functions import valid_oai_args, validate_oai_parameters, ParameterError
import os


class TestFunctionsOAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.uri = 'http://localhost:5000/oai'
        cls.dir = os.path.dirname(os.path.realpath(__file__))

    def test_true(self):
        args = {
            'verb': 'GetRecord',
            'identifier': 'AU100',
            'metadataPrefix': 'oai_dc'}

        self.assertTrue(valid_oai_args(args['verb']))
        self.assertTrue(validate_oai_parameters(args))

    def test_Error(self):
        args = {
            'verb': 'GetRec',
            'identifier': 'AU100',
            'metadataPrefix': 'oai_dc'}

        self.assertRaises(ParameterError, validate_oai_parameters, args)

    def test_missing_required(self):
        args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'oai_dc'}

    def test_exclusive(self):
        args = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'oai_dc',
            'resumptionToken': 'fake token'}

        self.assertRaises(ParameterError, validate_oai_parameters, args)

    # live test each of the 6 OAI verb functions
    def test_GetRecordDc(self):
        # dynamic
        data = {
            'verb': 'GetRecord',
            'identifier': 'AU240',
            'metadataPrefix': 'oai_dc'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifier = dynamic_record.xpath(
            '//oai:identifier',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_GetRecord_240_dc.xml'))
        static_identifier = static_record.xpath(
            '//oai:identifier',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        assert dynamic_identifier == static_identifier

    def test_GetRecordIgsn(self):
        # dynamic
        data = {
            'verb': 'GetRecord',
            'identifier': 'AU240',
            'metadataPrefix': 'igsn'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifier = dynamic_record.xpath(
            '//cs:resourceIdentifier',
            namespaces={'cs': 'https://igsn.csiro.au/schemas/3.0'}
        )[0].text

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_GetRecord_240_igsn.xml'))
        static_identifier = static_record.xpath(
            '//cs:resourceIdentifier',
            namespaces={'cs': 'https://igsn.csiro.au/schemas/3.0'}
        )[0].text

        assert dynamic_identifier == static_identifier

    def test_Identify(self):
        # dynamic
        data = {
            'verb': 'Identify'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifier = dynamic_record.xpath(
            '//oai:repositoryName',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_Identify.xml'))
        static_identifier = static_record.xpath(
            '//oai:repositoryName',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        assert dynamic_identifier == static_identifier

    def test_ListIdentifiers(self):
        # dynamic
        data = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'oai_dc'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifiers = dynamic_record.xpath(
            '//oai:identifier/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_ListIdentifiers.xml'))
        static_identifiers = static_record.xpath(
            '//oai:identifier/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        assert dynamic_identifiers == static_identifiers

    def test_ListMetadataFormats(self):
        # dynamic
        data = {
            'verb': 'ListMetadataFormats',
            'identifier': 'AU240'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifiers = dynamic_record.xpath(
            '//oai:metadataPrefix/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_ListMetadataFormats.xml'))
        static_identifiers = static_record.xpath(
            '//oai:metadataPrefix/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        assert dynamic_identifiers == static_identifiers

    def test_ListRecords(self):
        # dynamic
        data = {
            'verb': 'ListRecords',
            'metadataPrefix': 'oai_dc'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifiers = dynamic_record.xpath(
            '//oai:identifier/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_ListRecords.xml'))
        static_identifiers = static_record.xpath(
            '//oai:identifier/text()',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )

        assert dynamic_identifiers == static_identifiers

    def test_ListSets(self):
        # dynamic
        data = {
            'verb': 'ListSets'
        }
        r = requests.get(self.uri, params=data)
        dynamic_record = etree.parse(StringIO(r.content))
        dynamic_identifier = dynamic_record.xpath(
            '//oai:setName',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_ListSets.xml'))

        static_identifier = static_record.xpath(
            '//oai:setName',
            namespaces={'oai': 'http://www.openarchives.org/OAI/2.0/'}
        )[0].text

        assert dynamic_identifier == static_identifier

if __name__ == '__main__':
    unittest.main()
