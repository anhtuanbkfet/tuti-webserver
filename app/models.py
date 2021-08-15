from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'tb_user'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    usertype = db.Column(db.String(255))

    def __repr__(self):
        return '<User %r>' % self.name


class Action(db.Model):
    __tablename__ = 'tb_actions'
    action_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    last_action_id = db.Column(db.Integer)
    action_type = db.Column(db.Integer)
    time_start = db.Column(db.BigInteger)
    description = db.Column(db.String(255))
    is_latest_action = db.Column(db.Boolean)

    def __init__(self, user_id, last_action_id, action_type, time_start, description=None, is_latest_action = True):
        self.user_id = user_id
        self.last_action_id = last_action_id
        self.action_type = action_type
        self.time_start = time_start
        self.description = description
        self.is_latest_action = is_latest_action
