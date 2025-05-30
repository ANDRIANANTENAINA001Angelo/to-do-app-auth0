from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(150), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_sub = db.Column(db.String(100), nullable=False)

