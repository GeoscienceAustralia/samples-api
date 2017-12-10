import logging
import _config as conf
from flask import Flask
from controller import pages, classes, oai

app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)

app.register_blueprint(pages.pages)
app.register_blueprint(classes.classes)
app.register_blueprint(oai.oai_)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(debug=conf.DEBUG)
