from renderer import Renderer
from flask import Response, render_template
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal
from ldapi import LDAPI
from lxml import etree
import requests
from StringIO import StringIO
import config


class RegisterRenderer(Renderer):
    def __init__(self, request, uri, endpoints, page, per_page, last_page_no):
        Renderer.__init__(self, uri, endpoints)

        self.request = request
        self.uri = uri
        self.register = []
        self.g = None
        self.per_page = per_page
        self.page = page
        self.last_page_no = last_page_no

        self._get_details_from_oracle_api(page, per_page)

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

    def _get_details_from_oracle_api(self, page, per_page):
        """
        Populates this instance with data from the Oracle Samples table API

        :param page: the page number of the total resultset from the Samples Set API
        :return: None
        """
        #os.environ['NO_PROXY'] = 'ga.gov.au'
        r = requests.get(config.XML_API_URL_SAMPLESET.format(page, per_page), timeout=3)
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

            register_uri_str = self.request.base_url
            if self.per_page is not None:
                register_uri_str += '?per_page=' + str(self.per_page)
            else:
                register_uri_str += '?per_page=100'
            register_uri_str_no_page_no = register_uri_str + '&page='
            if self.page is not None:
                register_uri_str += '&page=' + str(self.page)
            else:
                register_uri_str += '&page=1'
            register_uri = URIRef(register_uri_str)

            self.g.add((register_uri, RDF.type, REG.FederatedRegister))
            self.g.add((register_uri, RDFS.label, Literal('Samples Register', datatype=XSD.string)))

            # pagination
            self.g.add((register_uri, REG.firstRegisterPage, URIRef(register_uri_str_no_page_no + '1')))
            self.g.add((register_uri, REG.lastRegisterPage, URIRef(register_uri_str_no_page_no + str(self.last_page_no))))

            if self.page != 1:
                self.g.add((register_uri, REG.prevRegisterPage, URIRef(register_uri_str_no_page_no + str(self.page - 1))))

            if self.page != self.last_page_no:
                self.g.add((register_uri, REG.nextRegisterPage, URIRef(register_uri_str_no_page_no + str(self.page + 1))))

            # add all the items
            for item in self.register:
                item_uri = URIRef(self.request.base_url + item)
                self.g.add((item_uri, RDF.type, URIRef(self.uri)))
                self.g.add((item_uri, RDFS.label, Literal('Sample igsn:' + item, datatype=XSD.string)))
                self.g.add((item_uri, REG.register, register_uri))
