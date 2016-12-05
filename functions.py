"""
A list of functions for use anywhere but particularly in routes.py
"""
from flask import Response, render_template
import settings


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
