import unittest
from renderers import Sample


# global Sample for testing
s = None


class TestSample(unittest.TestCase):
    """
    Tests for the Sample class
    """

    @classmethod
    def setUpClass(cls):
        global s
        s = Sample()

    def test_populate_from_xml_file(self):
        """
        Tests loading the Sample class instance
        """
        # load
        s.populate_from_xml_file('sample_eg1.xml')

        # compare instance variables
        assert s.igsn == 'AU2648696', 'IGSN instance varable not correct'
        assert s.entity_uri == 'http://pid.geoscience.gov.au/site/15846', 'entity_uri instance variable not correct'
        assert s.lith == 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment', \
            'lith instance variable not correct, expecting "http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment", got ' + s.lith

    def run_all_tests(self):
        self.test_populate_from_xml_file()


# Define test suites
def test_suite():
    """
    Returns a test suite of all the tests in this module.
    """

    test_classes = [TestSample]

    suite_list = map(unittest.defaultTestLoader.loadTestsFromTestCase,
                     test_classes)

    suite = unittest.TestSuite(suite_list)

    return suite


# Define main function
def main():
    unittest.TextTestRunner(verbosity=2).run(test_suite())


if __name__ == '__main__':
    main()



