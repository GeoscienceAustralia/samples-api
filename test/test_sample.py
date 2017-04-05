import unittest
from model import Sample


class TestSample(unittest.TestCase):
    """
    Tests for the Sample class
    """

    def test_populate_from_xml_file(self):
        """
        Tests loading the Sample class instance
        """
        # load
        s = Sample(None, None, 'sample_eg1.xml')

        # compare instance variables
        assert s.igsn == 'AU2648696', 'IGSN instance varable not correct'
        assert s.entity_uri == 'http://pid.geoscience.gov.au/site/15846', 'entity_uri instance variable not correct'
        assert s.lith == 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment', \
            'lith instance variable not correct, expecting "http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment", got ' + s.lith

    def test_populate_from_api(self):
        """
        Tests loading the Sample class instance
        """
        # load
        s = Sample("http://localhost:8080/oai", 'AU100', None)

        # compare instance variables
        assert s.igsn == 'AU100', 'IGSN instance variable not correct'

    # def run_all_tests(self):
    #     self.test_populate_from_xml_file()
