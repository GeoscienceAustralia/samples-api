"""
A list of functions for use anywhere but particularly in routes.py
"""
from flask import Response, render_template
import settings


def get_file_extension(mimetype):
    """
    Matches the file extension to MIME types

    :param mimetype: an HTTP mime type
    :return: a string
    """
    file_extension = {
        'text/turtle': '.ttl',
        'application/rdf+xml': '.rdf',
        'application/rdf+json': '.json',
        'application/xml': '.xml',
        'text/xml': '.xml',
    }

    return file_extension[mimetype]


def an_int(s):
    """
    Safely (no Error throw) tests to see whether a string can be itnerpreted as an int

    :param s: string
    :return: boolean
    """
    if s is not None:
        try:
            int(s)
            return True
        except ValueError:
            return False
    else:
        return False


def valid_view(view, views_formats):
    """
    Determines whether a requested model view is valid and, if it is, it returns it

    :return: view name (string) or False
    """
    if view is not None:
        if view in views_formats.iterkeys():
            return view
        else:
            raise ParameterError(
                'The _view parameter is invalid. For this object, it must be one of {0}'
                .format(', '.join(views_formats.iterkeys()))
            )
    else:
        # views_formats will give us the default view
        return views_formats['default']


def valid_format(format, view, views_formats):
    """
    Determines whether a requested format for a particular model view is valid and, if it is, it returns it

    :return: view name (string) or False
    """
    if format is not None:
        if format.replace(' ', '+') in views_formats[view]:
            return format.replace(' ', '+')
        else:
            raise ParameterError(
                'The _format parameter is invalid. For this model view, format should be one of {0}'
                .format(', '.join(views_formats[view]))
            )
    else:
        # HTML is default
        return 'text/html'


def get_valid_view_and_format(view, format, views_formats):
    """
    If both the view and the format are valid, return them
    :param view: the model view parameter
    :param format: the MIMETYPE format parameter
    :param views_formats: the allowed views and their formats in this instance
    :return: valid view and format
    """
    view = valid_view(view, views_formats)
    format = valid_format(format, view, views_formats)
    if view and format:
        # return valid view and format
        return view, format


def client_error_Response(error_message):
    return Response(
        error_message,
        status=400,
        mimetype='text/plain'
    )


def render_templates_alternates(parent_template, views_formats):
    return render_template(
        parent_template,
        base_uri=settings.BASE_URI,
        web_subfolder=settings.WEB_SUBFOLDER,
        view='alternates',
        placed_html=render_template('view_alternates.html', views_formats=views_formats)
    )


class ParameterError(ValueError):
    pass
