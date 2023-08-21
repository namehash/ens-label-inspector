from mangum import Mangum
from label_inspector.web_api import app


handler = Mangum(app, lifespan='off')
