import unittest

from routes.oai_functions import valid_oai_args, validate_oai_parameters, ParameterError


class TestFunctionsOAI(unittest.TestCase):
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

        self.assertRaises(ParameterError, valid_oai_args, args['verb'])
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

if __name__ == '__main__':
    unittest.main()
