from flask import Flask
from database import init_db
from models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    init_db(app)
    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database initialized.")
