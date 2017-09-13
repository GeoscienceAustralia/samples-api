from datetime import datetime
from io import StringIO
import requests
from flask import Response, render_template
from lxml import etree
from lxml import objectify
from rdflib import Graph, URIRef, RDF, RDFS, XSD, OWL, Namespace, Literal, BNode
import _config
from _ldapi.__init__ import LDAPI
from controller.datestamp import *


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

    def __init__(self, igsn, xml=None):
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
        self.sample_no = None

        if xml is not None:  # even if there are values for Oracle API URI and IGSN, load from XML file if present
            self._populate_from_xml_file(xml)
        else:
            self._populate_from_oracle_api()

    def render(self, view, mimetype):
        if self.sample_no is None:
            return Response('Sample with IGSN {} not found.'.format(self.igsn), status=404, mimetype='text/plain')

        if view == 'igsn-o':
            if mimetype == 'text/html':
                return self.export_html(model_view=view)
            else:
                return Response(self.export_rdf(view, mimetype), mimetype=mimetype)
        elif view == 'dc':
            if mimetype == 'text/html':
                return self.export_html(model_view=view)
            elif mimetype == 'text/xml':
                return Response(self.export_dc_xml(), mimetype=mimetype)
            else:
                return Response(self.export_rdf(view, mimetype), mimetype=mimetype)
        elif view == 'igsn':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_igsn_xml(),
                mimetype='text/xml'
            )
        elif view == 'igsn-r1':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_igsn_r1_xml(),
                mimetype='text/xml'
            )
        elif view == 'csirov3':  # only XML for this view
            return Response(
                '<?xml version="1.0" encoding="utf-8"?>\n' + self.export_csirov3_xml(),
                mimetype='text/xml'
            )
        elif view == 'prov':
            if mimetype == 'text/html':
                return self.export_html(model_view=view)
            else:
                return Response(self.export_rdf(view, mimetype), mimetype=mimetype)
        elif view == 'sosa':  # RDF only for this view
            return Response(self.export_rdf(view, mimetype), mimetype=mimetype)

    def validate_xml(self, xml):
        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print('not valid xml')
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
        r = requests.get(_config.XML_API_URL_SAMPLE.format(self.igsn))
        if "No data" in r.content.decode('utf-8'):
            raise ParameterError('No Data')

        if self.validate_xml(r.content):
            self._populate_from_xml_file(r.content)
            return True
        else:
            return False

    def _populate_from_xml_file(self, xml):
        """
        Populates this instance with data from an XML file.

        :param xml: XML according to GA's Oracle XML API from the Samples DB
        :return: None
        """
        try:
            root = objectify.fromstring(xml)
            from .lookups import TERM_LOOKUP

            self.igsn = root.ROW.IGSN
            self.sample_id = root.ROW.SAMPLEID
            self.sample_no = root.ROW.SAMPLENO
            self.sample_type = TERM_LOOKUP['sample_type'].get(root.ROW.SAMPLE_TYPE_NEW)
            if self.sample_type is None:
                self.sample_type = TERM_LOOKUP['sample_type']['unknown']
            self.method_type = TERM_LOOKUP['method_type'].get(root.ROW.SAMPLING_METHOD)
            if self.method_type is None:
                self.method_type = TERM_LOOKUP['method_type']['Unknown']
            self.material_type = TERM_LOOKUP['material_type'].get(root.ROW.MATERIAL_CLASS)
            if self.material_type is None:
                self.material_type = TERM_LOOKUP['material_type']['unknown']
            # self.long_min = root.ROW.SAMPLE_MIN_LONGITUDE
            # self.long_max = root.ROW.SAMPLE_MAX_LONGITUDE
            # self.lat_min = root.ROW.SAMPLE_MIN_LATITUDE
            # self.lat_max = root.ROW.SAMPLE_MAX_LATITUDE
            self.gtype = root.ROW.GEOM.SDO_GTYPE
            self.srid = root.ROW.GEOM.SDO_SRID
            self.x = root.ROW.GEOM.SDO_POINT.X
            self.y = root.ROW.GEOM.SDO_POINT.Y
            self.z = root.ROW.GEOM.SDO_POINT.Z
            self.elem_info = root.ROW.GEOM.SDO_ELEM_INFO
            self.ordinates = root.ROW.GEOM.SDO_ORDINATES
            self.state = TERM_LOOKUP['state'].get(root.ROW.STATEID)
            if self.state is None:
                self.state = Sample.URI_MISSSING
            self.country = root.ROW.COUNTRY
            self.depth_top = root.ROW.TOP_DEPTH
            self.depth_base = root.ROW.BASE_DEPTH
            self.strath = root.ROW.STRATNAME
            self.age = root.ROW.AGE
            self.remark = root.ROW.REMARK
            self.lith = TERM_LOOKUP['lith'].get(root.ROW.LITHNAME)
            if self.lith is None:
                self.lith = Sample.URI_MISSSING
            self.date_acquired = str2datetime(root.ROW.ACQUIREDATE).date() if root.ROW.ACQUIREDATE != '' else None
            self.date_modified = str2datetime(root.ROW.MODIFIED_DATE) if root.ROW.MODIFIED_DATE != '' else None
            self.entity_uri = 'http://pid.geoscience.gov.au/site/' + str(root.ROW.ENO) if root.ROW.ENO is not None else None
            self.entity_name = root.ROW.ENTITYID
            self.entity_type = TERM_LOOKUP['entity_type'].get(root.ROW.ENTITY_TYPE)
            self.hole_long_min = root.ROW.HOLE_MIN_LONGITUDE if root.ROW.HOLE_MIN_LONGITUDE != '' else None
            self.hole_long_max = root.ROW.HOLE_MAX_LONGITUDE if root.ROW.HOLE_MAX_LONGITUDE != '' else None
            self.hole_lat_min = root.ROW.HOLE_MIN_LATITUDE if root.ROW.HOLE_MIN_LATITUDE != '' else None
            self.hole_lat_max = root.ROW.HOLE_MAX_LATITUDE if root.ROW.HOLE_MAX_LATITUDE != '' else None
            # self.date_modified = None
            # self.modified_datestamp = None
            # TODO: replace all the other calles to this with a call to self.wkt instead
            # self.wkt = self._generate_sample_wkt()
        except Exception as e:
            print(e)

        return True

    def _generate_sample_wkt(self):
        if self.z is not None:
            wkt = 'SRID={};POINTZ({} {} {})'.format(self.srid, self.x, self.y, self.z)
        else:
            if self.srid is not None and self.x is not None and self.y is not None:
                wkt = 'SRID={};POINT({} {} {})'.format(self.srid, self.x, self.y)
            else:
                wkt = ''

        return wkt

    def _generate_sample_gml(self):
        if self.z is not None:
            gml = '<gml:Point srsDimension="3" srsName="https://epsg.io/{}">' \
                  '<gml:pos>{} {} {}</gml:pos>' \
                  '</gml:Point>'.format(self.srid, self.x, self.y, self.z)
        else:
            if self.srid is not None and self.x is not None and self.y is not None:
                gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/{}">' \
                      '<gml:pos>{} {}</gml:pos>' \
                      '</gml:Point>'.format(self.srid, self.x, self.y)
            else:
                gml = ''

        return gml

    def _generate_parent_wkt(self):
        if self.hole_long_min is not None and self.hole_long_max is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'long_max': self.hole_long_max,
                'lat_min': self.hole_lat_min,
                'lat_max': self.hole_lat_max
            }
            wkt = 'SRID={srid};POLYGON(({long_min} {lat_max}, {long_max} {lat_max}, {long_max} {lat_min}, {long_max} {lat_min}, {long_min} {lat_max}))'.format(**coordinates)
        elif self.hole_long_min is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'lat_min': self.hole_lat_min
            }
            wkt = 'SRID={srid};POINT({long_min} {lat_min})'.format(**coordinates)
        else:
            wkt = ''

        return wkt

    def _generate_parent_gml(self):
        if self.hole_long_min is not None and self.hole_long_max is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'long_max': self.hole_long_max,
                'lat_min': self.hole_lat_min,
                'lat_max': self.hole_lat_max
            }
            gml = '<ogc:BBOX>'\
                  '<ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>'\
                  '<gml:Envelope srsName="https://epsg.io/{srid}">' \
                  '<gml:upperCorner>{long_min} {lat_max}</gml:upperCorner>' \
                  '<gml:lowerCorner>{long_max} {lat_min}</gml:lowerCorner>'\
                  '</gml:Envelope>'\
                  '</ogc:BBOX>'.format(**coordinates)
        elif self.hole_long_min is not None:
            coordinates = {
                'srid': self.srid,
                'long_min': self.hole_long_min,
                'lat_min': self.hole_lat_min
            }
            gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/{srid}">' \
                  '<gml:pos>{long_min} {lat_min}</gml:pos>' \
                  '</gml:Point>'.format(**coordinates)
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

    def export_rdf(self, model_view='igsn-o', rdf_mime='text/turtle'):
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

        # URI for this sample
        base_uri = 'http://pid.geoscience.gov.au/sample/'
        this_sample = URIRef(base_uri + self.igsn)
        g.add((this_sample, RDFS.label, Literal('Sample igsn:' + self.igsn, datatype=XSD.string)))

        # define GA
        ga = URIRef(Sample.URI_GA)

        # pingback endpoint
        PROV = Namespace('http://www.w3.org/ns/prov#')
        g.bind('prov', PROV)
        g.add((this_sample, PROV.pingback, URIRef(base_uri + '/pingback')))

        # generate things common to particular views
        if model_view == 'igsn-o' or model_view == 'dc':
            # DC = Namespace('http://purl.org/dc/elements/1.1/')
            DCT = Namespace('http://purl.org/dc/terms/')
            g.bind('dct', DCT)

        if model_view == 'igsn-o' or model_view == 'sosa':
            SAMFL = Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
            g.bind('samfl', SAMFL)

        if model_view == 'igsn-o' or model_view == 'sosa' or model_view == 'dc':
            GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')
            g.bind('geosp', GEOSP)

            # sample location in GML & WKT, formulation from GeoSPARQL
            wkt = Literal(self._generate_sample_wkt(), datatype=GEOSP.wktLiteral)
            gml = Literal(self._generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        if model_view == 'igsn-o' or model_view == 'prov':
            PROV = Namespace('http://www.w3.org/ns/prov#')
            g.bind('prov', PROV)
            AUROLE = Namespace('http://communications.data.gov.au/def/role/')
            g.bind('aurole', AUROLE)

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
            g.add((this_sample, IGSN.alternateIdentifier, Literal(self.igsn, datatype=IGSN.IGSN)))
            # g.add((alternate_identifier, RDF.type, URIRef('http://pid.geoscience.gov.au/def/voc/igsn-codelists/IGSN')))
            # g.add((alternate_identifier, PROV.value, Literal(self.igsn, datatype=XSD.string)))

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
            if self.date_acquired is not None:
                g.add((this_sample, SAMFL.samplingTime, Literal(self.date_acquired.isoformat(), datatype=XSD.datetime)))

            from model.lookups import TERM_LOOKUP
            # TODO: represent Public/Private (and other?) access methods in DB, add to terms in vocab?
            g.add((this_sample, DCT.accessRights, URIRef(TERM_LOOKUP['access']['Public'])))
            # TODO: make a register of Entities
            site = URIRef(self.entity_uri)

            g.add((this_sample, SAMFL.relatedSamplingFeature, site))  # could be OM.featureOfInterest

            # parent
            if self.entity_type is not None:
                g.add((site, RDF.type, URIRef(self.entity_type)))
            else:
                g.add((
                    site,
                    RDF.type,
                    URIRef('http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole')
                ))

            site_geometry = BNode()
            g.add((site, GEOSP.hasGeometry, site_geometry))
            g.add((site_geometry, RDF.type, SAMFL.Point))  # TODO: extend this for other geometry types
            g.add((site_geometry, GEOSP.asWKT, Literal(self._generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
            g.add((site_geometry, GEOSP.asGML, Literal(self._generate_parent_gml(), datatype=GEOSP.wktLiteral)))

            site_elevation = BNode()
            g.add((site, SAMFL.samplingElevation, site_elevation))
            g.add((site_elevation, RDF.type, SAMFL.Elevation))
            g.add((site_elevation, SAMFL.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((site_elevation, SAMFL.verticalDatum,
                   Literal("http://spatialreference.org/ref/epsg/4283/", datatype=XSD.anyUri)))
            g.add((site, SAMFL.sampledFeature, this_sample))

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
        elif model_view == 'sosa':
            SOSA = Namespace('http://www.w3.org/ns/sosa/')
            g.bind('sosa', SOSA)
            # Sample
            g.add((this_sample, RDF.type, SOSA.Sample))

            #
            #   Sampling
            #
            # Sampling declaration
            sampling = BNode()
            g.add((sampling, RDF.type, SOSA.Sampling))
            if self.date_acquired is not None:
                g.add((sampling, SOSA.resultTime, Literal(self.date_acquired.isoformat(), datatype=XSD.date)))
            g.add((this_sample, SOSA.isResultOf, sampling))  # associate

            #
            #   Sampler
            #
            # Sampler declaration
            sampler = BNode()
            g.add((sampler, RDF.type, SOSA.Sampler))
            g.add((sampler, RDF.type, URIRef(self.method_type)))
            g.add((sampling, SOSA.madeBySampler, sampler))  # associate Sampler (with Sampling)

            # #
            # #   Procedure
            # #
            # # Procedure declaration
            # procedure = BNode()
            # g.add((procedure, RDF.type, SOSA.Procedure))
            # # g.add((this_sample, RDF.type, SOSA.Procedure))
            #  TODO: domsthing about missing if any method info is not known
            # # associate Procedure
            # g.add((this_sample, SOSA.usedProcedure, procedure))

            SAMP = Namespace('http://www.w3.org/ns/sosa/sampling/')
            g.bind('sampling', SAMP)

            # SampleRelationship to Site
            site = URIRef(self.entity_uri)
            sr = BNode()
            g.add((sr, RDF.type, SAMP.SampleRelationship))
            g.add((sr, SAMP.relatedSample, site))
            # TODO: replace with a real Concept URI
            g.add((sr, SAMP.natureOfRelationship, URIRef('http://example.org/sampling/relationship/subsample')))
            g.add((this_sample, SAMP.hasSampleRelationship, sr))  # associate

            # Site details
            g.add((site, RDF.type, OWL.NamedIndividual))
            # specific type of Site
            if self.entity_type is not None:
                site_type = URIRef(self.entity_type)
            else:
                site_type = URIRef('http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole')
            g.add((site, RDF.type, site_type))
            g.add((site_type, RDFS.subClassOf, SOSA.Sample))

            # FOI geometry
            site_geometry = BNode()
            g.add((site, GEOSP.hasGeometry, site_geometry))
            g.add((site_geometry, RDF.type, GEOSP.Geometry))
            g.add((site_geometry, GEOSP.asWKT, Literal(self._generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
            # g.add((site_geometry, GEOSP.asGML, Literal(self._generate_parent_gml(), datatype=GEOSP.wktLiteral)))
            # FOI elevation
            site_elevation = BNode()
            g.add((site, SAMFL.samplingElevation, site_elevation))
            g.add((site_elevation, RDF.type, SAMFL.Elevation))
            g.add((site_elevation, SAMFL.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((site_elevation, SAMFL.verticalDatum,
                   Literal("http://spatialreference.org/ref/epsg/4283/", datatype=XSD.anyUri)))

            #
            #   Feature of Interest
            #
            # domain feature, same for all Samples
            domain_feature = URIRef('http://registry.it.csiro.au/sandbox/csiro/oznome/feature/earth-realm/lithosphere')
            g.add((domain_feature, RDF.type, SOSA.FeatureOfInterest))
            SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
            g.bind('skos', SKOS)
            g.add((domain_feature, SKOS.exactMatch, URIRef('http://sweet.jpl.nasa.gov/2.3/realmGeol.owl#Lithosphere')))
            g.add((this_sample, SOSA.isSampleOf, domain_feature))  # associate

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

        if self.date_acquired is None:
            d = ''
        else:
            d = self.date_acquired
        template = render_template(
            'sample_dc.xml',
            identifier=self.igsn,
            description=self.remark,
            date=d,
            type=self.sample_type,
            format=self.material_type,
            wkt=self._generate_sample_wkt(),
            creator='Geoscience Australia ({})'.format(Sample.URI_GA),
            publisher='Geoscience Australia ({})'.format(Sample.URI_GA),
        )

        return template

    def export_igsn_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """

        # acquired date fudge
        if self.date_acquired is not None:
            collection_time = datetime_to_datestamp(self.date_acquired)
        else:
            collection_time = '1900-01-01T00:00:00Z'



        template = render_template(
            'sample_igsn.xml',
            igsn=self.igsn,
            sample_id=self.sample_id,
            description=self.remark,
            wkt=self._generate_sample_wkt(),
            sample_type=self.sample_type,
            material_type=self.material_type,
            collection_method=self.method_type,
            collection_time=collection_time
        )

        return template

    def export_igsn_r1_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN XML Schema

        :return: XML string
        """
        template = render_template(
            'sample_igsn_r1.xml',
            igsn=self.igsn,
            sample_id=self.sample_id,
            description=self.remark,
            wkt=self._generate_sample_wkt(),
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
            wkt=self._generate_sample_wkt(),
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
                description=self.remark if self.remark != '' else '-',
                date_acquired=self.date_acquired if self.date_acquired is not None else '<a href="{}">{}</a>'.format(Sample.URI_MISSSING, Sample.URI_MISSSING.split('/')[-1]),
                sample_type=self.sample_type,
                wkt=self._generate_sample_wkt(),
                sampling_feature=self.entity_type,
                method_type=self.method_type,
                material_type=self.material_type
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
        else:  # elif model_view == 'dc':
            view_title = 'Dublin Core view'

            sample_table_html = render_template(
                'sample_dc.html',
                identifier=self.igsn,
                description=self.remark if self.remark != '' else '-',
                date=self.date_acquired if self.date_acquired is not None else '<a href="{}">{}</a>'.format(
                    Sample.URI_MISSSING, Sample.URI_MISSSING.split('/')[-1]),
                type=self.sample_type,
                format=self.material_type,
                wkt=self._generate_sample_wkt(),
                creator='<a href="{}">Geoscience Australia</a>'.format(Sample.URI_GA),
                publisher='<a href="{}">Geoscience Australia</a>'.format(Sample.URI_GA),
            )

        if self.date_acquired is not None:
            year_acquired = '({})'.format(datetime.datetime.strftime(self.date_acquired, '%Y'))
        else:
            year_acquired = ''

        # add in the Pingback header links as they are valid for all HTML views
        pingback_uri = _config.BASE_URI_SAMPLE + self.igsn + "/pingback"
        headers = {
            'Link': '<{}>;rel = "http://www.w3.org/ns/prov#pingback"'.format(pingback_uri)
        }

        return Response(
            render_template(
                'page_sample.html',
                view=model_view,
                igsn=self.igsn,
                year_acquired=year_acquired,
                view_title=view_title,
                sample_table_html=sample_table_html,
                date_now=datetime.datetime.now().strftime('%d %B %Y'),
                system_url='http://54.66.133.7'
            ),
            headers=headers
        )


class ParameterError(ValueError):
    pass


if __name__ == '__main__':
    s = Sample(None, xml='c:/work/samples-api/test/static_data/AU239.xml')
    # print s.igsn
    # print s.sample_id
    # print 'sample_type ' + s.sample_type
    # print 'method_type ' + s.method_type
    # print 'material_type ' + s.material_type
    # # print 'long_min ' + s.long_min
    # # print 'long_max ' + s.long_max
    # # print 'lat_min ' + s.lat_min
    # # print 'lat_max ' + s.lat_max
    # print 'gtype ' + str(s.gtype)
    # print 'srid ' + str(s.srid)
    # print 'x ' + str(s.x)
    # print 'y ' + str(s.y)
    # print 'z ' + str(s.z)
    # print 'elem_info ' + s.elem_info
    # print 'ordinates ' + s.ordinates
    # print 'state ' + s.state
    # print 'country ' + s.country
    # print 'depth_top ' + str(s.depth_top)
    # print 'depth_base ' + str(s.depth_base)
    # print 'strath ' + s.strath
    # print 'age ' + s.age
    # print 'remark ' + s.remark
    # print 'lith ' + s.lith
    # print 'date_acquired ' + s.date_acquired.isoformat()
    # print 'entity_uri ' + s.entity_uri
    # print 'entity_name ' + s.entity_name
    # print 'entity_type ' + s.entity_type
    # print 'hole_long_min ' + str(s.hole_long_min)
    # print 'hole_long_max ' + str(s.hole_long_max)
    # print 'hole_lat_min ' + str(s.hole_lat_min)
    # print 'hole_lat_max ' + str(s.hole_lat_max)
    # print 'sample_no ' + str(s.sample_no)
    # print s.export_dc_xml()

    # s = Sample('http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSample?pIGSN={0}', 'AU239')
    # print s.igsn

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()

    from model.lookups import TERM_LOOKUP

    print(TERM_LOOKUP['sample_type']['unknown'])

    print(TERM_LOOKUP['method_type']['Unknown'])

    print(TERM_LOOKUP['material_type']['unknown'])
