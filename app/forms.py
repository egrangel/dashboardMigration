from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ConfigurationForm(FlaskForm):
    config_id = StringField('Configuration ID')
    config_name = StringField('Configuration Name', validators=[DataRequired()])
    es_url = StringField('Elasticsearch URL', validators=[DataRequired()])
    es_port = StringField('Elasticsearch Port', validators=[DataRequired()])
    kb_url = StringField('Kibana URL', validators=[DataRequired()])
    kb_port = StringField('Kibana Port', validators=[DataRequired()])
    es_user = StringField('Elasticsearch User', validators=[DataRequired()])
    es_pass = PasswordField('Elasticsearch Password', validators=[DataRequired()])
    es_index_name = StringField('Elasticsearch Index Name', validators=[DataRequired()])
    submit = SubmitField('Save Configuration')