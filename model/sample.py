from lxml import etree
from rdflib import Graph, URIRef, RDF, RDFS, XSD, Namespace, Literal, BNode
from StringIO import StringIO
import requests
from model.datestamp import *
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
        self.sample_id = None
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
        self.date_modified = None
        self.modified_datestamp = None
        self.sample_no = None
        self.wkt = None
        self.ga = URIRef(Sample.URI_GA)
        # populate all instance variables from API
        # TODO: lazy load this, i.e. only populate if a view that need populating is loaded which is every view except for Alternates

        if oracle_api_samples_url is None:
            self._populate_from_xml_file(xml)
        else:
            self._populate_from_oracle_api()

    def render(self, view, mimetype):
        if mimetype in LDAPI.get_rdf_mimetypes_list():
            return Response(self.export_rdf(view, mimetype), mimetype=mimetype)

        if view == 'igsn-o':  # the GA IGSN Ontology in RDF or HTML
            # RDF formats handled by general case
            # HTML is the only other enabled format for igsn view
            return self.export_html(model_view=view)
        elif view == 'dc':  # Dublin Core in RDF or HTML
            # RDF formats handled by general case
            if mimetype == 'text/xml':
                return Response(
                    '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_dc_xml(),
                    mimetype='text/xml')
            else:
                return self.export_html(model_view=view)
        elif view == 'igsn':  # the community agreed description metadata schema
            # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_igsn_xml(),
                mimetype='text/xml'
            )
        elif view == 'csirov3':
            # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_csirov3_xml(),
                mimetype='text/xml'
            )
        elif view == 'prov':  # PROV-O in RDF (soon or HTML)
            # RDF formats handled by general case
            # only RDF for this view so set the mimetype to our favourite mime format
            return self.export_html(model_view=view)

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

        if self.validate_xml(r.content):
            self._populate_from_xml_file(StringIO(r.content))
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
                self.sample_id = elem.text
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
                    self.date_acquired = str2datetime(elem.text)
                else:
                    self.date_acquired = Sample.URI_MISSSING
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
            elif elem.tag == "MODIFIED_DATE":
                self.date_modified = str2datetime(elem.text)
            elif elem.tag == "SAMPLENO":
                if elem.text is not None:
                    self.sample_no = elem.text
        self.modified_datestamp = datetime_to_datestamp(self.date_modified)

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

    def __graph_preconstruct(self, g):
        u = '''
            PREFIX prov: <http://www.w3.org/ns/prov#>
            DELETE {
                ?a prov:generated ?e .
            }
            INSERT {
                ?e prov:wasGeneratedBy ?a .
            }
            WHERE {
                ?a prov:generated ?e .
            }
        '''
        g.update(u)

        return g

    def __gen_visjs_nodes(self, g):
        nodes = ''

        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            SELECT *
            WHERE {
                ?s a ?o .
                {?s a prov:Entity .}
                UNION
                {?s a prov:Activity .}
                UNION
                {?s a prov:Agent .}
                OPTIONAL {?s rdfs:label ?label .}
            }
            '''
        for row in g.query(q):
            if str(row['o']) == 'http://www.w3.org/ns/prov#Entity':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Entity'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", shape: "ellipse", color:{background:"#FFFC87", border:"#808080"}},\n' % {
                    'node_id': row['s'],
                    'label': label
                }
            elif str(row['o']) == 'http://www.w3.org/ns/prov#Activity':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Activity'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", shape: "box", color:{background:"#9FB1FC", border:"blue"}},\n' % {
                    'node_id': row['s'],
                    'label': label
                }
            elif str(row['o']) == 'http://www.w3.org/ns/prov#Agent':
                if row['label'] is not None:
                    label = row['label']
                else:
                    label = 'Agent'
                nodes += '\t\t\t\t{id: "%(node_id)s", label: "%(label)s", image: "/static/img/agent.png", shape: "image"},\n' % {
                    'node_id': row['s'],
                    'label': label
                }

        return nodes

    def __gen_visjs_edges(self, g):
        edges = ''

        q = '''
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            SELECT *
            WHERE {
                ?s ?p ?o .
                ?s prov:wasAttributedTo|prov:wasGeneratedBy|prov:used|prov:wasDerivedFrom|prov:wasInformedBy ?o .
            }
            '''
        for row in g.query(q):
            edges += '\t\t\t\t{from: "%(from)s", to: "%(to)s", arrows:"to", font: {align: "bottom"}, color:{color:"black"}, label: "%(relationship)s"},\n' % {
                'from': row['s'],
                'to': row['o'],
                'relationship': str(row['p']).split('#')[1]
            }

        return edges

    def _make_vsjs(self, g):
        g = self.__graph_preconstruct(g)

        nodes = 'var nodes = new vis.DataSet([\n'
        nodes += self.__gen_visjs_nodes(g)
        nodes = nodes.rstrip().rstrip(',') + '\n\t\t\t]);\n'

        edges = 'var edges = new vis.DataSet([\n'
        edges += self.__gen_visjs_edges(g)
        edges = edges.rstrip().rstrip(',') + '\n\t\t\t]);\n'

        visjs = '''
        %(nodes)s

        %(edges)s

        var container = document.getElementById('network');

        var data = {
            nodes: nodes,
            edges: edges,
        };

        var options = {};
        var network = new vis.Network(container, data, options);
        ''' % {'nodes': nodes, 'edges': edges}

        return visjs

    def export_rdf(self, model_view='default', rdf_mime='text/turtle'):
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
        g.add((this_sample, RDFS.label, Literal('Sample igsn:' + self.igsn, datatype=XSD.string)))

        # define GA
        ga = URIRef(Sample.URI_GA)

        # sample location in GML & WKT, formulation from GeoSPARQL
        wkt = Literal(self._generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self._generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        # select model view
        if model_view == 'igsn-o':
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

            if self.material_type != 'http://www.opengis.net/def/nil/OGC/0/missing':
                g.add((this_sample, SAMFL.materialClass, URIRef(self.material_type)))
            if self.method_type != 'http://www.opengis.net/def/nil/OGC/0/missing':
                g.add((this_sample, SAMFL.samplingMethod, URIRef(self.method_type)))
            if self.date_acquired != 'http://www.opengis.net/def/nil/OGC/0/missing':
                g.add((this_sample, SAMFL.samplingTime, Literal(self.date_acquired.isoformat(), datatype=XSD.datetime)))

            # TODO: represent Public/Private (and other?) access methods in DB, add to terms in vocab?
            g.add((this_sample, DCT.accessRights, URIRef(TERM_LOOKUP['access']['Public'])))
            # TODO: make a register of Entities
            if self.entity_uri != 'http://www.opengis.net/def/nil/OGC/0/missing':
                this_parent = URIRef(self.entity_uri)
            else:
                # TODO: get a real parent URL
                this_parent = URIRef('http://www.opengis.net/def/nil/OGC/0/missing')

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

            # just for visjs
            g.add((ga, RDF.type, PROV.Agent))
            g.add((this_sample, PROV.wasAttributedTo, ga))
            g.add((ga, RDFS.label, Literal('Geoscience Australia', datatype=XSD.string)))

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
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """
        template = render_template(
            'sample_dc.xml',
            identifier=self.igsn,
            description=self.remark,
            date=self.date_acquired,
            type=self.sample_type,
            format=self.material_type,
            wkt='POINT' + self._generate_sample_wkt().split('POINT')[1],  # gml = self._generate_sample_gml()
            creator='Geoscience Australia',
            publisher='Geoscience Australia'
        )

        return template

    def export_igsn_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """
        template = render_template(
            'sample_igsn.xml',
            igsn=self.igsn,
            sample_id=self.sample_id,
            description=self.remark,
            wkt='POINT' + self._generate_sample_wkt().split('POINT')[1],  # gml = self._generate_sample_gml()
            sample_type=self.sample_type,
            material_type=self.material_type,
            collection_method=self.method_type,
            collection_time=self.date_acquired
        )

        return template

    def export_csirov3_xml(self):
        """
        Exports this Sample instance in XML that validates against the CSIRO v3 Schema

        :return: XML string
        """
        # sample location in GML & WKT, formulation from GeoSPARQL
        template = render_template(
            'sample_csirov3.xml',
            igsn=self.igsn,
            sample_type=self.sample_type,
            material_type=self.material_type,
            method_type=self.method_type,
            wkt='POINT' + self._generate_sample_wkt().split('POINT')[1],  # kludge to remove EPSG URI,
            sample_id=self.sample_id,
            collection_time=self.date_acquired
        )

        return template

    def export_html(self, model_view='default'):
        """
        Exports this instance in HTML, according to a given model from the list of supported models.

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
            'default']
        :return: HTML string
        """
        if model_view == 'igsn-o':
            view_title = 'IGSN Ontology view'

            sample_table_html = render_template(
                'sample_igsn-o.html',
                igsn=self.igsn,
                sample_id=self.sample_id,
                description=self.remark,
                date_acquired=self.date_acquired,
                sample_type=self.sample_type,
                wkt='POINT' + self._generate_sample_wkt().split('POINT')[1],
                sampling_feature=TERM_LOOKUP['entity_type'][self.entity_type],
                method_type=self.method_type,
                material_type=self.material_type
            )

        elif model_view == 'dc':
            view_title = 'Dublin Core view'

            sample_table_html = render_template(
                'sample_dc.html',
                identifier=self.igsn,
                description=self.remark,
                date=self.date_acquired,
                type=self.sample_type,
                format=self.material_type,
                wkt='POINT' + self._generate_sample_wkt().split('POINT')[1],  # gml = self._generate_sample_gml()
                creator='Geoscience Australia',
                publisher='Geoscience Australia'
            )

        elif model_view == 'prov':
            view_title = 'PROV Ontology view'
            prov_turtle = self.export_rdf('prov', 'text/turtle')
            g = Graph().parse(data=prov_turtle, format='turtle')

            sample_table_html = render_template(
                'sample_prov.html',
                visjs=self._make_vsjs(g),
                prov_turtle=prov_turtle,
            )

        if self.date_acquired is not None and self.date_acquired != Sample.URI_MISSSING:
            year_acquired = datetime.strftime(self.date_acquired, '%Y')
        else:
            year_acquired = 'XXXX'

        return render_template(
            'page_sample.html',
            view=model_view,
            igsn=self.igsn,
            year_acquired=year_acquired,
            view_title=view_title,
            sample_table_html=sample_table_html,
            date_now=datetime.now().strftime('%d %B %Y'),
            system_url='http://54.66.133.7'
        )


class ParameterError(ValueError):
    pass

if __name__ == '__main__':
    s = Sample('http://fake.com', 'AU100')
    print s.export_dc_xml()

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()
