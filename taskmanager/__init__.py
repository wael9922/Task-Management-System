from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_restful import Api
from taskmanager.config import Config


app = Flask(__name__)
app.config.from_object(Config)


db = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)
api = Api(app)

login_manager.login_view = 'login'


# def create_app(class_config=Config):
#     app = Flask(__name__)
#     app.config.from_object(class_config)
#     db.init_app(app)
#     login_manager.init_app(app)
#     bcrypt.init_app(app)
#     mail.init_app(app)
#     jwt.init_app(app)
#     api.init_app(app)
#
#     login_manager.login_view = 'login'
#     return app


from taskmanager import routes
from taskmanager import endpoints