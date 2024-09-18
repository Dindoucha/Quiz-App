from flask import Flask
from flask_sqlalchemy import *
from flask_login import LoginManager
from decouple import config


db = SQLAlchemy()

DB_USERNAME = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')
DB_HOST = config('DB_HOST')
DB_NAME = config('DB_NAME')

def create_app() :
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'jkedjzmeoiepz'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    db.init_app(app)
    
    from .views import viewsBluprint
    from .auth import authBluprint
    app.register_blueprint(viewsBluprint, url_prefix='/')
    app.register_blueprint(authBluprint, url_prefix='/')

    from .models import User
    create_database(app)

    login_manager = LoginManager ()
    login_manager.login_view = 'authBluprint.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id) : 
        return User.query.get(int(id))
    return app


def create_database(app) : 
    with app.app_context():
        db.create_all()
        print('Created Database !')