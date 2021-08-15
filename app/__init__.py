import os
from flask import Flask, flash, redirect, url_for, request
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__name__))
db_path = os.path.join(basedir, 'database/tuti-web-service.db')
db_uri = 'sqlite:///{}'.format(db_path)


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '0'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

# to init database if not exist: 
# >>> from yourapplication import db
# >>> db.create_all()

db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from .models import User


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

# blueprint for auth routes in our app
from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

# for image explorer
from .explorer import explorer as explorer_blueprint
app.register_blueprint(explorer_blueprint)

# for TuTi serevice
from .tuti_service import tuti_service as tuti_service_blueprint
app.register_blueprint(tuti_service_blueprint)

app.config.from_object(__name__)
from app import error_handler



