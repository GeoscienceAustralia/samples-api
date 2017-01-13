import os
from StringIO import StringIO

import requests
from lxml import etree
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal

from ldapi import LDAPI


class SampleRegister:
    """
    This class represents a Sample as listed in the Samples register.
    """

    URI_GA = URIRef('http://pid.geoscience.gov.au/org/ga')
    URI_DS_REG = URIRef('http://pid.geoscience.gov.au/dataset/')

    def __init__(self):
        self.samples = []

    def validate_xml(self, xml):

        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print 'not valid xml'
            return False

    def populate_from_oracle_api(self, xml_api_url, page_no):
        """
        Populates this instance with data from the Oracle Samples table API

        :param page_no: the page number of the total resultset from the Samples Set API
        :return: None
        """
        #os.environ['NO_PROXY'] = 'ga.gov.au'
        print xml_api_url.format(page_no)
        r = requests.get(xml_api_url.format(page_no))
        xml = r.content

        if self.validate_xml(xml):
            self.populate_from_xml_file(StringIO(xml))
            return True
        else:
            return False

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
        return '"' + '", "'.join(self.samples) + '"'

    def export_as_rdf(self, model_view='default', rdf_mime='text/turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view: string of one of the model view names available for SampleRegister objects ['reg', 'dc', '',
            'default']
        :param rdf_mime: string of one of the rdflib serlialization format ['n3', 'nquads', 'nt', 'pretty-xml', 'trig',
            'trix', 'turtle', 'xml'], from http://rdflib3.readthedocs.io/en/latest/plugin_serializers.html
        :return: RDF string
        """

        # things that are applicable to all model views; the graph and some namespaces
        g = Graph()
        # DC = Namespace('http://purl.org/dc/elements/1.1/')
        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)

        AUROLE = Namespace('http://communications.data.gov.au/def/role/')
        g.bind('aurole', AUROLE)
        PROV = Namespace('http://www.w3.org/ns/prov#')
        g.bind('prov', PROV)

        # URI for this register of Samples
        this_register = 'http://pid.geoscience.gov.au/model/'
        this_register_uri = URIRef(this_register)
        igsn_base_uri = this_register

        # select model view
        if model_view == 'default' or model_view == 'dpr' or model_view is None:
            # default model is the reg model
            # reg model required namespaces
            REG = Namespace('http://purl.org/linked-data/registry#')
            g.bind('reg', REG)

            DPR = Namespace('http://promsns.org/def/dpr#')
            g.bind('dpr', DPR)

            IGSN = Namespace('http://pid.geoscience.gov.au/def/ont/igsn#')
            g.bind('igsn', IGSN)

            ORG = Namespace('http://www.w3.org/ns/org#')
            g.bind('org', ORG)

            DCAT = Namespace('https://www.w3.org/ns/dcat#')
            g.bind('dcat', DCAT)

            # classing the register
            g.add((URIRef(this_register), RDF.type, REG.Register))

            # metadata for the Register
            g.add((SampleRegister.URI_GA, RDF.type, DPR.DataProviderRegister))
            g.add((SampleRegister.URI_GA, RDF.type, ORG.Organization))
            g.add((SampleRegister.URI_GA, RDFS.label, Literal('Geoscience Australia', datatype=XSD.string)))
            g.add((
                SampleRegister.URI_GA,
                RDFS.comment,
                Literal('Geoscience Australia (GA) is Austriala\'s national custodian of geoscience information. As a '
                        'Data Provider Register, GA publishes much information including samples\' metadata, datasets, '
                        'web services, vocabularies and ontologies', datatype=XSD.string)))
            g.add((SampleRegister.URI_GA, REG.subregister, SampleRegister.URI_DS_REG))

            g.add((SampleRegister.URI_DS_REG, RDF.type, REG.FederatedRegister))
            g.add((SampleRegister.URI_DS_REG, RDFS.label, Literal('GA\'s Dataset register', datatype=XSD.string)))
            g.add((SampleRegister.URI_DS_REG, REG.containedItemClass, DCAT.Dataset))
            g.add((SampleRegister.URI_DS_REG, REG.subregister, this_register_uri))

            g.add((this_register_uri, RDF.type, REG.Register))
            g.add((this_register_uri, RDFS.label, Literal('GA\'s Samples register', datatype=XSD.string)))
            g.add((this_register_uri, REG.containedItemClass, IGSN.Sample))

            # for each Sample
            for sample_igsn_str in self.samples:
                g.add((URIRef(igsn_base_uri + sample_igsn_str), RDF.type, IGSN.Sample))
                g.add((URIRef(igsn_base_uri + sample_igsn_str), RDFS.label, Literal(
                    'Sample ' + sample_igsn_str,
                    datatype=XSD.string)))
                g.add((URIRef(igsn_base_uri + sample_igsn_str), REG.register, URIRef(this_register)))

        elif model_view == 'dc':
            pass
        elif model_view == 'prov':
            pass

        return g.serialize(format=LDAPI.get_file_extension(rdf_mime))

    def export_as_html(self, model_view='default'):
        """
        Exports this instance in HTML, according to a given model from the list of supported models.

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
            'default']
        :return: HTML string
        """
        html = '<style>' + \
               '   table.data {' + \
               '       border-collapse: collapse;' + \
               '       border: solid 2px black;' + \
               '   }' + \
               '   table.data td, table.data th {' + \
               '       border: solid 1px black;' + \
               '       padding: 5px;' + \
               '   }' + \
               '</style>'

        # the register itself
        html += '<h2>This Register of Samples</h2>'
        html += '<table class="data">'
        html += '   <tr><th>Property</th><th>Value</th></tr>'
        html += '   <tr><td>Type</td><td>reg:FederatedRegister</td></tr>'
        html += '   <tr><td>reg:containedItemClass</td><td>igsn:Sample</td></tr>'
        html += '   <tr><td>parent</td><td><a href="http://pid.geoscience.gov.au/dataset/">' \
                'GA\'s Dataset Register</a></td></tr>'
        html += '</table>'

        # samples
        html += '<h2>Samples</h2>'
        html += '<ul>'
        for sample_uri in self.samples:
            html += '   <li><a href="' + sample_uri + '">' + sample_uri + '</a></li>'
        html += '</ul>'

        return html

    def export_ListRecords(self, model_view='default'):
            if model_view == 'default' or model_view == 'oai_dc' or model_view is None:
                # export dc xml compliant with OAI-PMH
                root = etree.XML('''\
                <?xml version="1.0" encoding="UTF-8" ?>
                <?xml-stylesheet type="text/xsl" href="xsl/oaitohtml.xsl"?>
                <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
                    <responseDate>2016-12-21T08:04:45Z</responseDate>
                    <request verb="ListRecords" from="2011-06-01T00:00:00Z" metadataPrefix="oai_dc">
                        http://doidb.wdc-terra.org/igsnoaip/oai</request>
                    <ListRecords>
                ''')

            elif model_view == 'dc':
                pass
            elif model_view == 'prov':
                pass


if __name__ == '__main__':
    sr = SampleRegister()
    # sr.populate_from_xml_file('../test/samples_register_eg1.xml')
    import settings
    sr.populate_from_oracle_api(settings.XML_API_URL, 1)
    # print sr.export_as_text()
    # print sr.export_as_html()
    print sr.export_as_rdf(model_view='dpr', rdf_mime='text/turtle')

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()
