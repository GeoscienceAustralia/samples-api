import logging
import settings
from flask import Flask
from routes import pages, model_classes, oai
app = Flask(__name__)

app.register_blueprint(pages.pages)
app.register_blueprint(model_classes.model_classes)
app.register_blueprint(oai.oai_)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=settings.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(port=settings.PORT,
            debug=settings.DEBUG)
