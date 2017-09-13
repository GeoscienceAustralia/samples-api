import unittest
import requests
from lxml import etree
from io import StringIO
from controller.oai_functions import *
from controller.oai_errors import *
import os


class TestFunctionsOAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.uri = 'http://localhost:5000/oai'
        cls.dir = os.path.dirname(os.path.realpath(__file__))

    def test_true(self):
        test_args = {
            'verb': 'GetRecord',
            'identifier': 'AU100',
            'metadataPrefix': 'oai_dc'}

        self.assertTrue(validate_oai_parameters(test_args))
        self.assertTrue(validate_oai_parameters(test_args))

    def test_verb_error(self):
        test_args = {
            'verb': 'GetRec',
            'identifier': 'AU100',
            'metadataPrefix': 'oai_dc'}

        self.assertRaises(BadVerbError, validate_oai_parameters, test_args)

    def test_missing_required(self):
        test_args = {
            'verb': 'GetRecord',
            'metadataPrefix': 'oai_dc'}
        # missing record identifier

        self.assertRaises(BadArgumentError, validate_oai_parameters, test_args)

    def test_exclusive(self):
        test_args = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'oai_dc',
            'resumptionToken': 'fake_token'}

        self.assertRaises(BadArgumentError, validate_oai_parameters, test_args)

    # live test each of the 6 OAI verb functions
    def test_GetRecordDc(self):
        # dynamic
        test_args = {
            'verb': 'GetRecord',
            'identifier': 'AU240',
            'metadataPrefix': 'oai_dc'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
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
        test_args = {
            'verb': 'GetRecord',
            'identifier': 'AU240',
            'metadataPrefix': 'igsn'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
        dynamic_identifier = dynamic_record.xpath(
            '//igsn:alternateIdentifier',
            namespaces={'igsn': 'http://schema.igsn.org/description/1.0'}
        )[0].text

        # static
        static_record = etree.parse(os.path.join(self.dir, 'static_data', 'static_GetRecord_240_igsn.xml'))
        static_identifier = static_record.xpath(
            '//igsn:alternateIdentifier',
            namespaces={'igsn': 'http://schema.igsn.org/description/1.0'}
        )[0].text

        assert dynamic_identifier == static_identifier

    def test_Identify(self):
        # dynamic
        test_args = {
            'verb': 'Identify'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
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
        test_args = {
            'verb': 'ListIdentifiers',
            'metadataPrefix': 'oai_dc'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
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
        test_args = {
            'verb': 'ListMetadataFormats',
            'identifier': 'AU240'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
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
        dynamic_record = etree.parse(BytesIO(r.content))
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
        test_args = {
            'verb': 'ListSets'
        }
        r = requests.get(self.uri, params=test_args)
        dynamic_record = etree.parse(BytesIO(r.content))
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
