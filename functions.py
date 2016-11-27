def validate_view(request, views_formats):
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


def validate_format():
    pass


def get_default_view():
    pass