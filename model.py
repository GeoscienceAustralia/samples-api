from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode


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
            'AUS': 'http://www.geonames.org/2077456/australia.html'
        },
        'lith': {
            'one': 'ONE',
            'two': 'TWO',
        },
        'entity_type': {
            'BOTEHOLE': 'borehole',
            'two': 'TWO',
        }
    }

    '''

    '''

    def __init__(self):
        pass

    def populate_from_oracle_api(self):
        """
        Populates this instance with data from the Oracle Samples table API
        :return: None
        """
        # call API
        # request.get
        pass

    def populate_from_xml_file(self, xml_file):
        """
        Populates this instance with data from an XML file.

        This is mainly a testing function.

        :param xml_file:
        :return: None
        """
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
                self.sample_type = Sample.TERM_LOOKUP['sample_type'].get(elem.text),
            elif elem.tag == "SAMPLING_METHOD":
                self.method_type = Sample.TERM_LOOKUP['method_type'].get(elem.text),
            elif elem.tag == "MATERIAL_CLASS":
                self.material_type = Sample.TERM_LOOKUP['material_type'].get(elem.text),
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
                self.state = Sample.TERM_LOOKUP['state'].get(elem.text),
            elif elem.tag == "COUNTRY":
                self.country = Sample.TERM_LOOKUP['country'].get(elem.text),
            elif elem.tag == "TOP_DEPTH":
                self.depth_top = elem.text
            elif elem.tag == "BASE_DEPTH":
                self.depth_base = elem.text
            elif elem.tag == "STRATNAME":
                self.strath = elem.text
            elif elem.tag == "AGE":
                self.age = elem.text
            elif elem.tag == "REMARK":
                self.remark = elem.text
            elif elem.tag == "LITHNAME":
                self.lith = elem.text
            elif elem.tag == "ACQUIREDATE":
                self.date_aquire = elem.text
            elif elem.tag == "ENTITY_TYPE":
                self.entity_type = elem.text
            elif elem.tag == "ENTITYID":
                self.entity_id = elem.text
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
            elif elem.tag == "ENO":
                self.entity_no = elem.text

        return True

    def export_as_rdf(self, model_view='default', format='turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view: string of one of the model view names available for Sample objects ['igsn', 'dc', '',
            'default']
        :param format: string of one of the rdflib serlialization format ['n3', 'nquads', 'nt', 'pretty-xml', 'trig',
            'trix', 'turtle', 'xml'], from http://rdflib3.readthedocs.io/en/latest/plugin_serializers.html
        :return: RDF string
        """

        g = Graph()
        # declare namespaces
        PROV = Namespace('http://www.w3.org/ns/prov#')
        DCT = Namespace('http://purl.org/dc/elements/1.1/')
        SAM = Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
        GEOSP = Namespace('http://www.opengis.net/ont/geosparql#')
        SF = Namespace('http://www.opengis.net/ont/sf#')
        IGSN = Namespace('http://pig.geoscience.gov.au/def/igsn')

        # TODO: match the triples generator code to the example
        # make the sample URI
        base_uri = 'http://pid.geoscience.gov.au/sample/'
        this_sample = URIRef(base_uri + self.igsn)

        # make the triples
        g.add((this_sample, RDF.type, SAM.Specimen))

        # location = BNode()
        # g.add((this_sample, SAM.currentLocation, location))
        # location = GA Services building
        elevation = BNode()
        g.add((elevation, RDF.type, SAM.Elevation))
        g.add((this_sample, SAM.samplingElevation, elevation))
        g.add((elevation, SAM.elevation, Literal(self.z, datatype=XSD.float)))
        g.add((elevation, SAM.verticalDatum, Literal("GDA94", datatype=XSD.string)))

        g.add((this_sample, RDF.type, GEOSP.Feature))
        g.add((this_sample, RDF.type, PROV.Entity))
        g.add((this_sample, DCT.identifier, Literal(self.igsn)))
        point = BNode()
        g.add((this_sample, GEOSP.hasGeometry, point))
        g.add((point, RDF.type, SF.Point))
        if self.z is not None:
            # wkt = "SRID=" + self.srid + ";POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            wkt = "<http://www.opengis.net/def/crs/EPSG/0/" + self.srid + "> POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            gml = '<gml:Point srsDimension="3" srsName="http://www.opengis.net/def/crs/EPSG/0/' + self.srid + '">'\
                    '<gml:pos>' + self.x + ' ' + self.y + ' ' + self.z + '</gml:pos>'\
                  '</gml:Point>'
        else:
            # wkt = "SRID=" + self.srid + ";POINT(" + self.x + " " + self.y + ")"
            wkt = "<http://www.opengis.net/def/crs/EPSG/0/" + self.srid + "> POINT(" + self.x + " " + self.y + ")"
            gml = '<gml:Point srsDimension="2" srsName="http://www.opengis.net/def/crs/EPSG/0/' + self.srid + '">'\
                    '<gml:pos>' + self.x + ' ' + self.y + '</gml:pos>'\
                  '</gml:Point>'

        g.add((point, GEOSP.asWKT, Literal(wkt, datatype=GEOSP.wktLiteral)))
        g.add((point, GEOSP.asGML, Literal(gml, datatype=GEOSP.gmlLiteral)))

        #g.add((this_sample, RDFS.label, Literal('Sample', datatype=XSD.string)))

        # TODO: implement a lookup table for each of the items in the GA DB that must be vocab terms in the IGSN vocab
        # TODO: implement a fake vocab for sampling feature type BOREHOLE, SURVEY, PIPELINE)
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingPoint
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#Location
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#materialClass
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#samplingMethod
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#samplingTime
        #http://def.seegrid.csiro.au/ontology/om/sam-lite#SpatialSamplingFeature hostedProcedure ObservationProcess
        #http://def.seegrid.csiro.au/isotc211/iso19156/2011/sampling#specimenType

        #sam:Specimen sam:currentLocation sam:Location
        #geosp:Geomtry geosp.asWKT ...
        #http://def.seegrid.csiro.au/isotc211/iso19156/2011/sampling#Specimen

        # prefix gm: http://def.seegrid.csiro.au/isotc211/iso19107/2003/geometry#
        #gm:Object
        #   gm:Primitive
        #      gm:Point

        #geo:lat
        #geo:long


        #this_sample gm:position gm:Position
        #gm:Position gm:coordinates ?
        #gm:Position gm:srs 8311

        #http://ijsdir.jrc.ec.europa.eu/index.php/ijsdir/article/view/351/359

        #
        #   try thsi sample via Stirling's API: AU239
        #


        #
        # WKT example from Kolas2013
        # "<http://www.opengis.net/def/crs/EPSG/0/8311> Point(-83.38 33.95)"^^geo:wktLiteral
        #
        '''
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix geo: <http://www.opengis.net/ont/geosparql#> .
        @prefix ex: <http://www.example.org/POI#> .
        @prefix sf: <http://www.opengis.net/ont/sf#> .

        ex:WashingtonMonument a ex:Monument;
        rdfs:label "Washington Monument";
        geo:hasGeometry [
            a sf:Point;
            geo:asWKT "POINT(-77.03524 38.889468)"^^geo:wktLiteral.
        ]
        '''

        return g.serialize(format='nt')

    def export_as_igsn_xml(self):
        """
        Exports this Sample instance in XML that validates against the IGSN Descriptive Metadata schema from
        https://github.com/IGSN/metadata/tree/dev/description

        :return: XML string
        """



if __name__ == '__main__':
    s = Sample()
    s.populate_from_xml_file('test/sample_eg1.xml')
    #print s.export_as_rdf()

