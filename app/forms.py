from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired

class UserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = StringField('Password', validators=[InputRequired()])
    name = StringField('Your name', validators=[InputRequired()])
    usertype = StringField('User-type (admin/normal)', validators=[InputRequired()], default='admin')
