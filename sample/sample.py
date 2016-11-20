from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode
from datetime import datetime
from StringIO import StringIO



class Sample:
    """
    Sample class
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
    TERM_LOOKUP = {
        'access': {
            'Public': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Public',
            'Private': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Private'
        },
        'sample_type': {
            'automated':            'http://vocabulary.odm2.org/specimentype/automated/',
            'core':                 'http://vocabulary.odm2.org/specimentype/core/',
            'coreHalfRound':        'http://vocabulary.odm2.org/specimentype/coreHalfRound/',
            'corePiece':            'http://vocabulary.odm2.org/specimentype/corePiece/',
            'coreQuarterRound':     'http://vocabulary.odm2.org/specimentype/coreQuarterRound/',
            'coreSection':          'http://vocabulary.odm2.org/specimentype/coreSection/',
            'coreSectionHalf':      'http://vocabulary.odm2.org/specimentype/coreSectionHalf/',
            'coreSub-Piece':        'http://vocabulary.odm2.org/specimentype/coreSub-Piece/',
            'coreWholeRound':       'http://vocabulary.odm2.org/specimentype/coreWholeRound/',
            'cuttings':             'http://vocabulary.odm2.org/specimentype/cuttings/',
            'dredge':               'http://vocabulary.odm2.org/specimentype/dredge/',
            'foliageDigestion':     'http://vocabulary.odm2.org/specimentype/foliageDigestion/',
            'foliageLeaching':      'http://vocabulary.odm2.org/specimentype/foliageLeaching/',
            'forestFloorDigestion': 'http://vocabulary.odm2.org/specimentype/forestFloorDigestion/',
            'grab':                 'http://vocabulary.odm2.org/specimentype/grab/',
            'individualSample':     'http://vocabulary.odm2.org/specimentype/individualSample/',
            'litterFallDigestion':  'http://vocabulary.odm2.org/specimentype/litterFallDigestion/',
            'orientedCore':         'http://vocabulary.odm2.org/specimentype/orientedCore/',
            'other':                'http://vocabulary.odm2.org/specimentype/other/',
            'petriDishDryDeposition': 'http://vocabulary.odm2.org/specimentype/petriDishDryDeposition/',
            'precipitationBulk':    'http://vocabulary.odm2.org/specimentype/precipitationBulk/',
            'rockPowder':           'http://vocabulary.odm2.org/specimentype/rockPowder/',
            'standardReferenceSpecimen': 'http://vocabulary.odm2.org/specimentype/standardReferenceSpecimen/',
            'terrestrialSection':   'http://vocabulary.odm2.org/specimentype/terrestrialSection/',
            'thinSection':          'http://vocabulary.odm2.org/specimentype/thinSection/',
            'unknown':              'http://vocabulary.odm2.org/specimentype/unknown/'
        },
        'method_type': {
            'Auger':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Auger',
            'Blast':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Blast',
            'Box':          'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Box',
            'ChainBag':     'http://pid.geoscience.gov.au/def/voc/igsn-codelists/ChainBag',
            'Corer':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Corer',
            'Dredge':       'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Dredge',
            'Drill':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Drill',
            'FreeFall':     'http://pid.geoscience.gov.au/def/voc/igsn-codelists/FreeFall',
            'Grab':         'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Grab',
            'Gravity':      'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Gravity',
            'GravityGiant': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/GravityGiant',
            'Hammer':       'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Hammer',
            'Hand':         'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Hand',
            'Kastenlot':    'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Kastenlot',
            'Knife':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Knife',
            'MOCNESS':      'http://pid.geoscience.gov.au/def/voc/igsn-codelists/MOCNESS',
            'Multi':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Multi',
            'Net':          'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Net',
            'OtherMethod':  'http://pid.geoscience.gov.au/def/voc/igsn-codelists/OtherMethod',
            'Piston':       'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Piston',
            'PistonGiant':  'http://pid.geoscience.gov.au/def/voc/igsn-codelists/PistonGiant',
            'Probe':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Probe',
            'Rock':         'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Rock',
            'Scallop':      'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Scallop',
            'Scoop':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Scoop',
            'SideSaddle':   'http://pid.geoscience.gov.au/def/voc/igsn-codelists/SideSaddle',
            'Trap':         'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Trap',
            'Trawl':        'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Trawl',
            'TriggerWeight': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/TriggerWeight',
            'UnknownMethod': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/UnknownMethod',
            'Vibrating':    'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Vibrating'
        },
        'material_type': {
            'air':          'http://vocabulary.odm2.org/medium/air/',
            'gas':          'http://vocabulary.odm2.org/medium/gas/',
            'ice':          'http://vocabulary.odm2.org/medium/ice/',
            'liquidAqueous': 'http://vocabulary.odm2.org/medium/liquidAqueous/',
            'liquidOrganic': 'http://vocabulary.odm2.org/medium/liquidOrganic/',
            'mineral':      'http://vocabulary.odm2.org/medium/mineral/',
            'organism':     'http://vocabulary.odm2.org/medium/organism/',
            'other':        'http://vocabulary.odm2.org/medium/other/',
            'particulate':  'http://vocabulary.odm2.org/medium/particulate/',
            'rock':         'http://vocabulary.odm2.org/medium/rock/',
            'sediment':     'http://vocabulary.odm2.org/medium/sediment/',
            'snow':         'http://vocabulary.odm2.org/medium/snow/',
            'soil':         'http://vocabulary.odm2.org/medium/soil/',
            'tissue':       'http://vocabulary.odm2.org/medium/tissue/',
            'unknown':      'http://vocabulary.odm2.org/medium/unknown/'
        },
        'state': {
            'ACT':  'http://www.geonames.org/2177478/',
            'NT':   'http://www.geonames.org/2064513/',
            'NSW':  'http://sws.geonames.org/2155400/',
            'QLD':  'http://www.geonames.org/2152274/',
            'SA':   'http://www.geonames.org/2061327/',
            'TAS':  'http://www.geonames.org/2147291/',
            'VIC':  'http://www.geonames.org/2145234/',
            'WA':   'http://www.geonames.org/2058645/'
        },
        'country': {
            'AUS': 'http://www.geonames.org/2077456/'
        },
        'lith': {
            'one': 'ONE',
            'two': 'TWO',
        },
        'entity_type': {
            'BOREHOLE': 'http://vocabulary.odm2.org/samplingfeaturetype/borehole/',
            'FIELD SITE': 'http://vocabulary.odm2.org/samplingfeaturetype/site/',
        }
    }

    # Associates an RDF mimetype to an rdflib RDF format
    RDF_MIMETYPES = {
        'text/turtle': 'turtle',
        'text/ntriples': 'nt',
        'text/nt': 'nt',
        'text/n3': 'nt',
        'application/rdf+xml': 'xml',
        'application/rdf+json': 'json-ld'
    }
    '''
    Entity Types not yet in a vocab

    ACREAGE RELEASE
    COUNTRY
    DRILLHOLE
    EMITTER
    ESSCI
    ESTUARY
    EXPLORATION PERMIT
    FACIES
    FIELD SITE
    MAPSHEET
    MARSEGMENT
    MINERAL DEPOSIT
    MINERAL PROJECT
    MINERALISED ZONE
    OBSERVATORY
    PIPELINE
    PLACE NAME
    POLITICAL REGION
    PORT
    POWER STATION
    PRODUCTION LICENCE
    PROJECT
    PROVINCE
    RESOURCE PROCESSING PLANT
    RESOURCE PROJECT
    RETENTION LEASE
    SECTION
    SEISMICLINE
    STATE
    SURVEY
    WELL
    WILDCAT LOCATION
    '''

    def __init__(self):
        self.igsn = None
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
        self.entity_type = None
        self.date_aquired = None
        self.entity_uri = None
        self.entity_name = None
        self.entity_type = None
        self.hole_long_min = None
        self.hole_long_max = None
        self.hole_lat_min = None
        self.hole_lat_max = None
        self.date_load = None
        self.sample_no = None

    def populate_from_oracle_api(self):
        """
        Populates this instance with data from the Oracle Samples table API

        :return: None
        """
        # call API
        # r = request.get(...)
        # xml = r.content # check the mimetype
        # call populate_from_xml_file(StringIO(r.content))
        pass

    def populate_from_xml_file(self, xml_file):
        """
        Populates this instance with data from an XML file.

        :param xml_file:
        :return: None
        """
        # iterate through the elements in the XML element tree and handle each
        for event, elem in etree.iterparse(xml_file):
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
                self.sample_type = Sample.TERM_LOOKUP['sample_type'].get(elem.text)
            elif elem.tag == "SAMPLING_METHOD":
                self.method_type = Sample.TERM_LOOKUP['method_type'].get(elem.text)
            elif elem.tag == "MATERIAL_CLASS":
                if elem.text:
                    self.material_type = Sample.TERM_LOOKUP['material_type'].get(elem.text)
            elif elem.tag == "SAMPLE_MIN_LONGITUDE":
                self.long_min = elem.text
            elif elem.tag == "SAMPLE_MAX_LONGITUDE":
                self.long_max = elem.text
            elif elem.tag == "SAMPLE_MIN_LATITUDE":
                self.lat_min = elem.text
            elif elem.tag == "SAMPLE_MAX_LATITUDE":
                self.lat_max = elem.text
            elif elem.tag == "SDO_GTYPE":
                self.gtype = elem.text
            elif elem.tag == "SDO_SRID":
                self.srid = elem.text
            elif elem.tag == "X":
                self.x = elem.text
            elif elem.tag == "Y":
                self.y = elem.text
            elif elem.tag == "Z":
                self.z = elem.text
            elif elem.tag == "SDO_ELEM_INFO":
                self.elem_info = elem.text
            elif elem.tag == "SDO_ORDINATES":
                self.ordinates = elem.text
            elif elem.tag == "STATEID":
                self.state = Sample.TERM_LOOKUP['state'].get(elem.text)
            elif elem.tag == "COUNTRY":
                self.country = Sample.TERM_LOOKUP['country'].get(elem.text)
            elif elem.tag == "TOP_DEPTH":
                self.depth_top = elem.text
            elif elem.tag == "BASE_DEPTH":
                self.depth_base = elem.text
            elif elem.tag == "STRATNAME":
                self.strath = elem.text
            elif elem.tag == "AGE":
                self.age = elem.text
            elif elem.tag == "REMARK":
                if elem.text:
                    self.remark = elem.text
            elif elem.tag == "LITHNAME":
                self.lith = elem.text
            elif elem.tag == "ACQUIREDATE":
                if elem.text:
                    self.date_aquired = datetime.strptime(elem.text, '%d-%b-%y')
            elif elem.tag == "ENO":
                self.entity_uri = 'http://pid.geoscience.gov.au/site/' + elem.text
            elif elem.tag == "ENTITYID":
                self.entity_name = elem.text
            elif elem.tag == "ENTITY_TYPE":
                self.entity_type = elem.text
            elif elem.tag == "HOLE_MIN_LONGITUDE":
                self.hole_long_min = elem.text
            elif elem.tag == "HOLE_MAX_LONGITUDE":
                self.hole_long_max = elem.text
            elif elem.tag == "HOLE_MIN_LATITUDE":
                self.hole_lat_min = elem.text
            elif elem.tag == "HOLE_MAX_LATITUDE":
                self.hole_lat_max = elem.text
            elif elem.tag == "LOADEDDATE":
                self.date_load = elem.text
            elif elem.tag == "SAMPLENO":
                self.sample_no = elem.text

        return True

    def generate_sample_wkt(self):
        if self.z is not None:
            # wkt = "SRID=" + self.srid + ";POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            wkt = "<http://www.opengis.net/def/crs/EPSG/0/" + self.srid + "> POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
        else:
            # wkt = "SRID=" + self.srid + ";POINT(" + self.x + " " + self.y + ")"
            wkt = "<http://www.opengis.net/def/crs/EPSG/0/" + self.srid + "> POINT(" + self.x + " " + self.y + ")"

        return wkt

    def generate_sample_gml(self):
        if self.z is not None:
            gml = '<gml:Point srsDimension="3" srsName="http://www.opengis.net/def/crs/EPSG/0/' + self.srid + '">'\
                    '<gml:pos>' + self.x + ' ' + self.y + ' ' + self.z + '</gml:pos>'\
                  '</gml:Point>'
        else:
            gml = '<gml:Point srsDimension="2" srsName="http://www.opengis.net/def/crs/EPSG/0/' + self.srid + '">'\
                    '<gml:pos>' + self.x + ' ' + self.y + '</gml:pos>'\
                  '</gml:Point>'

        return gml

    def generate_parent_wkt(self):
        # TODO: add support for geometries other than Point
        wkt = "<http://www.opengis.net/def/crs/EPSG/0/" + self.srid + "> POINT(" + self.hole_long_min + " " + self.hole_lat_min + ")"

        return wkt

    def generate_parent_gml(self):
        # TODO: add support for geometries other than Point
        gml = '<gml:Point srsDimension="2" srsName="http://www.opengis.net/def/crs/EPSG/0/' + self.srid + '">' \
              ' <gml:pos>' + self.hole_long_min + ' ' + self.hole_lat_min + '</gml:pos>' \
              '</gml:Point>'
        return gml

    def export_as_rdf(self, model_view='default', rdf_mime='text/turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
            'default']
        :param format: string of one of the rdflib serlialization format ['n3', 'nquads', 'nt', 'pretty-xml', 'trig',
            'trix', 'turtle', 'xml'], from http://rdflib3.readthedocs.io/en/latest/plugin_serializers.html
        :return: RDF string
        """

        # things that are applicable to all model views; the graph and some namespaces
        g = Graph()
        # DC = Namespace('http://purl.org/dc/elements/1.1/')
        DCT = Namespace('http://purl.org/dc/terms/')
        g.bind('dct', DCT)
        SAM = Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
        g.bind('sam', SAM)
        GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')
        g.bind('geosp', GEOSP)
        OM = Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
        g.bind('om', OM)
        AUROLE = Namespace('http://communications.data.gov.au/def/role/')
        g.bind('aurole', AUROLE)

        # URI for this sample
        base_uri = 'http://pid.geoscience.gov.au/sample/'
        this_sample = URIRef(base_uri + self.igsn)

        # define GA
        ga = URIRef('http://pid.geoscience.gov.au/org/ga')

        # sample location in GML & WKT, formulation from GeoSPARQL
        wkt = Literal(self.generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self.generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        # select model view
        if model_view == 'default' or model_view == 'igsn' or model_view is None:
            # default model is the IGSN model

            # IGSN model required namespaces
            PROV = Namespace('http://www.w3.org/ns/prov#')
            g.bind('prov', PROV)
            SF = Namespace('http://www.opengis.net/ont/sf#')
            g.bind('sf', SF)
            IGSN = Namespace('http://pid.geoscience.gov.au/def/ont/igsn#')
            g.bind('igsn', IGSN)

            # classing the sample
            g.add((this_sample, RDF.type, SAM.Specimen))
            g.add((this_sample, RDF.type, PROV.Entity))

            # linking the sample and the RDF document
            #g.add((this_sample, FOAF.isPrimaryTopicOf, PROV.Entity))

            '''
            dc:identifier [
                a igsn:AlternateIdentifier;
                igsn:identifierType <http://pid.geoscience.gov.au/def/voc/igsn-codelists/IGSN>; #skos:Concept;
                prov:value "IGSN"^^xsd:string;
            ];
            '''
            alternate_identifier = BNode()
            g.add((this_sample, DCT.identifier, alternate_identifier))
            g.add((alternate_identifier, RDF.type, IGSN.AlternateIdentifier))
            g.add((alternate_identifier, IGSN.identifierType, URIRef('http://pid.geoscience.gov.au/def/voc/igsn-codelists/IGSN')))
            g.add((alternate_identifier, PROV.value, Literal(self.igsn, datatype=XSD.string)))

            '''
            geo:hasGeometry [
                a sf:Point; # or Line
                geo:asGML "<gml:Point srsDimension="3" srsName="http://www.opengis.net/def/crs/EPSG/0/4326"><gml:pos>49.40 -123.26</gml:pos></gml:Point>"^^geosp:gmlLiteral
                geo:asWKT "<http://www.opengis.net/def/crs/EPSG/0/8311> POINTZ(144.2409874717 -18.1739861699)"^^geosp:wktLiteral
            ];
            '''
            geometry = BNode()
            g.add((this_sample, GEOSP.hasGeometry, geometry))
            g.add((geometry, RDF.type, SF.Point))
            g.add((geometry, GEOSP.asGML, gml))
            g.add((geometry, GEOSP.asWKT, wkt))

            '''
            sam:samplingElevation [
                a sam:Elevation;
                sam:elevation 34.6;
                sam:verticalDatum <http://www.opengis.net/def/crs/EPSG/0/xxxx>;
            ];
            '''
            elevation = BNode()
            g.add((this_sample, SAM.samplingElevation, elevation))
            g.add((elevation, RDF.type, SAM.Elevation))
            g.add((elevation, SAM.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((elevation, SAM.verticalDatum, Literal("GDA94", datatype=XSD.string)))

            '''
            sam:currentLocation "some note"^^xsd:string;
            sam:materialClass <http://vocabulary.odm2.org/medium/rock/>;
            sam:samplingMethod skos:Concept; (methodType) http://pid.geoscience.gov.au/def/voc/igsn-codelists/Drill
            #sam:specimenType skos:Concept;
            sam:samplingTime ""^^xsd:datetime;
            dct:accessRights skos:Concept #http://pid.geoscience.gov.au/def/voc/igsn-codelists/Private
            obs:featureOfInterest <parent_uri>;
            '''
            g.add((this_sample, SAM.currentLocation, Literal('GA Services building', datatype=XSD.string)))
            if self.material_type is not None:
                g.add((this_sample, SAM.materialClass, URIRef(self.material_type)))
            if self.method_type is not None:
                g.add((this_sample, SAM.samplingMethod, URIRef(self.method_type)))
            if self.date_aquired is not None:
                g.add((this_sample, SAM.samplingTime, Literal(self.date_aquired, datatype=datetime)))
            # TODO: represent Public/Private (and other?) access methods in DB, add to terms in vocab?
            g.add((this_sample, DCT.accessRights, URIRef(Sample.TERM_LOOKUP['access']['Public'])))
            # TODO: make a register of Entities
            this_parent = URIRef(self.entity_uri)
            g.add((this_sample, OM.featureOfInterest, this_parent))

            '''
            <parent_uri> a geo:Feature;
                #xxx:gaFeatureType skos:Concept; # we limit this to our voc (parent feature type from Entity Types: BOREHOLE, SURVEY, PIPELINE -- these should be in a vocab)
                #igsn:featureType (http://52.63.163.95/ga/sissvoc/ga-igsn-code-lists/resource?uri=http://pid.geoscience.gov.au/def/voc/igsn-codelists/featureType)
                geo:hasGeometry [
                    a sf:Point; # or anything (Line, Polygon, combo)
                    geo:asGML "<gml:Point srsDimension="3" srsName="http://www.opengis.net/def/crs/EPSG/0/4326"><gml:pos>49.40 -123.26</gml:pos></gml:Point>"^^geosp:gmlLiteral
                    geo:asWKT "<http://www.opengis.net/def/crs/EPSG/0/8311> POINTZ(144.2409874717 -18.1739861699)"^^geosp:wktLiteral
                ]
                sam:samplingElevation [
                    sam:elevation 34.6;
                    sam:verticalDatum <http://www.opengis.net/def/crs/EPSG/0/xxxx>;
                ]
            '''
            fake_entity_type_uri = 'http://pid.geoscience.gov.au/def/voc/sites/' + self.entity_type.title()
            g.add((this_parent, IGSN.featureType, URIRef(fake_entity_type_uri)))  # TODO: sort out the parent type, both the predicate used and the value (need a vocab)

            parent_geometry = BNode()
            g.add((this_parent, GEOSP.hasGeometry, parent_geometry))
            g.add((parent_geometry, RDF.type, SF.Point))  # TODO: extend this for other geometry types
            g.add((parent_geometry, GEOSP.asWKT, Literal(self.generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
            g.add((parent_geometry, GEOSP.asGML, Literal(self.generate_parent_gml(), datatype=GEOSP.wktLiteral)))

            parent_elevation = BNode()
            g.add((this_parent, SAM.samplingElevation, parent_elevation))
            g.add((parent_elevation, RDF.type, SAM.Elevation))
            g.add((parent_elevation, SAM.elevation, Literal(self.z, datatype=XSD.float)))
            g.add((parent_elevation, SAM.verticalDatum, Literal("GDA94", datatype=XSD.string)))

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
            if self.date_aquired is not None:
                g.add((this_sample, DCT.date, Literal(self.date_aquired.isoformat(), datatype=XSD.date)))
            if self.remark is not None:
                g.add((this_sample, DCT.description, self.remark))
            if self.material_type is not None:
                g.add((this_sample, DCT.format, URIRef(self.material_type)))
            g.add((this_sample, DCT.identifier, Literal('igsn:' + self.igsn, datatype=XSD.string)))
            # define GA as a dct:Agent
            g.add((ga, RDF.type, DCT.Agent))
            g.add((this_sample, DCT.publisher, ga))
            # g.add((this_sample, DCT.relation, ga)) -- no value yet in GA DB
            # g.add((this_sample, DCT.subject, ga)) -- how is this different to type?
            # g.add((this_sample, DCT.title, ga)) -- no value at GA
            if self.sample_type is not None:
                g.add((this_sample, DCT.type, URIRef(self.sample_type)))

        return g.serialize(format=Sample.RDF_MIMETYPES[rdf_mime])

    def is_xml_export_valid(self, xml_string):
        """
        Validate and export of this Sample instance in XML using the XSD files from the dev branch
        of the IGSN repo: https://github.com/IGSN/metadata/tree/dev/description. The actual XSD
        files used are in the xml-validation dir, commit be2f0f8d7ef78407c386d3c8a0aba7c31397aa29

        :param xml_string:
        :return: boolean
        """
        # load the schema
        xsd_doc = etree.parse(StringIO('xml-validation/resource.xsd'))
        xsd = etree.XMLSchema(xsd_doc)

        # load the XML doc
        xml = etree.parse(StringIO(xml_string))

        return xsd.validate(xml)

    def export_as_igsn_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN Descriptive Metadata schema from
        https://github.com/IGSN/metadata/tree/dev/description

        :return: XML string
        """


        '''
        SESAR XML example from: https://app.geosamples.org/webservices/display.php?igsn=LCZ7700AK

        <?xml version="1.0" encoding="UTF-8"?>
        <results>
            <qrcode_img_src>app.geosamples.org/barcode/image.php?igsn=LCZ7700AK&amp;sample_id=CDR4_100mesh</qrcode_img_src>
            <user_code>LCZ</user_code>
            <igsn>LCZ7700AK</igsn>
            <name>CDR4_100mesh</name>
            <sample_type>Individual Sample</sample_type>
            <parent_igsn>LCZ771200</parent_igsn>
            <publish_date>2015-07-01</publish_date>
            <material>Rock</material>
            <classification>Metamorphic</classification>
            <field_name>hornfels grade metavolcaniclastic</field_name>
            <description>ground with a mortar and pestle to pass through a 100 mesh (150um) sieve</description>
            <collection_method>Manual&amp;gt;Hammer</collection_method>
            <geological_unit>Fajardo Formation</geological_unit>
            <purpose>weathering study</purpose>
            <latitude>18.28657</latitude>
            <longitude>-65.77803</longitude>
            <country>Puerto Rico</country>
            <cruise_field_prgrm>Luquillo Critical Zone Observatory (CZO)</cruise_field_prgrm>
            <collector>Joe Orlando</collector>
            <collection_start_date>2011-01-13</collection_start_date>
            <collection_date_precision>day</collection_date_precision>
            <current_archive>Department of Geosciences, Penn State Unv</current_archive>
            <current_archive_contact>Susan L. Brantley</current_archive_contact>
            <parents>
                <parent>LCZ771200 CDR4</parent>
            </parents>
            <siblings>
                <sibling>LCZ7700AJ CDR4_sawcut</sibling>
                <sibling>LCZ7700AL CDR4_TS_30um</sibling>
                <sibling>LCZ7700AM CDR4_TS_150um</sibling>
            </siblings>
        </results>

        Example XML from
        http://www.iedadata.org/services/sesar_examplexml

    <samples>
        <sample>
            <sample_type>Dredge</sample_type>
            <igsn>R05333444</igsn>
            <user_code>R05</user_code>
            <name>Primary name of sample</name>
            <sample_other_name>Another name by which the sample is known</sample_other_name>
            <parent_igsn>R05000001</parent_igsn>
            <parent_sample_type>Core</parent_sample_type>
            <parent_name>Rebeccas Original Core</parent_name>
            <is_private>1</is_private>
            <publish_date>05/22/2011</publish_date>
            <material>Rock</material>
            <classification>Igneous>Plutonic>Exotic</classification>
            <field_name>Name of field, ie. Basalt</field_name>
            <description>description of sample</description>
            <age_min>10.02</age_min>
            <age_max>10.02</age_max>
            <age_unit>Million Years (Ma)</age_unit>
            <geological_age>10.02</geological_age>
            <geological_unit></geological_unit>
            <collection_method></collection_method>
            <collection_method_descr></collection_method_descr>
            <size>10.02</size>
            <size_unit>cm</size_unit>
            <sample_comment></sample_comment>
            <latitude>10.02</latitude>
            <longitude>10.02</longitude>
            <latitude_end>10.02</latitude_end>
            <longitude_end>10.02</longitude_end>
            <elevation>10.02</elevation>
            <elevation_end>10.02</elevation_end>
            <primary_location_type>Ocean Ridge</primary_location_type>
            <primary_location_name>East Pacific Rise</primary_location_name>
            <location_description>ridge axis</location_description>
            <locality>21 North study area</locality>
            <locality_description></locality_description>
            <country>Name of country</country>
            <province>Name of province</province>
            <county>Name of county</county>
            <city>Name of city</city>
            <cruise_field_prgrm>Name of cruise field program ie HLY0805</cruise_field_prgrm>
            <platform_type>Icebreaker</platform_type>
            <platform_name>Name of platform ie USCGC Healy</platform_name>
            <platform_descr>Platform Description ie US Coast Guard Cutter</platform_descr>
            <collector>Collector / Chief Scientist name</collector>
            <collector_detail>Details of Collector</collector_detail>
            <collection_start_date></collection_start_date>
            <collection_start_time></collection_start_time>
            <collection_end_date></collection_end_date>
            <collection_end_time></collection_end_time>
            <collection_date_precision></collection_date_precision>
            <current_archive></current_archive>
            <current_archive_contact></current_archive_contact>
            <original_archive></original_archive>
            <original_archive_contact></original_archive_contact>
            <depth_min>10.2</depth_min>
            <depth_max>10.2</depth_max>
            <depth_scale>cm</depth_scale>
            <other_names>Another name by which this sample may be known</other_names>
            <other_names>Yet another name by which this sample may be known</other_names>
            <other_names>And yet another name by which this sample may be known</other_names>
        </sample>
    </samples>
        '''
        pass

    def export_as_html(self, model_view='default'):
        """
        Exports this instance in HTML, according to a given model from the list of supported models.

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
            'default']
        :return: HTML string
        """
        html =  '<style>' + \
                '   table.data {' +\
                '       border-collapse: collapse;' + \
                '       border: solid 2px black;' + \
                '   }' + \
                '   table.data tr, table.data th {' + \
                '       border: solid 1px black;' + \
                '       padding: 5px;' + \
                '   }' + \
                '</style>'

        html += '<table class="data">'
        html += '   <tr><th>Property</th><th>Value</th></tr>'
        if model_view == 'default' or model_view == 'igsn' or model_view is None:
            # TODO: complete the properties in this view
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            html += '   <tr><th>Sample ID</th><td>' + self.sampleid + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Sample Type</th><td>' + self.sample_type + '</td></tr>'

        elif model_view == 'dc':
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            html += '   <tr><th>Coverage</th><td>' + self.generate_sample_wkt() + '</td></tr>'
            if self.date_aquired is not None:
                html += '   <tr><th>Date</th><td>' + self.date_aquired.isoformat() + '</td></tr>'
            if self.remark is not None:
                html += '   <tr><th>Description</th><td>' + self.remark + '</td></tr>'
            if self.material_type is not None:
                html += '   <tr><th>Format</th><td>' + self.material_type + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Type</th><td>' + self.sample_type + '</td></tr>'

        html += '</table>'

        return html

if __name__ == '__main__':
    s = Sample()
    s.populate_from_xml_file('test/sample_eg1.xml')
    print s.export_as_rdf(rdf_mime='application/rdf+xml')

