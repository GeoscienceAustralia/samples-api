from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode
from StringIO import StringIO
import requests
from model.datestamp import datetime_to_datestamp
from datetime import datetime
from ldapi import LDAPI
from flask import Response, render_template
from lookups import TERM_LOOKUP


class Sample:
    """
    This class represents a Sample and methods in this class allow a sample to be loaded from GA's internal Oracle
    Samples database and to be exported in a number of formats including RDF, according to the 'IGSN Ontology' and an
    expression of the Dublin Core ontology, HTML, XML in the form given by the GA Oracle DB's API and also XML according
    to CSIRO's IGSN schema (v2).
    """

    """
    Associates terms in the database with terms in the IGSN codelist vocabulary:
    http://pid.geoscience.gov.au/def/voc/igsn-codelists

    One of:
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/accessType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/all-concepts
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/collectionType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/contributorType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/featureType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/geometryType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/identifierType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/materialType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/methodType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/relationType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/resourceType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/sampleType
        http://pid.geoscience.gov.au/def/voc/igsn-codelists/sridType
    """

    URI_MISSSING = 'http://www.opengis.net/def/nil/OGC/0/missing'
    URI_INAPPLICABLE = 'http://www.opengis.net/def/nil/OGC/0/inapplicable'
    URI_GA = 'http://pid.geoscience.gov.au/org/ga'

    def __init__(self, oracle_api_samples_url, igsn, xml=None):
        self.oracle_api_samples_url = oracle_api_samples_url
        self.igsn = igsn
        self.sampleid = None
        self.sample_type = None
        self.method_type = None
        self.material_type = None
        self.long_min = None
        self.long_max = None
        self.lat_min = None
        self.lat_max = None
        self.gtype = None
        self.srid = None
        self.x = None
        self.y = None
        self.z = None
        self.elem_info = None
        self.ordinates = None
        self.state = None
        self.country = None
        self.depth_top = None
        self.depth_base = None
        self.strath = None
        self.age = None
        self.remark = None
        self.lith = None
        self.date_acquired = None
        self.entity_uri = None
        self.entity_name = None
        self.entity_type = None
        self.hole_long_min = None
        self.hole_long_max = None
        self.hole_lat_min = None
        self.hole_lat_max = None
        self.date_load = None
        self.date_modified = None
        self.sample_no = None

        # populate all instance variables from API
        # TODO: lazy load this, i.e. only populate if a view that need populating is loaded which is every view except for Alternates

        if oracle_api_samples_url is None:
            self._populate_from_xml_file(xml)
        else:
            self._populate_from_oracle_api()

    def render(self, view, mimetype):
        if mimetype in LDAPI.get_rdf_mimetypes_list():
            return Response(self.export_as_rdf(view, mimetype), mimetype=mimetype)

        if view == 'igsn':
            # RDF formats handled by general case
            # HTML is the only other enabled format for igsn view
            return self.export_as_html(model_view=view)
        elif view == 'dc':
            # RDF formats handled by general case
            if mimetype == 'application/xml':
                return self.export_dc_xml()
            else:
                return self.export_as_html(model_view=view)
        elif view == 'prov':
            # RDF formats handled by general case
            # only RDF for this view so set the mimetype to our favourite mime format
            mimetype = 'text/turtle'
            return Response(self.export_as_rdf('prov', mimetype), mimetype=mimetype)
        elif view == 'csirov3':
            # only XML for this view
            return Response(
                self.export_as_csirov3_xml(),
                status=200,
                mimetype='application/xml',
                # headers={'Content-Disposition': 'attachment; filename=' + igsn + '.xml'}
            )

    def validate_xml(self, xml):
        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print 'not valid xml'
            return False

    def _populate_from_oracle_api(self):
        """
        Populates this instance with data from the Oracle Samples table API

        :param oracle_api_samples_url: the Oracle XML API URL string for a single sample
        :param igsn: the IGSN of the sample desired
        :return: None
        """
        # internal URI
        # os.environ['NO_PROXY'] = 'ga.gov.au'
        # call API
        r = requests.get(self.oracle_api_samples_url.format(self.igsn))
        # deal with missing XML declaration
        if "No data" in r.content:
            raise ParameterError('No Data')
        if not r.content.startswith('<?xml version="1.0" ?>'):
            xml = '<?xml version="1.0" ?>\n' + r.content
        else:
            xml = r.content
        if self.validate_xml(xml):
            self._populate_from_xml_file(StringIO(xml))
            return True
        else:
            return False

    def _populate_from_xml_file(self, xml):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Samples DB
        :return: None
        """
        # iterate through the elements in the XML element tree and handle each
        for event, elem in etree.iterparse(xml):
            '''
            <ROWSET>
             <ROW>
              <IGSN>AU2648696</IGSN>
              <SAMPLEID>1905_50252</SAMPLEID>
              <SAMPLE_TYPE_NEW/>
              <SAMPLING_METHOD/>
              <MATERIAL_CLASS/>
              <SAMPLE_MIN_LONGITUDE/>
              <SAMPLE_MAX_LONGITUDE/>
              <SAMPLE_MIN_LATITUDE/>
              <SAMPLE_MAX_LATITUDE/>
              <GEOM>
               <SDO_GTYPE>3001</SDO_GTYPE>
               <SDO_SRID>8311</SDO_SRID>
               <SDO_POINT>
                <X>143.43508333</X>
                <Y>-26.94486389</Y>
                <Z>219.453</Z>
               </SDO_POINT>
               <SDO_ELEM_INFO/>
               <SDO_ORDINATES/>
              </GEOM>
              <STATEID>QLD</STATEID>
              <COUNTRY>AUS</COUNTRY>
              <TOP_DEPTH>843</TOP_DEPTH>
              <BASE_DEPTH>868</BASE_DEPTH>
              <STRATNAME/>
              <AGE/>
              <REMARK/>
              <LITHNAME/>
              <ACQUIREDATE/>
              <ENTITY_TYPE>BOREHOLE</ENTITY_TYPE>
              <ENTITYID>TALGEBERRY 4</ENTITYID>
              <HOLE_MIN_LONGITUDE>143.43508333</HOLE_MIN_LONGITUDE>
              <HOLE_MAX_LONGITUDE/>
              <HOLE_MIN_LATITUDE>-26.94486389</HOLE_MIN_LATITUDE>
              <HOLE_MAX_LATITUDE/>
              <LOADEDDATE>10-NOV-16</LOADEDDATE>
              <SAMPLENO>2648696</SAMPLENO>
              <ENO>15846</ENO>
             </ROW>
            </ROWSET>
            '''
            if elem.tag == "IGSN":
                self.igsn = elem.text
            elif elem.tag == "SAMPLEID":
                self.sampleid = elem.text
            elif elem.tag == "SAMPLE_TYPE_NEW":
                if elem.text is not None:
                    self.sample_type = TERM_LOOKUP['sample_type'].get(elem.text)
                    if self.sample_type is None:
                        self.sample_type = Sample.URI_MISSSING
            elif elem.tag == "SAMPLING_METHOD":
                if elem.text is not None:
                    self.method_type = TERM_LOOKUP['method_type'].get(elem.text)
                    if self.method_type is None:
                        self.method_type = Sample.URI_MISSSING
            elif elem.tag == "MATERIAL_CLASS":
                if elem.text is not None:
                    self.material_type = TERM_LOOKUP['material_type'].get(elem.text)
                    if self.material_type is None:
                        self.material_type = Sample.URI_MISSSING
            elif elem.tag == "SAMPLE_MIN_LONGITUDE":
                if elem.text is not None:
                    self.long_min = elem.text
            elif elem.tag == "SAMPLE_MAX_LONGITUDE":
                if elem.text is not None:
                    self.long_max = elem.text
            elif elem.tag == "SAMPLE_MIN_LATITUDE":
                if elem.text is not None:
                    self.lat_min = elem.text
            elif elem.tag == "SAMPLE_MAX_LATITUDE":
                if elem.text is not None:
                    self.lat_max = elem.text
            elif elem.tag == "SDO_GTYPE":
                if elem.text is not None:
                    self.gtype = elem.text
            elif elem.tag == "SDO_SRID":
                if elem.text is not None:
                    self.srid = elem.text
            elif elem.tag == "X":
                if elem.text is not None:
                    self.x = elem.text
            elif elem.tag == "Y":
                if elem.text is not None:
                    self.y = elem.text
            elif elem.tag == "Z":
                if elem.text is not None:
                    self.z = elem.text
            elif elem.tag == "SDO_ELEM_INFO":
                if elem.text is not None:
                    self.elem_info = elem.text
            elif elem.tag == "SDO_ORDINATES":
                if elem.text is not None:
                    self.ordinates = elem.text
            elif elem.tag == "STATEID":
                if elem.text is not None:
                    self.state = TERM_LOOKUP['state'].get(elem.text)
                    if self.state is None:
                        self.state = Sample.URI_MISSSING
            elif elem.tag == "COUNTRY":
                if elem.text is not None:
                    self.country = TERM_LOOKUP['country'].get(elem.text)
                    if self.country is None:
                        self.country = Sample.URI_MISSSING
            elif elem.tag == "TOP_DEPTH":
                if elem.text is not None:
                    self.depth_top = elem.text
            elif elem.tag == "BASE_DEPTH":
                if elem.text is not None:
                    self.depth_base = elem.text
            elif elem.tag == "STRATNAME":
                if elem.text is not None:
                    self.strath = elem.text
            elif elem.tag == "AGE":
                if elem.text is not None:
                    self.age = elem.text
            elif elem.tag == "REMARK":
                if elem.text:
                    self.remark = elem.text
            elif elem.tag == "LITHNAME":
                if elem.text is not None:
                    self.lith = TERM_LOOKUP['lith'].get(elem.text)
                    if self.lith is None:
                        self.lith = Sample.URI_MISSSING
            elif elem.tag == "ACQUIREDATE":
                if elem.text is not None:
                    self.date_acquired = datetime.strptime(elem.text, '%Y-%m-%d %H:%M:%S')
            elif elem.tag == "ENO":
                if elem.text is not None:
                    self.entity_uri = 'http://pid.geoscience.gov.au/site/' + elem.text
            elif elem.tag == "ENTITYID":
                if elem.text is not None:
                    self.entity_name = elem.text
            elif elem.tag == "ENTITY_TYPE":
                if elem.text is not None:
                    self.entity_type = elem.text
            elif elem.tag == "HOLE_MIN_LONGITUDE":
                if elem.text is not None:
                    self.hole_long_min = elem.text
            elif elem.tag == "HOLE_MAX_LONGITUDE":
                if elem.text is not None:
                    self.hole_long_max = elem.text
            elif elem.tag == "HOLE_MIN_LATITUDE":
                if elem.text is not None:
                    self.hole_lat_min = elem.text
            elif elem.tag == "HOLE_MAX_LATITUDE":
                if elem.text is not None:
                    self.hole_lat_max = elem.text
            elif elem.tag == "LOADEDDATE":
                if elem.text is not None:
                    self.date_load = datetime.strptime(elem.text, '%Y-%m-%d %H:%M:%S')
            elif elem.tag == "MODIFIED_DATE":
                if elem.text is not None:
                    self.date_modified = datetime.strptime(elem.text, '%Y-%m-%d %H:%M:%S')
            elif elem.tag == "SAMPLENO":
                if elem.text is not None:
                    self.sample_no = elem.text

        return True

    def _generate_sample_wkt(self):
        if self.z is not None:
            # wkt = "SRID=" + self.srid + ";POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            wkt = "<https://epsg.io/" + self.srid + "> " \
                  "POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
        else:
            # wkt = "SRID=" + self.srid + ";POINT(" + self.x + " " + self.y + ")"
            if self.srid is not None and self.x is not None and self.y is not None:
                wkt = "<https://epsg.io/" + self.srid + "> POINT(" + self.x + " " + self.y + ")"
            else:
                wkt = ''

        return wkt

    def _generate_sample_wkt_csirov3_xml(self):
        if self.z is not None:
            # wkt = "SRID=" + self.srid + ";POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            wkt = "POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
        else:
            # wkt = "SRID=" + self.srid + ";POINT(" + self.x + " " + self.y + ")"
            if self.srid is not None and self.x is not None and self.y is not None:
                wkt = "POINT(" + self.x + " " + self.y + ")"
            else:
                wkt = ''

        return wkt

    def _generate_sample_gml(self):
        if self.z is not None:
            gml = '<gml:Point srsDimension="3" srsName="https://epsg.io/' + self.srid + '">' \
                  '<gml:pos>' + self.x + ' ' + self.y + ' ' + self.z + '</gml:pos>' \
                  '</gml:Point>'
        else:
            if self.srid is not None and self.x is not None and self.y is not None:
                gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/' + self.srid + '">' \
                      '<gml:pos>' + self.x + ' ' + self.y + '</gml:pos>' \
                      '</gml:Point>'
            else:
                gml = ''

        return gml

    def _generate_parent_wkt(self):
        # TODO: add support for geometries other than Point
        if self.srid is not None and self.x is not None and self.y is not None:
            wkt = "<https://epsg.io/" + self.srid + ">POINT(" + self.hole_long_min + " " + self.hole_lat_min + ")"
        else:
            wkt = ''

        return wkt

    def _generate_parent_gml(self):
        # TODO: add support for geometries other than Point
        if self.srid is not None and self.x is not None and self.y is not None:
            gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/' + \
                  self.srid + '"><gml:pos>' + self.hole_long_min + ' ' + self.hole_lat_min + '</gml:pos>' \
                  '</gml:Point>'
        else:
            gml = ''

        return gml

    def export_as_rdf(self, model_view='default', rdf_mime='text/turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
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

        SAMFL = Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
        g.bind('samfl', SAMFL)

        GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geosp', GEOSP)

        AUROLE = Namespace('http://communications.data.gov.au/def/role/')
        g.bind('aurole', AUROLE)

        PROV = Namespace('http://www.w3.org/ns/prov#')
        g.bind('prov', PROV)

        # URI for this sample
        base_uri = 'http://pid.geoscience.gov.au/sample/'
        this_sample = URIRef(base_uri + self.igsn)

        # define GA
        ga = URIRef(Sample.URI_GA)

        # sample location in GML & WKT, formulation from GeoSPARQL
        wkt = Literal(self._generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self._generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        # select model view
        if model_view == 'igsn':
            # default model is the IGSN model
            # IGSN model required namespaces
            IGSN = Namespace('http://pid.geoscience.gov.au/def/ont/igsn#')
            g.bind('igsn', IGSN)

            # classing the sample
            g.add((this_sample, RDF.type, SAMFL.Specimen))

            # AlternateIdentifier
            alternate_identifier = BNode()
            g.add((this_sample, DCT.identifier, alternate_identifier))
            g.add((alternate_identifier, RDF.type, URIRef('http://pid.geoscience.gov.au/def/voc/igsn-codelists/IGSN')))
            g.add((alternate_identifier, PROV.value, Literal(self.igsn, datatype=XSD.string)))

            # Geometry
            geometry = BNode()
            g.add((this_sample, SAMFL.samplingLocation, geometry))
            g.add((geometry, RDF.type, SAMFL.Point))
            g.add((geometry, GEOSP.asGML, gml))
            g.add((geometry, GEOSP.asWKT, wkt))

            # Elevation
            elevation = BNode()
            g.add((this_sample, SAMFL.samplingElevation, elevation))
            g.add((elevation, RDF.type, SAMFL.Elevation))
            g.add((elevation, SAMFL.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((elevation, SAMFL.verticalDatum, Literal(
                'http://spatialreference.org/ref/epsg/4283/',
                datatype=XSD.anyUri)))

            # properties
            g.add((this_sample, SAMFL.currentLocation, Literal('GA Services building', datatype=XSD.string)))
            if self.material_type is not None:
                g.add((this_sample, SAMFL.materialClass, URIRef(self.material_type)))
            if self.method_type is not None:
                g.add((this_sample, SAMFL.samplingMethod, URIRef(self.method_type)))
            if self.date_acquired is not None:
                g.add((this_sample, SAMFL.samplingTime, Literal(self.date_acquired.isoformat(), datatype=XSD.datetime)))
            # TODO: represent Public/Private (and other?) access methods in DB, add to terms in vocab?
            g.add((this_sample, DCT.accessRights, URIRef(TERM_LOOKUP['access']['Public'])))
            # TODO: make a register of Entities
            if self.entity_uri is not None:
                this_parent = URIRef(self.entity_uri)
            else:
                # TODO: get a real parent URL
                this_parent = URIRef('http://fake.com')

            g.add((this_sample, SAMFL.relatedSamplingFeature, this_parent))  # could be OM.featureOfInterest

            # parent
            if self.entity_type is not None:
                g.add((this_parent, RDF.type, URIRef(TERM_LOOKUP['entity_type'][self.entity_type])))
            else:
                g.add((
                    this_parent,
                    RDF.type,
                    URIRef('http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole')
                ))

            parent_geometry = BNode()
            g.add((this_parent, GEOSP.hasGeometry, parent_geometry))
            g.add((parent_geometry, RDF.type, SAMFL.Point))  # TODO: extend this for other geometry types
            g.add((parent_geometry, GEOSP.asWKT, Literal(self._generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
            g.add((parent_geometry, GEOSP.asGML, Literal(self._generate_parent_gml(), datatype=GEOSP.wktLiteral)))

            parent_elevation = BNode()
            g.add((this_parent, SAMFL.samplingElevation, parent_elevation))
            g.add((parent_elevation, RDF.type, SAMFL.Elevation))
            g.add((parent_elevation, SAMFL.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((parent_elevation, SAMFL.verticalDatum,
                   Literal("http://spatialreference.org/ref/epsg/4283/", datatype=XSD.anyUri)))
            g.add((this_parent, SAMFL.sampledFeature, this_sample))

            # define GA as an PROV Org with an ISO19115 role of Publisher
            g.add((ga, RDF.type, PROV.Org))
            qualified_attribution = BNode()
            g.add((qualified_attribution, RDF.type, PROV.Attribution))
            g.add((qualified_attribution, PROV.agent, ga))
            g.add((qualified_attribution, PROV.hadRole, AUROLE.Publisher))
            g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution))
        elif model_view == 'dc':
            # this is the cut-down IGSN --> Dublin core mapping describe at http://igsn.github.io/oai/
            g.add((this_sample, RDF.type, DCT.PhysicalResource))
            g.add((this_sample, DCT.coverage, wkt))
            # g.add((this_sample, DCT.creator, Literal('Unknown', datatype=XSD.string)))
            if self.date_acquired is not None:
                g.add((this_sample, DCT.date, Literal(self.date_acquired.isoformat(), datatype=XSD.date)))
            if self.remark is not None:
                g.add((this_sample, DCT.description, Literal(self.remark, datatype=XSD.string)))
            if self.material_type is not None:
                g.add((this_sample, URIRef('http://purl.org/dc/terms/format'), URIRef(self.material_type)))
            g.add((this_sample, DCT.identifier, Literal(self.igsn, datatype=XSD.string)))
            # define GA as a dct:Agent
            g.add((ga, RDF.type, DCT.Agent))
            g.add((this_sample, DCT.publisher, ga))
            # g.add((this_sample, DCT.relation, ga)) -- no value yet in GA DB
            # g.add((this_sample, DCT.subject, ga)) -- how is this different to type?
            # g.add((this_sample, DCT.title, ga)) -- no value at GA
            if self.sample_type is not None:
                g.add((this_sample, DCT.type, URIRef(self.sample_type)))
        elif model_view == 'prov':
            g.add((this_sample, RDF.type, PROV.Entity))
            g.add((ga, RDF.type, PROV.Org))
            qualified_attribution = BNode()
            g.add((qualified_attribution, RDF.type, PROV.Attribution))
            g.add((qualified_attribution, PROV.agent, ga))
            g.add((qualified_attribution, PROV.hadRole, AUROLE.Publisher))
            g.add((this_sample, PROV.qualifiedAttribution, qualified_attribution))

        return g.serialize(format=LDAPI.get_rdf_parser_for_mimetype(rdf_mime))

    def _is_xml_export_valid(self, xml_string):
        """
        Validate and export of this Sample instance in XML using the XSD files from the dev branch
        of the IGSN repo: https://github.com/IGSN/metadata/tree/dev/description. The actual XSD
        files used are in the xml-validation dir, commit be2f0f8d7ef78407c386d3c8a0aba7c31397aa29

        :param xml_string:
        :return: boolean
        """
        # online validator: https://www.corefiling.com/opensource/schemaValidate.html
        # load the schema
        xsd_doc = etree.parse('../xml-validation/igsn-csiro-v2.0-all.xsd')
        xsd = etree.XMLSchema(xsd_doc)

        # load the XML doc
        xml = etree.parse(StringIO(xml_string))

        return xsd.validate(xml)

    def export_dc_xml(self):
        """
        Exports this Sample instance in XML that validates against the OAI Dublin Core Metadata from
        https://www.openarchives.org/OAI/openarchivesprotocol.html

        using the IGSN to Dublin Core mappings from
        https://github.com/IGSN/metadata/wiki/IGSN-Registration-Metadata-Version-1.0

        :return: XML string
        """

        '''
        <record>
        <header><identifier>oai:registry.igsn.org:18211</identifier>
        <datestamp>2013-06-19T15:28:23Z</datestamp>
        <setSpec>IEDA</setSpec><setSpec>IEDA.SESAR</setSpec>
        </header>
        <metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
        <dc:creator>IEDA</dc:creator>
        <dc:identifier>http://hdl.handle.net/10273/847000108</dc:identifier>
        <dc:identifier>igsn:10273/847000108</dc:identifier>
        </oai_dc:dc></metadata></record>
        '''

        if isinstance(self.date_acquired, datetime):
            sampling_time = self.date_acquired.isoformat()
        elif isinstance(self.date_load, datetime):
            sampling_time = self.date_load.isoformat()
        elif isinstance(self.date_modified, datetime):
            sampling_time = self.date_modified.isoformat()
        else:
            sampling_time = Sample.URI_MISSSING
        if isinstance(self.date_modified, datetime):
            modified_time = self.date_modified.isoformat()
        elif isinstance(self.date_load, datetime):
            modified_time = self.date_load.isoformat()
         # URI for this sample
        base_uri = 'http://pid.geoscience.gov.au/sample/'
        this_sample = URIRef(base_uri + self.igsn)

        # define GA
        ga = URIRef(Sample.URI_GA)

        GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')

        # sample location in GML & WKT, formulation from GeoSPARQL
        wkt = Literal(self._generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self._generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        dt = datetime.now()

        format = URIRef(self.material_type)

        # TODO:   add is site uri
        xml = 'xml = <record>\
        <header>\
        <identifier>' + self.entity_uri + '</identifier>\
        <datestamp>' + datetime_to_datestamp(dt) + '</datestamp>\
        <setSpec>IEDA</setSpec>\
        <setSpec>IEDA.SESAR</setSpec>\
        </header>\
        <metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"\
           xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"\
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
           xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">\
        <dc:creator>' + ga + '</dc:creator>\
        <dc:identifier>' + self.igsn + '</dc:identifier>\
        <dc:type>' + self.sample_type + '</dc:type>\
        <dc:coverage>' + wkt + '</dc:coverage>\
        </oai_dc:dc> \
        </metadata> \
        </record>'

        return xml

    def export_as_csirov3_xml(self):
        """
        Exports this Sample instance in XML that validates against the CSIRO v3 Schema

        :return: XML string
        """
        # CSIRO
        '''
        <?xml version="1.0" encoding="UTF-8"?>
        <igsn:samples
                xsi:schemaLocation="http://igsn.org/schema/kernel-v.1.0 ../xml-validation/igsn-csiro-v2.0.xsd"
                xmlns:igsn="http://igsn.org/schema/kernel-v.1.0"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <!-- from https://github.com/kitchenprinzessin3880/csiro-igsn-schema/blob/master/example-capricon.xml -->
            <!--igsn:subNamespace>CAP</igsn:subNamespace -->
            <igsn:sample>
                <igsn:sampleNumber identifierType="igsn">CSCAP0001</igsn:sampleNumber>
                <igsn:sampleName>Cap0001-JHP8</igsn:sampleName>
                <igsn:isPublic>1</igsn:isPublic>
                <igsn:landingPage><![CDATA[https://capdf.csiro.au/gs-hydrogeochem/public/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=public:hydrogeochem&cql_filter=sid%3D243]]></igsn:landingPage>
                <igsn:sampleTypes>
                    <igsn:sampleType>http://vocabulary.odm2.org/specimentype/precipitationBulk</igsn:sampleType>
                </igsn:sampleTypes>
                <igsn:materialTypes>
                    <igsn:materialType>http://vocabulary.odm2.org/medium/snow</igsn:materialType>
                </igsn:materialTypes>
                <igsn:samplingLocation/>
                <igsn:sampling_time/>
                <igsn:sampleCuration>
                    <igsn:curation> <!-- nick -->
                        <igsn:curator>Mineral Resources Flagship,CSIRO</igsn:curator>
                        <igsn:curationLocation>Some location</igsn:curationLocation>
                    </igsn:curation> <!-- nick -->
                </igsn:sampleCuration>
                <igsn:classification>rock</igsn:classification>
                <igsn:comments>This is a fake comment</igsn:comments>
                <igsn:otherNames>
                    <igsn:otherName>FakeOtherName</igsn:otherName>
                </igsn:otherNames>
                <igsn:purpose>Fake purpose</igsn:purpose>
                <igsn:samplingFeatures>
                    <igsn:samplingFeature>
                        <igsn:samplingFeatureName>mountain X</igsn:samplingFeatureName>
                    </igsn:samplingFeature>
                </igsn:samplingFeatures>
                <igsn:sampleCollectors>
                    <igsn:collector>Nick Car</igsn:collector>
                </igsn:sampleCollectors>
                <igsn:samplingMethod>bucket</igsn:samplingMethod>
                <igsn:samplingCampaign>Campaign X</igsn:samplingCampaign>
                <igsn:relatedResources>
                    <igsn:relatedResourceIdentifier>abcd1234</igsn:relatedResourceIdentifier>
                </igsn:relatedResources>
                <igsn:logElement event="submitted" timeStamp="2015-09-10T18:20:30" />
            </igsn:sample>
        </igsn:samples>
        '''

        # CSIRO v3
        sample_wkt = self._generate_sample_wkt_csirov3_xml()
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        cs = 'https://igsn.csiro.au/schemas/3.0'
        root = etree.Element(
            '{%s}resources' % cs,
            # namespace='https://igsn.csiro.au/schemas/3.0',
            nsmap={'xsi': xsi, 'cs': cs})
        root.attrib['{%s}schemaLocation' % xsi] = \
            'https://igsn.csiro.au/schemas/3.0 igsn-csiro-v3.0.xsd'
        r = etree.SubElement(root, '{%s}resource' % cs)
        r.attrib['registrationType'] = 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/SampleResource'
        etree.SubElement(r, '{%s}resourceIdentifier' % cs).text = self.igsn
        etree.SubElement(r, '{%s}landingPage' % cs).text = 'https://pid.geoscience.gov.au/sample/' + self.igsn
        # etree.SubElement(r, '{%s}isPublic' % cs).text = 'true'
        etree.SubElement(r, '{%s}resourceTitle' % cs).text = 'Sample igsn:' + self.igsn
        rt = etree.SubElement(r, '{%s}resourceTypes' % cs)
        etree.SubElement(rt, '{%s}resourceType' % cs).text = self.sample_type
        mt = etree.SubElement(r, '{%s}materialTypes' % cs)
        etree.SubElement(mt, '{%s}materialType' % cs).text = self.material_type
        etree.SubElement(r, '{%s}method' % cs).text = self.method_type
        # etree.SubElement(r, '{%s}campaign' % cs).text = ''
        l = etree.SubElement(r, '{%s}location' % cs)
        g = etree.SubElement(l, '{%s}geometry' % cs)
        if self.srid is not None:
            g.text = sample_wkt
            g.attrib['srid'] = 'https://epsg.io/' + self.srid
            g.attrib['verticalDatum'] = 'https://epsg.io/4283'
        # g.attrib['geometryURI'] = 'http://www.altova.com'
        cd = etree.SubElement(r, '{%s}curationDetails' % cs)
        c = etree.SubElement(cd, '{%s}curation' % cs)
        etree.SubElement(c, '{%s}curator' % cs).text = 'Geoscience Australia'
        etree.SubElement(c, '{%s}curationDate' % cs).text = datetime.now().strftime('%Y')
        etree.SubElement(c, '{%s}curationLocation' % cs).text = \
            'Geoscience Australia, Jerrabomberra Ave, Symonston, ACT, Australia'
        etree.SubElement(c, '{%s}curatingInstitution' % cs).attrib['institutionURI'] = \
            'http://pid.geoscience.gov.au/org/ga'

        if self.sample_no is not None:
            ai = etree.SubElement(r, '{%s}alternateIdentifiers' % cs)
            etree.SubElement(ai, '{%s}alternateIdentifiers' % cs).text = self.sample_no

        if self.date_acquired is not None:
            ti = etree.SubElement(r, '{%s}date' % cs)
            etree.SubElement(ti, '{%s}timeInstant' % cs).text = self.date_acquired

        if self.remark is not None:
            etree.SubElement(r, '{%s}comment' % cs).text = self.remark

        # em.classifications(
        #     em.classification('')),
        # em.purpose('a'),
        # em.sampledFeatures(
        #     em.sampledFeature('token', sampledFeatureURI='http://www.altova.com')),
        # em.collectors(
        #     em.collector(
        #         em.collectorName('a'),
        #         em.collectorIdentifier(
        #             'token',
        #             collectorIdentifierType='http://pid.geoscience.gov.au/def/voc/igsn-codelists/URL'))),
        # em.contributors(
        #     em.contributor(
        #         em.contributorName('a'),
        #         em.contributorIdentifier(
        #             'token',
        #             contributorIdentifierType='http://pid.geoscience.gov.au/def/voc/igsn-codelists/Handle'
        #         ),
        #         contributorType='http://pid.geoscience.gov.au/def/voc/igsn-codelists/Other')),
        # em.relatedResourceIdentifiers(
        #     em.relatedResourceIdentifier(
        #         'String',
        #         relatedIdentifierType='http://pid.geoscience.gov.au/def/voc/igsn-codelists/bibcode',
        #         relationType='http://pid.geoscience.gov.au/def/voc/igsn-codelists/IsSourceOf')),
        # em.logDate('2001', eventType='registered')

        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return xml

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

        html += '<table class="data">'
        html += '   <tr><th>Property</th><th>Value</th></tr>'
        if model_view == 'igsn':
            # TODO: complete the properties in this view
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            html += '   <tr><th>Identifier</th><td>' + self.igsn + '</td></tr>'
            if self.sampleid is not None:
                html += '   <tr><th>Sample ID</th><td>' + self.sampleid + '</td></tr>'
            if self.date_acquired is not None:
                html += '   <tr><th>Date</th><td>' + self.date_acquired.isoformat() + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Sample Type</th><td><a href="' + self.sample_type + '">' + self.sample_type.split('/')[-1] + '</a></td></tr>'
            html += '   <tr><th>Sampling Location (WKT)</th><td>' + self._generate_sample_wkt() + '</td></tr>'
            html += '   <tr><th>Current Location</th><td>GA Services building</td></tr>'
            # TODO: make this resolve
            html += '   <tr><th>Sampling Feature</th><td><a style="text-decoration: line-through;" href="' + TERM_LOOKUP['entity_type'][self.entity_type] + '">' + TERM_LOOKUP['entity_type'][self.entity_type] + '</a></td></tr>'
            if self.method_type is not None:
                html += '   <tr><th>Method Type</th><td><a href="' + self.method_type + '">' + self.method_type.split('/')[-1] + '</a></td></tr>'
            # TODO: replace with dynamic
            html += '   <tr><th>Access Rights</th><td><a href="http://pid.geoscience.gov.au/def/voc/igsn-codelists/Public">Public</a></td></tr>'
            html += '   <tr><th>Publisher</th><td><a href="http://pid.geoscience.gov.au/org/ga">Geoscience Australia</a></td></tr>'
            if self.remark is not None:
                html += '   <tr><th>Description</th><td>' + self.remark + '</td></tr>'

        elif model_view == 'dc':
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            html += '   <tr><th>Coverage</th><td>' + self._generate_sample_wkt() + '</td></tr>'
            if self.date_acquired is not None:
                html += '   <tr><th>Date</th><td>' + self.date_acquired.isoformat() + '</td></tr>'
            if self.remark is not None:
                html += '   <tr><th>Description</th><td>' + self.remark + '</td></tr>'
            if self.material_type is not None:
                html += '   <tr><th>Format</th><td>' + self.material_type + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Type</th><td>' + self.sample_type + '</td></tr>'

        html += '</table>'

        if self.date_acquired is not None:
            year_acquired = datetime.strftime(self.date_acquired, '%Y')
        else:
            year_acquired = 'XXXX'

        return render_template(
            'page_sample.html',
            view=model_view,
            igsn=self.igsn,
            year_acquired=year_acquired,
            placed_html=html,
            date_now=datetime.now().strftime('%d %B %Y')
        )


class ParameterError(ValueError):
    pass

if __name__ == '__main__':
    s = Sample('http://fake.com', 'AU100')
    print s.export_dc_xml()

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()
