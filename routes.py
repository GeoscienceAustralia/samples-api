from flask import Blueprint, Response, render_template, request
from lxml import etree
from lxml.builder import ElementMaker
import settings
routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    """
    A basic landing page for this web service

    :return: HTTP Response (HTML page only)
    """
    views_formats = {
        'default': 'landingpage',
        'alternates': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'landingpage': ['text/html'],
        'getcapabilities': ['application/xml']
    }

    # validate view
    if request.args.get('_view') is not None:
        if request.args.get('_view') not in views_formats.iterkeys():
            return Response(
                'You have selected a view that does not exist for this API\'s index. Please choose one of ' +
                ', '.join(views_formats.iterkeys()) + '.',
                status=400,
                mimetype='text/plain')
        else:
            view = request.args.get('_view')
    else:
        view = 'default'

    # replace 'default' with nominated default view
    if view == 'default':
        view = views_formats['default']

    # validate format
    if request.args.get('_format') is not None:
        if request.args.get('_format').replace(' ', '+') not in views_formats[view]:
            return Response(
                'You have selected a format that does not exist for the view of Samples you selected. ' +
                'Please choose one of ' + ', '.join(views_formats[view]) + '.',
                status=400,
                mimetype='text/plain')
        else:
            format = request.args.get('_format').replace(' ', '+')
    else:
        format = 'text/html'

    # select view and format
    if view == 'alternates':
        return render_template(
            'sample.html',
            base_uri=settings.BASE_URI,
            web_subfolder=settings.WEB_SUBFOLDER,
            view=view,
            alternates_html=render_template('view_alternates.html', views_formats=views_formats)
        )
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
        if format == 'application/xml':

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

        else:
            return Response(
                'This view of the API\'s root only has an XML representation',
                status=400,
                mimetype='text/plain')


@routes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = {
        'default': 'igsn',
        'alternates': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'igsn': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'dc': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
    }

    # TODO: generalise this and move it to functions.py
    # validate view
    if request.args.get('_view') is not None:
        if request.args.get('_view') not in views_formats.iterkeys():
            return Response(
                'You have selected a view that does not exist for Samples. Please choose one of ' +
                ', '.join(views_formats.iterkeys()) + '.',
                status=400,
                mimetype='text/plain')
        else:
            view = request.args.get('_view')
    else:
        view = 'default'

    # replace 'default' with nominated default view
    if view == 'default':
        view = views_formats['default']

    # validate format
    if request.args.get('_format') is not None:
        if request.args.get('_format').replace(' ', '+') not in views_formats[view]:
            return Response(
                'You have selected a format that does not exist for the view of Samples you selected. ' +
                'Please choose one of ' + ', '.join(views_formats[view]) + '.',
                status=400,
                mimetype='text/plain')
        else:
            format = request.args.get('_format').replace(' ', '+')
    else:
        format = 'text/html'

    # select view and format
    if view == 'alternates':
        return render_template(
            'sample.html',
            base_uri=settings.BASE_URI,
            web_subfolder=settings.WEB_SUBFOLDER,
            view=view,
            alternates_html=render_template('view_alternates.html', views_formats=views_formats)
        )
    elif view in ['igsn', 'dc']:
        # for all these views we will need to populate a sample
        from sample import sample
        s = sample.Sample()
        s.populate_from_xml_file('test/sample_eg2.xml')

        if format in ['text/turtle', 'application/rdf+xml', 'application/rdf+json']:
            file_extension = {
                'text/turtle': '.ttl',
                'application/rdf+xml': '.rdf',
                'application/rdf+json': '.json'
            }
            return Response(
                s.export_as_rdf(
                    model_view=view,
                    rdf_mime=format),
                status=200,
                mimetype=format,
                headers={'Content-Disposition': 'attachment; filename=' + igsn + file_extension[format]}
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
    return render_template(
        'samples.html',
        base_uri=settings.BASE_URI,
        web_subfolder=settings.WEB_SUBFOLDER,
    )
