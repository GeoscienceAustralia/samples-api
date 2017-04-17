import logging
import config
from flask import Flask
from routes import pages, model_classes, oai
app = Flask(__name__)

app.register_blueprint(pages.pages)
app.register_blueprint(model_classes.model_classes)
app.register_blueprint(oai.oai_)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=config.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(debug=config.DEBUG)
