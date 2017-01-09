from lxml import etree
from rdflib import Graph, URIRef, RDF, XSD, Namespace, Literal, BNode
from StringIO import StringIO
from lxml.builder import ElementMaker
from lxml.builder import E
import os
import requests
from renderers.datestamp import datetime_to_datestamp
from datetime import datetime
from ldapi import LDAPI


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
    TERM_LOOKUP = {
        'access': {
            'Public': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Public',
            'Private': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Private'
        },
        'sample_type': {
            'automated': 'http://vocabulary.odm2.org/specimentype/automated',
            'core': 'http://vocabulary.odm2.org/specimentype/core',
            'coreHalfRound': 'http://vocabulary.odm2.org/specimentype/coreHalfRound',
            'corePiece': 'http://vocabulary.odm2.org/specimentype/corePiece',
            'coreQuarterRound': 'http://vocabulary.odm2.org/specimentype/coreQuarterRound',
            'coreSection': 'http://vocabulary.odm2.org/specimentype/coreSection',
            'coreSectionHalf': 'http://vocabulary.odm2.org/specimentype/coreSectionHalf',
            'coreSub-Piece': 'http://vocabulary.odm2.org/specimentype/coreSub-Piece',
            'coreWholeRound': 'http://vocabulary.odm2.org/specimentype/coreWholeRound',
            'cuttings': 'http://vocabulary.odm2.org/specimentype/cuttings',
            'dredge': 'http://vocabulary.odm2.org/specimentype/dredge',
            'foliageDigestion': 'http://vocabulary.odm2.org/specimentype/foliageDigestion',
            'foliageLeaching': 'http://vocabulary.odm2.org/specimentype/foliageLeaching',
            'forestFloorDigestion': 'http://vocabulary.odm2.org/specimentype/forestFloorDigestion',
            'grab': 'http://vocabulary.odm2.org/specimentype/grab',
            'individualSample': 'http://vocabulary.odm2.org/specimentype/individualSample',
            'litterFallDigestion': 'http://vocabulary.odm2.org/specimentype/litterFallDigestion',
            'orientedCore': 'http://vocabulary.odm2.org/specimentype/orientedCore',
            'other': 'http://vocabulary.odm2.org/specimentype/other',
            'petriDishDryDeposition': 'http://vocabulary.odm2.org/specimentype/petriDishDryDeposition',
            'precipitationBulk': 'http://vocabulary.odm2.org/specimentype/precipitationBulk',
            'rockPowder': 'http://vocabulary.odm2.org/specimentype/rockPowder',
            'standardReferenceSpecimen': 'http://vocabulary.odm2.org/specimentype/standardReferenceSpecimen',
            'terrestrialSection': 'http://vocabulary.odm2.org/specimentype/terrestrialSection',
            'thinSection': 'http://vocabulary.odm2.org/specimentype/thinSection',
            'unknown': 'http://vocabulary.odm2.org/specimentype/unknown'
        },
        'method_type': {
            'Auger': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Auger',
            'Blast': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Blast',
            'Box': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Box',
            'ChainBag': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/ChainBag',
            'Corer': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Corer',
            'CoreDiamond': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/CoreDiamons',  # TODO: add this to vocab
            'Dredge': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Dredge',
            'Drill': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Drill',
            'FreeFall': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/FreeFall',
            'Grab': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Grab',
            'Gravity': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Gravity',
            'GravityGiant': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/GravityGiant',
            'Hammer': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Hammer',
            'Hand': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Hand',
            'Kastenlot': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Kastenlot',
            'Knife': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Knife',
            'MOCNESS': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/MOCNESS',
            'Multi': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Multi',
            'Net': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Net',
            'OtherMethod': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/OtherMethod',
            'Piston': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Piston',
            'PistonGiant': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/PistonGiant',
            'Probe': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Probe',
            'Rock': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Rock',
            'Scallop': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Scallop',
            'Scoop': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Scoop',
            'SideSaddle': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/SideSaddle',
            'trap': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Trap',
            'trawl': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Trawl',
            'triggerweight': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/TriggerWeight',
            'unknownmethod': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/UnknownMethod',
            'vibrating': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/Vibrating'
        },
        'material_type': {
            'AIR': 'http://vocabulary.odm2.org/medium/air',
            'GAS': 'http://vocabulary.odm2.org/medium/gas',
            'ICE': 'http://vocabulary.odm2.org/medium/ice',
            'liquidAqueous': 'http://vocabulary.odm2.org/medium/liquidAqueous',
            'liquidOrganic': 'http://vocabulary.odm2.org/medium/liquidOrganic',
            'mineral': 'http://vocabulary.odm2.org/medium/mineral',
            'organism': 'http://vocabulary.odm2.org/medium/organism',
            'other': 'http://vocabulary.odm2.org/medium/other',
            'particulate': 'http://vocabulary.odm2.org/medium/particulate',
            'rock': 'http://vocabulary.odm2.org/medium/rock',
            'sediment': 'http://vocabulary.odm2.org/medium/sediment',
            'snow': 'http://vocabulary.odm2.org/medium/snow',
            'soil': 'http://vocabulary.odm2.org/medium/soil',
            'tissue': 'http://vocabulary.odm2.org/medium/tissue',
            'unknown': 'http://vocabulary.odm2.org/medium/unknown'
        },
        'state': {
            'ACT': 'http://www.geonames.org/2177478',
            'NT': 'http://www.geonames.org/2064513',
            'NSW': 'http://sws.geonames.org/2155400',
            'QLD': 'http://www.geonames.org/2152274',
            'SA': 'http://www.geonames.org/2061327',
            'TAS': 'http://www.geonames.org/2147291',
            'VIC': 'http://www.geonames.org/2145234',
            'WA': 'http://www.geonames.org/2058645'
        },
        'country': {
            'AUS': 'http://www.geonames.org/2077456',
            'PNG': 'http://www.geonames.org/2088628',
            'ATA': 'http://www.geonames.org/6697173',
            'SLB': 'http://www.geonames.org/2103350',
            'FRA': 'http://www.geonames.org/3017382',
            'TMP': 'http://www.geonames.org/1966436',
            'BRA': 'http://www.geonames.org/3469034',
            'INW': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/INW',
            'GBR': 'http://www.geonames.org/2635167',
            'ZAF': 'http://www.geonames.org/953987',
            'USA': 'http://www.geonames.org/6252001',
            'NCL': 'http://www.geonames.org/2139685',
            'GRL': 'http://www.geonames.org/3425505',
            'NOR': 'http://www.geonames.org/3144096',
            'ZWE': 'http://www.geonames.org/878675',
            'ITA': 'http://www.geonames.org/3175395',
            'CZE': 'http://www.geonames.org/3077311',
            'NZL': 'http://www.geonames.org/2186224',
            'INL': 'http://pid.geoscience.gov.au/def/voc/igsn-codelists/INL',
            'LKA': 'http://www.geonames.org/1227603',
            'IND': 'http://www.geonames.org/1269750'

        },
        # TODO: fix URI for 'unknown' in lith
        'lith': {
           'biogenic sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/biogenic_sediment',
           'websterite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'gypcrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'hardpan': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'argillite': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_mudstone',
           'pyroxene spinifex-textured basalt': 'http://resource.geosciml.org/classifier/cgi/lithology/basalt',
           'olivine hornblendite': 'http://resource.geosciml.org/classifier/cgi/lithology/hornblendite',
           'saprolite, highly weathered': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'fragmental igneous material': 'http://resource.geosciml.org/classifier/cgi/lithology/fragmental_igneous_material',
           'silty mud': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'kalsilitic and melilitic rocks': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'muddy silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'tephra': 'http://resource.geosciml.org/classifier/cgi/lithology/tephra',
           'intrusive rock': 'http://resource.geosciml.org/classifier/cgi/lithology/phaneritic_igneous_rock',
           'felsic granulite': 'http://resource.geosciml.org/classifier/cgi/lithology/granulite',
           'gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'quartzite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartzite',
           'quartz magnetite rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'ferruginous saprolite': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'olivine orthopyroxene gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'lignite': 'http://resource.geosciml.org/classifier/cgi/lithology/lignite',
           'meimechite': 'http://resource.geosciml.org/classifier/cgi/lithology/komatiitic_rock',
           'ultramafic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'sodalite monzodiorite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzodiorite',
           'quartz rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'volcanic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/fine_grained_igneous_rock',
           'diopside sanidine phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'greenschist facies rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/chlorite_actinolite_epidote_metamorphic_rock',
           'loess': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'estuarine sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'diamictite': 'http://resource.geosciml.org/classifier/cgi/lithology/diamictite',
           'impactite': 'http://resource.geosciml.org/classifier/cgi/lithology/impact_generated_material',
           'gravelly clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'diopside leucite lamproite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'saprolite, pallid zone': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'muddy gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'chalk': 'http://resource.geosciml.org/classifier/cgi/lithology/chalk',
           'magnesite': 'http://resource.geosciml.org/classifier/cgi/lithology/dolomitic_or_magnesian_sedimentary_rock',
           'sandy silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'foid-bearing monzonite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_monzonite',
           'coastal sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'plagioclase-bearing pyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'kalsilitite': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'comendite': 'http://resource.geosciml.org/classifier/cgi/lithology/rhyolite',
           'schist': 'http://resource.geosciml.org/classifier/cgi/lithology/schist',
           'aplite': 'http://resource.geosciml.org/classifier/cgi/lithology/aplite',
           'komatiitic (high-Mg) basalt': 'http://resource.geosciml.org/classifier/cgi/lithology/basalt',
           'foid-bearing alkali feldspar syenite':
               'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_alkali_feldspar_syenite',
           'porphyry': 'http://resource.geosciml.org/classifier/cgi/lithology/porphyry',
           'rudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonate_sedimentary_rock',
           'breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/breccia',
           'conglomerate': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_conglomerate',
           'hyaloclastite': 'http://resource.geosciml.org/classifier/cgi/lithology/fragmental_igneous_rock',
           'fanglomerate': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'ultramafic schist': 'http://resource.geosciml.org/classifier/cgi/lithology/schist',
           'limestone wackestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'tourmalinite': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'limestone framestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'harzburgite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'pisolitic ironstone': 'http://resource.geosciml.org/classifier/cgi/lithology/iron_rich_sedimentary_rock',
           'metamorphosed mafic igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'oil shale': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_bearing_mudstone',
           'basic volcanic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/basic_igneous_rock',
           'weathered material, unknown origin':
               'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'vein epidote': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'minette': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'pebbly silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'greywacke': 'http://resource.geosciml.org/classifier/cgi/lithology/wacke',
           'tuffaceous mudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/tuffite',
           'hornblendite': 'http://resource.geosciml.org/classifier/cgi/lithology/hornblendite',
           'ferrocarbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite',
           'pitchstone': 'http://resource.geosciml.org/classifier/cgi/lithology/glassy_igneous_rock',
           'metamorphosed ultramafic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'foid-bearing trachyte': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_trachyte',
           'foid-bearing anorthosite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_anorthosite',
           'olivine hornblende pyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'basanite': 'http://resource.geosciml.org/classifier/cgi/lithology/basanite',
           'eclogite': 'http://resource.geosciml.org/classifier/cgi/lithology/eclogite',
           'basalt': 'http://resource.geosciml.org/classifier/cgi/lithology/basalt',
           'felsic gneiss': 'http://resource.geosciml.org/classifier/cgi/lithology/gneiss',
           'bone bed': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_rock',
           'basic intrusive rock': 'http://resource.geosciml.org/classifier/cgi/lithology/basic_igneous_rock',
           'igneous material': 'http://resource.geosciml.org/classifier/cgi/lithology/igneous_material',
           'mangerite': 'http://resource.geosciml.org/classifier/cgi/lithology/monzonite',
           'calc-silicate rock': 'http://resource.geosciml.org/classifier/cgi/lithology/skarn',
           'sheet flow deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'quartz latite': 'http://resource.geosciml.org/classifier/cgi/lithology/latitic_rock',
           'granulite': 'http://resource.geosciml.org/classifier/cgi/lithology/granulite',
           'dolostone/dolomite boundstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'alcrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'marble': 'http://resource.geosciml.org/classifier/cgi/lithology/marble',
           'phonolitic tephrite': 'http://resource.geosciml.org/classifier/cgi/lithology/phonolitic_tephrite',
           'dolostone/dolomite framestone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'melteigite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'olivine clinopyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'silty gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'phonolite': 'http://resource.geosciml.org/classifier/cgi/lithology/phonolilte',
           'acid igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/acidic_igneous_rock',
           'gravelly silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'limestone bafflestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'novaculite': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'hornblende gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'clayey gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'banded iron formation': 'http://resource.geosciml.org/classifier/cgi/lithology/iron_rich_sedimentary_rock',
           'foliated metamorphic rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/foliated_metamorphic_rock',
           'muddy sandy gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'quartz gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_gabbro',
           'vein quartz': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'till': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'eolian sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'magnetite iron formation':
               'http://resource.geosciml.org/classifier/cgi/lithology/iron_rich_sedimentary_rock',
           'crystalline dolostone/dolomite': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'metasedimentary siliciclastic rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'shonkinite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_syenite',
           'volcanic breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/fragmental_igneous_rock',
           'lag': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'pyroxene peridotite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'picrobasalt':
               'http://resource.geosciml.org/classifier/cgi/lithology/high_magnesium_fine_grained_igneous_rocks',
           'wackestone': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonate_wackestone',
           'olivine gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'kalsilite phlogopite olivine leucite melilitite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'granophyre': 'http://resource.geosciml.org/classifier/cgi/lithology/granitoid',
           'tuffite': 'http://resource.geosciml.org/classifier/cgi/lithology/tuffite',
           'dolostone/dolomite mudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'alluvial sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'chert': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'benmoreite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'dolomitic limestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'olivine pyroxene hornblendite': 'http://resource.geosciml.org/classifier/cgi/lithology/hornblendite',
           'diopside leucite richterite phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'foid-bearing diorite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_diorite',
           'olivine melilitite': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'felsic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'monzogranite': 'http://resource.geosciml.org/classifier/cgi/lithology/monzogranite',
           'sodalite syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_syenite',
           'lamproite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'spilite': 'http://resource.geosciml.org/classifier/cgi/lithology/spilite',
           'silty sandy gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'tuffaceous greywacke': 'http://resource.geosciml.org/classifier/cgi/lithology/tuffite',
           'clayey sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'teschenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_gabbro',
           'silty gravelly sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'massive sulphide': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'vein sulphide': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'granodiorite': 'http://resource.geosciml.org/classifier/cgi/lithology/granodiorite',
           'quartz monzogabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_monzogabbro',
           'slate': 'http://resource.geosciml.org/classifier/cgi/lithology/slate',
           'volcaniclastic sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'kersantite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'pelite': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'mudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_mudstone',
           'quartz anorthosite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_anorthosite',
           'flint': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'camptonite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'hornfels': 'http://resource.geosciml.org/classifier/cgi/lithology/hornfels',
           'gravelly clayey sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'charnockite': 'http://resource.geosciml.org/classifier/cgi/lithology/granite',
           'non-carbonate chemical or biochemical sedimentary rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/sedimentary_rock',
           'tuffaceous siltstone': 'http://resource.geosciml.org/classifier/cgi/lithology/tuffite',
           'greisen': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'psammite': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'ash and lapilli': 'http://resource.geosciml.org/classifier/cgi/lithology/ash_and_lapilli',
           'exotic alkaline igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'nephelinolite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'sandy silty clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'olivine diopside richterite phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'pedolith, mottled zone': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'olivine melilitolite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'quartz feldspar rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'bitumen': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_material',
           'urtite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'plagioclase-bearing hornblendite': 'http://resource.geosciml.org/classifier/cgi/lithology/hornblendite',
           'limestone boundstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'intermediate igneous rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/intermediate_composition_igneous_rock',
           'calcrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'rodingite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'limestone packstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'acid intrusive rock': 'http://resource.geosciml.org/classifier/cgi/lithology/acidic_igneous_rock',
           'dolorudite': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'saprolite, completely weathered': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'sandy mud': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'metasedimentary carbonate rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'mafic granulite': 'http://resource.geosciml.org/classifier/cgi/lithology/granulite',
           'saprock': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'gouge': 'http://resource.geosciml.org/classifier/cgi/lithology/breccia_gouge_series',
           'sedimentary rock': 'http://resource.geosciml.org/classifier/cgi/lithology/sedimentary_rock',
           'limestone mudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'calcite carbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite',
           'metamorphosed intermediate igneous rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'iron segregations':
               'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'pyroclastic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroclastic_rock',
           'hornblende pyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'metasedimentary rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'lamprophyre': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'quartz alkali feldspar syenite':
               'http://resource.geosciml.org/classifier/cgi/lithology/quartz_alkali_feldspar_syenite',
           'quartz sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'gossan': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'lherzolite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'lapilli tuff':
               'http://resource.geosciml.org/classifier/cgi/lithology/ash_tuff_lapillistone_and_lapilli_tuff',
           'unknown': 'http://www.opengis.net/def/nil/OGC/0/unknown',  # OGC nill type
           'pantellerite': 'http://resource.geosciml.org/classifier/cgi/lithology/rhyolite',
           'limestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'micrite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'appinite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'trachyte': 'http://resource.geosciml.org/classifier/cgi/lithology/trachyte',
           'dust': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'serpentinite': 'http://resource.geosciml.org/classifier/cgi/lithology/serpentinite',
           'diorite': 'http://resource.geosciml.org/classifier/cgi/lithology/diorite',
           'geyserite': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'limestone rudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'sand, eolian': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'melilitite': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'miaskite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzosyenite',
           'dolarenite': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'hydrothermal breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'phyllonite': 'http://resource.geosciml.org/classifier/cgi/lithology/phyllonite',
           'anorthosite': 'http://resource.geosciml.org/classifier/cgi/lithology/anorthosite',
           'non-clastic siliceous sedimentary rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'grapestone': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonate_sedimentary_rock',
           'pedolith': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'carbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite',
           'hyalo enstatite phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'pyroxene olivine melilitolite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'chromitite': 'http://resource.geosciml.org/classifier/cgi/lithology/ultramafic_igneous_rock',
           'gyttja': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'theralite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_gabbro',
           'rhyodacite': 'http://resource.geosciml.org/classifier/cgi/lithology/rhyolite',
           'quartz-rich granitoid': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_rich_igneous_rock',
           'tonalite': 'http://resource.geosciml.org/classifier/cgi/lithology/tonalite',
           'bauxite': 'http://resource.geosciml.org/classifier/cgi/lithology/bauxite',
           'analcimite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidite',
           'coquina': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'psammopelite': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'ooze': 'http://resource.geosciml.org/classifier/cgi/lithology/ooze',
           'orthopyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'quartz syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_syenite',
           'conglomeratic sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'quartz breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/breccia',
           'ferricrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'magnetite rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'regolith': 'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'foid-bearing intrusive rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/phaneritic_igneous_rock',
           'sandy clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'mugearite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'phosphorite': 'http://resource.geosciml.org/classifier/cgi/lithology/phosphorite',
           'sedimentary breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sedimentary_rock',
           'beach sediments': 'http://resource.geosciml.org/classifier/cgi/lithology/sediment',
           'coal': 'http://resource.geosciml.org/classifier/cgi/lithology/coal',
           'feldspar porphyry': 'http://resource.geosciml.org/classifier/cgi/lithology/porphyry',
           'dacite': 'http://resource.geosciml.org/classifier/cgi/lithology/dacite',
           'scree': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'vein barite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'pebbles': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'vein carbonate': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'mica schist': 'http://resource.geosciml.org/classifier/cgi/lithology/mica_schist',
           'shale': 'http://resource.geosciml.org/classifier/cgi/lithology/shale',
           'phonolitic foidite': 'http://resource.geosciml.org/classifier/cgi/lithology/phonolitic_foidite',
           'pseudotachylite': 'http://resource.geosciml.org/classifier/cgi/lithology/fault_related_material',
           'monchiquite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'foid-bearing volcanic rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/fine_grained_igneous_rock',
           'clastic sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'radiolarite': 'http://resource.geosciml.org/classifier/cgi/lithology/biogenic_silica_sedimentary_rock',
           'muddy sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'residual soil on fresh bedrock': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'obsidian': 'http://resource.geosciml.org/classifier/cgi/lithology/glassy_igneous_rock',
           'pyroxene melilitolite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'quartz feldspar porphyry': 'http://resource.geosciml.org/classifier/cgi/lithology/porphyry',
           'anthracite': 'http://resource.geosciml.org/classifier/cgi/lithology/anthracite_coal',
           'nepheline syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_syenite',
           'quartz trachyte': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytic_rock',
           'foid-bearing monzodiorite':
               'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_monzodiorite',
           'norite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'alnoite': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'ironstone': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'foid-bearing gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_gabbro',
           'acid volcanic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/acidic_igneous_rock',
           'troctolite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'olivine norite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'residual material': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'migmatite': 'http://resource.geosciml.org/classifier/cgi/lithology/migmatite',
           'foid-bearing igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/igneous_rock',
           'gravelly silty sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'andesite': 'http://resource.geosciml.org/classifier/cgi/lithology/andesite',
           'foid diorite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_diorite',
           'wood': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_material',
           'vitric tuff':
               'http://resource.geosciml.org/classifier/cgi/lithology/ash_tuff_lapillistone_and_lapilli_tuff',
           'silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'iron formation': 'http://resource.geosciml.org/classifier/cgi/lithology/iron_rich_sedimentary_rock',
           'ijolite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'spongolite': 'http://resource.geosciml.org/classifier/cgi/lithology/biogenic_silica_sedimentary_rock',
           'pegmatite': 'http://resource.geosciml.org/classifier/cgi/lithology/pegmatite',
           'exotic composition igneous rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_composition_igneous_rock',
           'beachrock': 'http://resource.geosciml.org/classifier/cgi/lithology/calcareous_carbonate_sedimentary_rock',
           'carbonate sedimentary rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/carbonate_sedimentary_rock',
           'calcilutite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'swamp sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'sandy gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'orthopyroxene gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'pyroxene hornblende gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'marine sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'foid-bearing alkali feldspar trachyte':
               'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_alkali_feldspar_trachyte',
           'greenstone':
               'http://resource.geosciml.org/classifier/cgi/lithology/chlorite_actinolite_epidote_metamorphic_rock',
           'augen gneiss': 'http://resource.geosciml.org/classifier/cgi/lithology/gneiss',
           'vein breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/breccia',
           'arenite': 'http://resource.geosciml.org/classifier/cgi/lithology/arenite',
           'olivine pyroxene melilitolite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'trondhjemite': 'http://resource.geosciml.org/classifier/cgi/lithology/tonalite',
           'foidolite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'foid gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_gabbro',
           'lithic tuff':
               'http://resource.geosciml.org/classifier/cgi/lithology/ash_tuff_lapillistone_and_lapilli_tuff',
           'quartz monzonite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_monzonite',
           'limburgite': 'http://resource.geosciml.org/classifier/cgi/lithology/basanite',
           'clinopyroxene norite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'phonolitic basanite': 'http://resource.geosciml.org/classifier/cgi/lithology/phonolitic_basanite',
           'claystone': 'http://resource.geosciml.org/classifier/cgi/lithology/claystone',
           'unconsolidated material': 'http://resource.geosciml.org/classifier/cgi/lithology/unconsolidated_material',
           'silty sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'peralkaline rhyolite': 'http://resource.geosciml.org/classifier/cgi/lithology/rhyolite',
           'syenogranite': 'http://resource.geosciml.org/classifier/cgi/lithology/syenogranite',
           'crystalline limestone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'mud': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'biomicrite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'foid syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_syenite',
           'scoria': 'http://resource.geosciml.org/classifier/cgi/lithology/basalt',
           'foid-bearing monzogabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_monzogabbro',
           'olivine pyroxene kalsilitite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'pyroxene hornblende norite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'basaltic trachyandesite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'lateritic duricrust': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'ash tuff': 'http://resource.geosciml.org/classifier/cgi/lithology/ash_tuff_lapillistone_and_lapilli_tuff',
           'bouldery clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'boundstone': 'http://resource.geosciml.org/classifier/cgi/lithology/boundstone',
           'glacial sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'breccia, bomb or block tephra':
               'http://resource.geosciml.org/classifier/cgi/lithology/ash_breccia_bomb_or_block_tephra',
           'tillite': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sedimentary_rock',
           'igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/igneous_rock',
           'leucite richterite lamproite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'rhyolite': 'http://resource.geosciml.org/classifier/cgi/lithology/rhyolite',
           'pyroxene hornblendite': 'http://resource.geosciml.org/classifier/cgi/lithology/hornblendite',
           'boulders': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'basic igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/basic_igneous_rock',
           'para-amphibolite': 'http://resource.geosciml.org/classifier/cgi/lithology/amphibolite',
           'dolostone/dolomite packstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'clayey silt': 'http://resource.geosciml.org/classifier/cgi/lithology/silt',
           'loam': 'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'extra-terrestrial material': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'agglomerate':
               'http://resource.geosciml.org/classifier/cgi/lithology/tuff_breccia_agglomerate_or_pyroclastic_breccia',
           'biosparite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'tourmalite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'pyroxene hornblende peridotite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'gypsum': 'http://resource.geosciml.org/classifier/cgi/lithology/rock_gypsum_or_anhydrite',
           'monzodiorite': 'http://resource.geosciml.org/classifier/cgi/lithology/monzodiorite',
           'marl': 'http://resource.geosciml.org/classifier/cgi/lithology/impure_carbonate_sedimentary_rock',
           'ultramafic intrusive rock': 'http://resource.geosciml.org/classifier/cgi/lithology/ultramafic_igneous_rock',
           'epiclastic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sedimentary_rock',
           'hornblende peridotite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'tephritic phonolite': 'http://resource.geosciml.org/classifier/cgi/lithology/tephritic_phonolite',
           'picrite': 'http://resource.geosciml.org/classifier/cgi/lithology/high_magnesium_fine_grained_igneous_rocks',
           'ignimbrite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroclastic_rock',
           'fergusite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'foid monzosyenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzosyenite',
           'duricrust': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'granofels': 'http://resource.geosciml.org/classifier/cgi/lithology/granofels',
           'argillaceous sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'blueschist facies rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/glaucophane_lawsonite_epidote_metamorphic_rock',
           'fenite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'limestone grainstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'olivine clinopyroxene norite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'foid-bearing syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_syenite',
           'travertine': 'http://resource.geosciml.org/classifier/cgi/lithology/travertine',
           'alkali feldspar syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/alkali_feldspar_syenite',
           'grainstone': 'http://resource.geosciml.org/classifier/cgi/lithology/grainstone',
           'silty clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'nephelinite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidite',
           'organic rich sedimentary material':
               'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_material',
           'dolostone/dolomite bindstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'peridotite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'greensand': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'barite': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'landslide deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'saprolite, moderately weathered': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'albitite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'soil': 'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'metasomatite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'diatomite': 'http://resource.geosciml.org/classifier/cgi/lithology/biogenic_silica_sedimentary_rock',
           'amphibolite': 'http://resource.geosciml.org/classifier/cgi/lithology/amphibolite',
           'olivine pyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'channel deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'fault or shear rock': 'http://resource.geosciml.org/classifier/cgi/lithology/fault_related_material',
           'arkose': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sandstone',
           'dolerite': 'http://resource.geosciml.org/classifier/cgi/lithology/doleritic_rock',
           'jaspilite': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'calciocarbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite',
           'crystalline carbonate': 'http://resource.geosciml.org/classifier/cgi/lithology/crystalline_carbonate',
           'dolostone/dolomite grainstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'magnetitite': 'http://resource.geosciml.org/classifier/cgi/lithology/ultramafic_igneous_rock',
           'sannaite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'monzonite': 'http://resource.geosciml.org/classifier/cgi/lithology/monzonite',
           'intermediate intrusive rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/intermediate_composition_igneous_rock',
           'diopside leucite phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'packstone': 'http://resource.geosciml.org/classifier/cgi/lithology/packstone',
           'saprolite': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'foidite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidite',
           'turbidite': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sedimentary_rock',
           'saprolith': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'dolostone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'silty sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'potassic trachybasalt': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'missourite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidolite',
           'latite': 'http://resource.geosciml.org/classifier/cgi/lithology/latite',
           'ferruginised rock fragments':
               'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'clayey sandy gravel': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'ultrabasic igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/ultrabasic_igneous_rock',
           'calcarenite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'quartz porphyry': 'http://resource.geosciml.org/classifier/cgi/lithology/porphyry',
           'guano': 'http://resource.geosciml.org/classifier/cgi/lithology/phosphorite',
           'dunite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'saprolite, mottled zone': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'essexite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzogabbro',
           'sinter': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'jotunite': 'http://resource.geosciml.org/classifier/cgi/lithology/monzodiorite',
           'tuffaceous sandstone': 'http://resource.geosciml.org/classifier/cgi/lithology/tuffite',
           'black shale': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_bearing_mudstone',
           'trachyandesite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'magnesiocarbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite',
           'meteorite': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'overbank deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'mylonite': 'http://resource.geosciml.org/classifier/cgi/lithology/mylonitic_rock',
           'leucitite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidite',
           'kimberlite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'gravelly muddy sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'metamorphic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'felsic schist': 'http://resource.geosciml.org/classifier/cgi/lithology/schist',
           'melilitolite': 'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'boninite':
               'http://resource.geosciml.org/classifier/cgi/lithology/high_magnesium_fine_grained_igneous_rocks',
           'tephrite': 'http://resource.geosciml.org/classifier/cgi/lithology/tephrite',
           'kalsilite phlogopite melilitite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'phyllite': 'http://resource.geosciml.org/classifier/cgi/lithology/phyllite',
           'trachybasalt': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'skarn': 'http://resource.geosciml.org/classifier/cgi/lithology/skarn',
           'foid monzogabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzogabbro',
           'clay': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'gabbronorite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'dolostone/dolomite floatstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'basaltic andesite': 'http://resource.geosciml.org/classifier/cgi/lithology/andesite',
           'sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/sediment',
           'terrestrial sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'limestone bindstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'grus': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'anthropogenic material':
               'http://resource.geosciml.org/classifier/cgi/lithology/anthropogenic_unconsolidated_material',
           'vogesite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'biocarbonate': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonate_sedimentary_rock',
           'siltstone': 'http://resource.geosciml.org/classifier/cgi/lithology/siltstone',
           'sodalitite': 'http://resource.geosciml.org/classifier/cgi/lithology/foidite',
           'kalsilite leucite olivine melilitite':
               'http://resource.geosciml.org/classifier/cgi/lithology/kalsilitic_and_melilitic_rock',
           'olivine orthopyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'melange': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'clinopyroxene gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'vein fluorite': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'vein iron oxide': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'clinopyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'anhydrite': 'http://resource.geosciml.org/classifier/cgi/lithology/rock_gypsum_or_anhydrite',
           'diopside phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'opdalite': 'http://resource.geosciml.org/classifier/cgi/lithology/granodiorite',
           'limestone breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'gravelly mud': 'http://resource.geosciml.org/classifier/cgi/lithology/mud',
           'pumice': 'http://resource.geosciml.org/classifier/cgi/lithology/acidic_igneous_rock',
           'coral': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'pyroxenite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'hawaiite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'sulphide-rich rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'leucite phlogopite lamproite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'sand, residual': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'amber': 'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_material',
           'shoshonite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'limestone floatstone': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'hyalo olivine diopside phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'dolostone/dolomite bafflestone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'dolocrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'jasper': 'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'mudflow deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'saprolite, very highly weathered':
               'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'olivine gabbronorite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'monzogabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/monzogabbro',
           'komatiite': 'http://resource.geosciml.org/classifier/cgi/lithology/komatiitic_rock',
           'clay, residual': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'gabbro': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbro',
           'chalcedony': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'foid-bearing latite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_bearing_latite',
           'quartz dolerite': 'http://resource.geosciml.org/classifier/cgi/lithology/doleritic_rock',
           'wehrlite': 'http://resource.geosciml.org/classifier/cgi/lithology/peridotite',
           'tephritic foidite': 'http://resource.geosciml.org/classifier/cgi/lithology/tephritic_foidite',
           'carbonate rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'fault breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/breccia_gouge_series',
           'parna': 'http://resource.geosciml.org/classifier/cgi/lithology/clay',
           'mafic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'volcaniclastic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/fragmental_igneous_rock',
           'organic rich sedimentary rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/organic_rich_sedimentary_rock',
           'mafic schist': 'http://resource.geosciml.org/classifier/cgi/lithology/schist',
           'dololutite': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'torbanite': 'http://resource.geosciml.org/classifier/cgi/lithology/coal',
           'alkali feldspar granite': 'http://resource.geosciml.org/classifier/cgi/lithology/alkali_feldspar_granite',
           'dolostone/dolomite breccia': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'pisoliths':
               'http://resource.geosciml.org/classifier/cgi/lithology/material_formed_in_surficial_environment',
           'enstatite sanidine phlogopite lamproite':
               'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'creep deposit': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'gneiss': 'http://resource.geosciml.org/classifier/cgi/lithology/gneiss',
           'gravelly sand': 'http://resource.geosciml.org/classifier/cgi/lithology/sand',
           'trachydacite': 'http://resource.geosciml.org/classifier/cgi/lithology/trachytoid',
           'quartz diorite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_diorite',
           'metamorphosed acid igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/metamorphic_rock',
           'crystal tuff':
               'http://resource.geosciml.org/classifier/cgi/lithology/ash_tuff_lapillistone_and_lapilli_tuff',
           'alkali basalt': 'http://resource.geosciml.org/classifier/cgi/lithology/alkali-olivine_basalt',
           'quartzolite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_rich_igneous_rock',
           'colluvial sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'alkali feldspar rhyolite': 'http://resource.geosciml.org/classifier/cgi/lithology/alkali_feldspar_rhyolite',
           'manganese rock': 'http://resource.geosciml.org/classifier/cgi/lithology/rock',
           'cobbles': 'http://resource.geosciml.org/classifier/cgi/lithology/gravel',
           'pyroxene hornblende gabbronorite': 'http://resource.geosciml.org/classifier/cgi/lithology/gabbroic_rock',
           'quartz monzodiorite': 'http://resource.geosciml.org/classifier/cgi/lithology/quartz_monzodiorite',
           'olivine websterite': 'http://resource.geosciml.org/classifier/cgi/lithology/pyroxenite',
           'silcrete': 'http://resource.geosciml.org/classifier/cgi/lithology/duricrust',
           'intermediate volcanic rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/intermediate_composition_igneous_rock',
           'carbonaceous siltstone': 'http://resource.geosciml.org/classifier/cgi/lithology/siltstone',
           'mineralisation': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'rock salt': 'http://resource.geosciml.org/classifier/cgi/lithology/rock_salt',
           'granite': 'http://resource.geosciml.org/classifier/cgi/lithology/granite',
           'carbonate iron formation':
               'http://resource.geosciml.org/classifier/cgi/lithology/iron_rich_sedimentary_rock',
           'lacustrine sediment': 'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sediment',
           'calcisiltite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'peat': 'http://resource.geosciml.org/classifier/cgi/lithology/peat',
           'lateritic residuum': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'dolostone/dolomite rudstone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'syenite': 'http://resource.geosciml.org/classifier/cgi/lithology/syenite',
           'enderbite': 'http://resource.geosciml.org/classifier/cgi/lithology/tonalite',
           'vein': 'http://resource.geosciml.org/classifier/cgi/lithology/metasomatic_rock',
           'ultramafic volcanic rock': 'http://resource.geosciml.org/classifier/cgi/lithology/ultramafic_igneous_rock',
           'ferruginous lag': 'http://resource.geosciml.org/classifier/cgi/lithology/residual_material',
           'foid monzodiorite': 'http://resource.geosciml.org/classifier/cgi/lithology/foid_monzodiorite',
           'evaporite': 'http://resource.geosciml.org/classifier/cgi/lithology/evaporite',
           'ultramafic igneous rock': 'http://resource.geosciml.org/classifier/cgi/lithology/ultramafic_igneous_rock',
           'siliciclastic sedimentary rock':
               'http://resource.geosciml.org/classifier/cgi/lithology/clastic_sedimentary_rock',
           'sandy siltstone': 'http://resource.geosciml.org/classifier/cgi/lithology/siltstone',
           'dolostone/dolomite wackestone': 'http://resource.geosciml.org/classifier/cgi/lithology/dolostone',
           'spessartite': 'http://resource.geosciml.org/classifier/cgi/lithology/exotic_alkaline_rock',
           'calcirudite': 'http://resource.geosciml.org/classifier/cgi/lithology/limestone',
           'porcellanite':
               'http://resource.geosciml.org/classifier/cgi/lithology/non_clastic_siliceous_sedimentary_rock',
           'dolomite carbonatite': 'http://resource.geosciml.org/classifier/cgi/lithology/carbonatite'
                },
        'entity_type': {
            'BOREHOLE': 'http://pid.geoscience.gov.au/def/voc/featureofinteresttype/borehole',
            'FIELD SITE': 'http://pid.geoscience.gov.au/def/voc/featureofinteresttype/site',
            'SURVEY': 'http://pid.geoscience.gov.au/def/voc/featureofinteresttype/survey',
            # see vocab <http://pid.geoscience.gov.au/def/voc/featureofinteresttype>
        }
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
        self.base_url = None

    def validate_xml(self, xml):

        parser = etree.XMLParser(dtd_validation=False)

        try:
            etree.fromstring(xml, parser)
            return True
        except Exception:
            print 'not valid xml'
            return False

    def populate_from_oracle_api(self, igsn, base_url):
        """
        Populates this instance with data from the Oracle Samples table API

        :param igsn: the IGSN of the sample desired
        :return: None
        """

        self.base_url = base_url
        # internal URI
        #os.environ['NO_PROXY'] = 'ga.gov.au'
        # target_url = 'http://biotite.ga.gov.au:7777/wwwstaff_distd/a.igsn_api.get_igsnSample?pIGSN=' + igsn
        # external URI
        target_url = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSample?pIGSN=' + igsn
        # call API
        r = requests.get(target_url)
        # deal with missing XML declaration
        if "No data" in r.content:
            raise ParameterError('No Data')
            return False
        if not r.content.startswith('<?xml version="1.0" ?>'):
            xml = '<?xml version="1.0" ?>\n' + r.content
        else:
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
                    self.sample_type = Sample.TERM_LOOKUP['sample_type'].get(elem.text)
                    if self.sample_type is None:
                        self.sample_type = Sample.URI_MISSSING
            elif elem.tag == "SAMPLING_METHOD":
                if elem.text is not None:
                    self.method_type = Sample.TERM_LOOKUP['method_type'].get(elem.text)
                    if self.method_type is None:
                        self.method_type = Sample.URI_MISSSING
            elif elem.tag == "MATERIAL_CLASS":
                if elem.text is not None:
                    self.material_type = Sample.TERM_LOOKUP['material_type'].get(elem.text)
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
                    self.state = Sample.TERM_LOOKUP['state'].get(elem.text)
                    if self.state is None:
                        self.state = Sample.URI_MISSSING
            elif elem.tag == "COUNTRY":
                if elem.text is not None:
                    self.country = Sample.TERM_LOOKUP['country'].get(elem.text)
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
                    self.lith = Sample.TERM_LOOKUP['lith'].get(elem.text)
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

    def generate_sample_wkt(self):
        if self.z is not None:
            # wkt = "SRID=" + self.srid + ";POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
            wkt = "<https://epsg.io/" + self.srid + "> " \
                  "POINTZ(" + self.x + " " + self.y + " " + self.z + ")"
        else:
            # wkt = "SRID=" + self.srid + ";POINT(" + self.x + " " + self.y + ")"
            wkt = "<https://epsg.io/" + self.srid + "> POINT(" + self.x + " " + self.y + ")"

        return wkt

    def generate_sample_gml(self):
        if self.z is not None:
            gml = '<gml:Point srsDimension="3" srsName="https://epsg.io/' + self.srid + '">' \
                  '<gml:pos>' + self.x + ' ' + self.y + ' ' + self.z + '</gml:pos>' \
                  '</gml:Point>'
        else:
            gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/' + self.srid + '">' \
                  '<gml:pos>' + self.x + ' ' + self.y + '</gml:pos>' \
                  '</gml:Point>'

        return gml

    def generate_parent_wkt(self):
        # TODO: add support for geometries other than Point
        wkt = "<https://epsg.io/" + self.srid + ">POINT(" + self.hole_long_min + " " + self.hole_lat_min + ")"

        return wkt

    def generate_parent_gml(self):
        # TODO: add support for geometries other than Point
        gml = '<gml:Point srsDimension="2" srsName="https://epsg.io/' + \
              self.srid + '"><gml:pos>' + self.hole_long_min + ' ' + self.hole_lat_min + '</gml:pos>' \
              '</gml:Point>'
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
        wkt = Literal(self.generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self.generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        # select model view
        if model_view == 'default' or model_view == 'igsn' or model_view is None:
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
            g.add((this_sample, DCT.accessRights, URIRef(Sample.TERM_LOOKUP['access']['Public'])))
            # TODO: make a register of Entities
            this_parent = URIRef(self.entity_uri)
            g.add((this_sample, SAMFL.relatedSamplingFeature, this_parent))  # could be OM.featureOfInterest

            # parent
            g.add((this_parent, RDF.type, URIRef(Sample.TERM_LOOKUP['entity_type'][self.entity_type])))

            parent_geometry = BNode()
            g.add((this_parent, GEOSP.hasGeometry, parent_geometry))
            g.add((parent_geometry, RDF.type, SAMFL.Point))  # TODO: extend this for other geometry types
            g.add((parent_geometry, GEOSP.asWKT, Literal(self.generate_parent_wkt(), datatype=GEOSP.wktLiteral)))
            g.add((parent_geometry, GEOSP.asGML, Literal(self.generate_parent_gml(), datatype=GEOSP.wktLiteral)))

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

        return g.serialize(format=LDAPI.get_file_extension(rdf_mime))

    def is_xml_export_valid(self, xml_string):
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
        wkt = Literal(self.generate_sample_wkt(), datatype=GEOSP.wktLiteral)
        gml = Literal(self.generate_sample_gml(), datatype=GEOSP.gmlLiteral)

        dt = datetime.now()
        date_stamp = datetime_to_datestamp(dt)

        format = URIRef(self.material_type)

        # TODO:   add is site uri
        xml = 'xml = <record>\
        <header>\
        <identifier>' + self.entity_uri + '</identifier>\
        <datestamp>' + date_stamp + '</datestamp>\
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
        Exports this Sample instance in XML that validates against the IGSN Descriptive Metadata schema from
        https://github.com/IGSN/metadata/tree/dev/description

        :return: XML string
        """
        # SESAR
        '''
        SESAR XML example from: https://app.geosamples.org/webservices/display.php?igsn=LCZ7700AK

        <?xml version="1.0" encoding="UTF-8"?>
        <results>
            <qrcode_img_src>
                app.geosamples.org/barcode/image.php?igsn=LCZ7700AK&amp;sample_id=CDR4_100mesh
            </qrcode_img_src>
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
        sample_wkt = self.generate_sample_wkt()
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
        if model_view == 'default' or model_view == 'igsn' or model_view is None:
            # TODO: complete the properties in this view
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            if self.sampleid is not None:
                html += '   <tr><th>Sample ID</th><td>' + self.sampleid + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Sample Type</th><td>' + self.sample_type + '</td></tr>'

        elif model_view == 'dc':
            html += '   <tr><th>IGSN</th><td>' + self.igsn + '</td></tr>'
            html += '   <tr><th>Coverage</th><td>' + self.generate_sample_wkt() + '</td></tr>'
            if self.date_acquired is not None:
                html += '   <tr><th>Date</th><td>' + self.date_acquired.isoformat() + '</td></tr>'
            if self.remark is not None:
                html += '   <tr><th>Description</th><td>' + self.remark + '</td></tr>'
            if self.material_type is not None:
                html += '   <tr><th>Format</th><td>' + self.material_type + '</td></tr>'
            if self.sample_type is not None:
                html += '   <tr><th>Type</th><td>' + self.sample_type + '</td></tr>'

        html += '</table>'

        return html
class ParameterError(ValueError):
    pass

if __name__ == '__main__':
    print "hello"
    s = Sample()
    #s.populate_from_xml_file('../test/sample_eg1.xml')
    s.populate_from_oracle_api('AU100')
    print s.export_dc_xml()

    # print s.is_xml_export_valid(open('../test/sample_eg3_IGSN_schema.xml').read())
    # print s.export_as_igsn_xml()
