"""Forms module."""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, BooleanField, SelectField, FloatField
from wtforms.validators import DataRequired, Optional

from . import models


class IndexForm(FlaskForm):
    upload = FileField('Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    output_type = SelectField(choices=models.Search.TYPES)
    combine_api_types = BooleanField()
    minimum_similarity = FloatField()
