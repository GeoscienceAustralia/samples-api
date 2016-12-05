from flask import Blueprint, Response, render_template, request, make_response
from lxml import etree
from lxml.builder import ElementMaker
import settings
import functions
from ldapi import LDAPI, LdapiParameterError
import datetime
routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    """
    A basic landing page for this web service

    :return: HTTP Response (HTML page only)
    """
    views_formats = {
        'default': 'landingpage',
        'alternates': ['text/html'],
        'landingpage': ['text/html'],
        'getcapabilities': ['application/xml']
    }

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )
    except LdapiParameterError, e:
        return functions.client_error_Response(e)

    # select view and format
    if view == 'alternates':
        return functions.render_templates_alternates('index.html', views_formats)
    elif view == 'landingpage':
        if format == 'text/html':
            return render_template(
                'index.html',
                base_uri=settings.BASE_URI,
                web_subfolder = settings.WEB_SUBFOLDER,
            )
        else:
            return Response(
                'This view of the API\'s root only has an HTML representation',
                status=400,
                mimetype='text/plain')
    elif view == 'getcapabilities':
        # only a single format for this view
        em = ElementMaker(namespace="http://fake.com/ldapi",
                          nsmap={
                              'ldapi': "http://fake.com/ldapi"
                          })
        onl = ElementMaker(namespace="http://fake.com/ldapi",
                          nsmap={
                              'xlink': "http://www.w3.org/1999/xlink",
                          })
        doc = em.LDAPI_Capabilities(
            em.Service(
                em.Name('Linked Data API'),
                em.Title('Geoscience Australia\'s Physical Samples'),
                em.KeywordList(
                    em.Keyword('sample'),
                    em.Keyword('IGSN'),
                    em.Keyword('Linked Data'),
                    em.Keyword('XML'),
                    em.Keyword('RDF'),
                ),
                # TODO: parameterised namespaces not working yet
                onl.OnlineResource(type="simple", href="http://pid.geoscience.gov.au/service/samples/"),
                em.ContactInformation(
                    em.ContactPersonPrimary(
                        em.contactPerson('Nicholas Car'),
                        em.ContactOrganization('Geoscience Australia')
                    ),
                    em.ContactAddress(
                        em.AddressType('Postal'),
                        em.Address('GPO Box 378'),
                        em.City('Canberra'),
                        em.StateOrProvince('ACT'),
                        em.PostCode('2601'),
                        em.Country('Australia'),
                        em.ContactVoiceTelephone('+61 2 6249 9111'),
                        em.ContactFacsimileTelephone(),
                        em.ContactElectronicMailAddress('clientservices@ga.gov.au')
                    )
                ),
                em.Fees('none'),
                em.AccessConstraints('(c) Commonwealth of Australia (Geoscience Australia) 2016. This product is released under the Creative Commons Attribution 4.0 International Licence. http://creativecommons.org/licenses/by/4.0/legalcode')
            ),
            em.Capability(
                em.Request(
                    em.GetCapabilities(
                        em.Format('application/xml'),
                        em.DCPType(
                            em.HTTP(
                                em.Get(
                                    onl.OnlineResource(
                                        type="simple",
                                        href="http://pid.geoscience.gov.au/service/samples/?_view=getcapabilities&_format=application/xml"),
                                )
                            )
                        )
                    ),
                    em.Sample(
                        em.Format('text/html'),
                        em.Format('text/turtle'),
                        em.Format('application/rdf+xml'),
                        em.Format('application/rdf+json'),
                        em.DCPType(
                            em.HTTP(
                                em.Get(
                                    onl.OnlineResource(
                                        type="simple",
                                        href="http://pid.geoscience.gov.au/service/samples/{SAMPLE_IGSN}"),
                                )
                            )
                        )
                    ),
                    em.SampleRegister(
                        em.Format('text/html'),
                        em.Format('text/turtle'),
                        em.Format('application/rdf+xml'),
                        em.Format('application/rdf+json'),
                        em.DCPType(
                            em.HTTP(
                                em.Get(
                                    onl.OnlineResource(
                                        type="simple",
                                        href="http://pid.geoscience.gov.au/service/samples/"),
                                )
                            )
                        )
                    )
                )

            )
        )
        xml = etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return Response(xml, status=200, mimetype='application/xml')


@routes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = {
        'default': 'igsn',
        'alternates': ['text/html'],
        'igsn': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'dc': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'prov': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
    }

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )
    except LdapiParameterError, e:
        return functions.client_error_Response(e)

    # select view and format
    if view == 'alternates':
        return functions.render_templates_alternates('sample.html', views_formats)
    elif view in ['igsn', 'dc', 'prov']:
        # for all these views we will need to populate a sample
        from sample.sample import Sample
        s = Sample()
        #s.populate_from_xml_file('test/sample_eg2.xml')
        s.populate_from_oracle_api(igsn)

        if format in ['text/turtle', 'application/rdf+xml', 'application/rdf+json']:
            return Response(
                s.export_as_rdf(
                    model_view=view,
                    rdf_mime=format),
                status=200,
                mimetype=format,
                headers={'Content-Disposition': 'attachment; filename=' + igsn + LDAPI.get_file_extension(format)}
            )
        elif format == 'application/xml':
            # TODO: implement IGSN XML format
            pass
        else:  # format == 'text/html'
            return render_template(
                'sample.html',
                base_uri=settings.BASE_URI,
                web_subfolder=settings.WEB_SUBFOLDER,
                view=view,
                placed_html=s.export_as_html(model_view=view)
            )


@routes.route('/sample/')
def samples():
    """
    Samples register

    :return: HTTP Response
    """

    views_formats = {
        'default': 'dpr',
        'alternates': ['text/html'],
        'dpr': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
    }

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )
    except LdapiParameterError, e:
        return functions.client_error_Response(e)

    # validate page_no parameter
    if functions.an_int(request.args.get('page_no')):
        page_no = int(request.args.get('page_no'))
    else:
        page_no = 1

    # select view and format
    if view == 'alternates':
        return functions.render_templates_alternates('samples.html', views_formats)
    elif view in ['dpr']:
        # only create and populate a SamplesRegister for views that need it
        from sample.samples_register import SampleRegister
        sr = SampleRegister()
        sr.populate_from_oracle_api(page_no)

        if format == 'text/html':
            return render_template(
                'samples.html',
                base_uri=settings.BASE_URI,
                web_subfolder=settings.WEB_SUBFOLDER,
                placed_html=sr.export_as_html(model_view='dpr')
            )
        elif format in views_formats['dpr']:
            return Response(
                sr.export_as_rdf(
                    model_view=view,
                    rdf_mime=format),
                status=200,
                mimetype=format,
                headers={'Content-Disposition': 'attachment; filename=samples_register' + LDAPI.get_file_extension(format)}
            )
        # no need for an else since views already validated


@routes.route('/page/about')
def about():
    return render_template('about.html')


@routes.route('/oai')
def oai():
    # TODO: validate args using functions_oai
    if request.args.get('verb'):
        verb = request.args.get('verb')
    else:
        values = {
            'response_date': datetime.datetime.now().isoformat(),
            'request_uri': 'http://54.66.133.7/igsn-ld-api/oai',
            'error_code': 'badVerb',
            'error_text': 'Illegal OAI verb'
        }
        template = render_template('oai_error.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response

    # TODO: implement using XML template
    if verb == 'GetRecord':
        # render_template
        pass
    elif verb == 'Identify':
        pass
