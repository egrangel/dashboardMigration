from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Configuration(db.Model):
    config_id = db.Column(db.Integer, primary_key=True)
    config_name = db.Column(db.String(255), nullable=False)
    es_url = db.Column(db.String(255), nullable=False)
    es_port = db.Column(db.String(10), nullable=False)
    kb_url = db.Column(db.String(255), nullable=False)
    kb_port = db.Column(db.String(10), nullable=False)
    es_user = db.Column(db.String(255), nullable=False)
    es_pass = db.Column(db.String(255), nullable=False)
    es_index_name = db.Column(db.String(255), nullable=False)