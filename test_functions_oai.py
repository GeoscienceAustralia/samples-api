__author__ = 'u65838'

import unittest
from functions_oai import valid_oai_args, validate_oai_parameters

class TestFunctionsOAI(unittest.TestCase):
    def test_true(self):
        args = {
        'verb':'GetRecord',
        'identifier':'AU100',
        'metadataPrefix':'oai_dc'}

        self.assertTrue(valid_oai_args(args['verb']))
        self.assertTrue(validate_oai_parameters(args))

    def test_Error(self):
        args = {
        'verb':'GetRec',
        'identifier':'AU100',
        'metadataPrefix':'oai_dc'}

        self.assertTrue(valid_oai_args(args['verb']))
        self.assertTrue(validate_oai_parameters(args))

    def test_missing_required(self):
        args = {
        'verb':'GetRecord',
        'metadataPrefix':'oai_dc'}

    def test_exclusive(self):
        args = {
        'verb':'ListIdentifiers',
        'resumptionToken':'AU100',
        'metadataPrefix':'oai_dc'}

        self.assertTrue(valid_oai_args(args['verb']))
        self.assertTrue(validate_oai_parameters(args))

        self.assertTrue(valid_oai_args(args['verb']))
        self.assertTrue(validate_oai_parameters(args))

if __name__ == '__main__':
    unittest.main()
