from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode
from StringIO import StringIO
from lxml.builder import ElementMaker
import os
import requests
from datetime import datetime


class SampleRegister:
    """
    This class represents a Sample as listed in the Samples register.
    """
    def __init__(self):
        self.samples = []

    def populate_from_xml_file(self, xml):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Samples DB
        :return: None
        """
        for event, elem in etree.iterparse(xml):
            if elem.tag == "IGSN":
                self.samples.append(elem.text)

    def export_as_text(self):
        return self.samples

if __name__ == '__main__':
    sr = SampleRegister()
    sr.populate_from_xml_file('../test/samples_register_eg1.xml')
    print sr.export_as_text()
    # print s.export_as_rdf(model_view='igsn', rdf_mime='text/turtle')

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()
