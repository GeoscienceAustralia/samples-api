from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode


class Sample:
    def __init__:
        pass

    def populate_from_oracle_api(self):
        """
        Populates this instance with data from the Oracle Samples table API
        :return: None
        """
        pass

    def populate_from_xml_file(self, xml_file):
        """
        Populates this instance with data from an XML file.

        This is mainly a testing function.

        :param xml_file:
        :return: None
        """
        root = etree.parse(xml_file)
        self.igsn = root.xpath('//ROW/IGSN/text()')[0]
        self.sample_id = root.xpath('//ROW/SAMPLEID/text()')[0]
        self.x = root.xpath('//ROW/GEOM/SDO_POINT/X/text()')[0]
        self.y = root.xpath('//ROW/GEOM/SDO_POINT/Y/text()')[0]
        self.z = root.xpath('//ROW/GEOM/SDO_POINT/Z/text()')[0]
        self.gtype = root.xpath('//ROW/GEOM/SDO_GTYPE/text()')[0]
        self.srid = root.xpath('//ROW/GEOM/SDO_SRID/text()')[0]

        self.state = root.xpath('//ROW/STATEID/text()')[0]
        self.country = root.xpath('//ROW/COUNTRY/text()')[0]

        #self.date = root.xpath('//ROW/LOADEDDATE/text()')[0]

        return etree.tostring(root)

    def export_as_rdf(self, model_view, format='turtle'):
        """
        Exports this instance in RDF, according to a given model from the list of supported models,
        in a given rdflib RDF format

        :param model_view:
        :param format:
        :return:
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


if __name__ == '__main__':
    i = IGSN()
    i.readFromOracleXml('sample_eg1.xml')
    print i.createRdfGraph()

