from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_matrix = db.Column(db.Text, nullable=False) 
    input_vector = db.Column(db.Text, nullable=False) 
    status = db.Column(db.String(20), nullable=False, default='pending') 
    progress = db.Column(db.Integer, default=0)
    result_gaussian = db.Column(db.Text, nullable=True) 
    error_message = db.Column(db.Text, nullable=True) 
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.id} by User {self.user_id}>'