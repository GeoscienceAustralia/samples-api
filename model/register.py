from renderer import Renderer
from flask import Response, render_template
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal
from ldapi import LDAPI
from lxml import etree
import requests
from StringIO import StringIO
import settings


class RegisterRenderer(Renderer):
    def __init__(self, request, uri, endpoints, page_no, no_per_page):
        Renderer.__init__(self, uri, endpoints)

        self.request = request
        self.uri = uri
        self.register = []
        self.g = None

        self._get_details_from_oracle_api(page_no, no_per_page)

    def render(self, view, mimetype, extra_headers=None):
        if view == 'reg':
            # is an RDF format requested?
            if mimetype in LDAPI.get_rdf_mimetypes_list():
                # it is an RDF format so make the graph for serialization
                self._make_reg_graph(view)
                rdflib_format = LDAPI.get_rdf_parser_for_mimetype(mimetype)
                return Response(
                    self.g.serialize(format=rdflib_format),
                    status=200,
                    mimetype=mimetype,
                    headers=extra_headers
                )
            elif mimetype == 'text/html':
                return Response(
                    render_template(
                        'class_register.html',
                        class_name=self.uri,
                        register=self.register,
                        system_url='http://54.66.133.7'
                    ),
                    mimetype='text/html',
                    headers=extra_headers
                )
        else:
            return Response('The requested model model is not valid for this class', status=400, mimetype='text/plain')

    def _get_details_from_file(self, xml):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Samples DB
        :return: None
        """
        for event, elem in etree.iterparse(xml):
            if elem.tag == "IGSN":
                self.register.append(elem.text)

    def validate_xml(self, xml):
        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print 'not valid xml'
            return False

    def _get_details_from_oracle_api(self, page_no, no_per_page):
        """
        Populates this instance with data from the Oracle Samples table API

        :param page_no: the page number of the total resultset from the Samples Set API
        :return: None
        """
        #os.environ['NO_PROXY'] = 'ga.gov.au'
        r = requests.get(settings.XML_API_URL_SAMPLESET.format(page_no, no_per_page), timeout=3)
        xml = r.content

        if self.validate_xml(xml):
            self._get_details_from_file(StringIO(xml))
            return True
        else:
            return False

    def _make_reg_graph(self, model_view):
        self.g = Graph()

        if model_view == 'reg':  # reg is default
            # make the static part of the graph
            REG = Namespace('http://purl.org/linked-data/registry#')
            self.g.bind('reg', REG)

            self.g.add((URIRef(self.request.url.split('?')[0]), RDF.type, REG.Register))

            # add all the items
            for item in self.register:
                self.g.add((URIRef(self.request.base_url + item), RDF.type, URIRef(self.uri)))
                self.g.add((URIRef(self.request.base_url + item), RDFS.label, Literal(item, datatype=XSD.string)))
                self.g.add((URIRef(self.request.base_url + item), REG.register, URIRef(self.request.base_url)))
