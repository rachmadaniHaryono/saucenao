"""Models module."""
from datetime import datetime
import os
import os.path as op

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TIMESTAMP
from sqlalchemy_utils.types import URLType, ChoiceType

from .saucenao import SauceNao


db = SQLAlchemy()
content_tags = db.Table(
    'content_tags',
    db.Column('content_id', db.Integer, db.ForeignKey('content.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True))
result_urls = db.Table(
    'result_urls',
    db.Column('result_id', db.Integer, db.ForeignKey('result.id'), primary_key=True),
    db.Column('url_id', db.Integer, db.ForeignKey('url.id'), primary_key=True))
result_contents = db.Table(
    'result_contents',
    db.Column('result_id', db.Integer, db.ForeignKey('result.id'), primary_key=True),
    db.Column('content_id', db.Integer, db.ForeignKey('content.id'), primary_key=True))
search_results = db.Table(
    'search_results',
    db.Column('search_id', db.Integer, db.ForeignKey('search.id'), primary_key=True),
    db.Column('result_id', db.Integer, db.ForeignKey('result.id'), primary_key=True))
search_checksums = db.Table(
    'search_checksums',
    db.Column('search_id', db.Integer, db.ForeignKey('search.id'), primary_key=True),
    db.Column('checksum_id', db.Integer, db.ForeignKey('checksum.id'), primary_key=True))


class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


class SingleStringValueModel(Base):
    __abstract__ = True
    value = db.Column(db.String)


class Url(Base):
    value = db.Column(URLType)


class Title(SingleStringValueModel):
    def __str__(self):
        return '<Title {0.id} {0.value}>'


class Namespace(SingleStringValueModel):
    def __str__(self):
        return '<Namespace {0.id} {0.value}>'


class Tag(SingleStringValueModel):
    namespace_id = db.Column(db.Integer, db.ForeignKey('namespace.id'))
    namespace = db.relationship(
        'Namespace', foreign_keys='Tag.namespace_id', lazy='subquery',
        backref=db.backref('tags', lazy=True))


class Content(SingleStringValueModel):
    tags = db.relationship(
        'Tag', secondary=content_tags, lazy='subquery',
        backref=db.backref('contents', lazy=True))


class Result(Base):
    title_id = db.Column(db.Integer, db.ForeignKey('title.id'))
    title = db.relationship(
        'Title', foreign_keys='Result.title_id', lazy='subquery',
        backref=db.backref('results', lazy=True))
    contents = db.relationship(
        'Content', secondary=result_contents, lazy='subquery',
        backref=db.backref('results', lazy=True))
    similarity = db.Column(db.Integer)
    external_urls = db.relationship(
        'Url', secondary=result_urls, lazy='subquery',
        backref=db.backref('results', lazy=True))


class Checksum(SingleStringValueModel):
    TYPE_SHA256 = 'sha256'
    TYPE_MD5 = 'md5'
    TYPES = [
        (TYPE_SHA256, 'sha256'),
        (TYPE_MD5, 'md5')
    ]
    type = db.Column(ChoiceType(TYPES))

    def __str__(self):
        return '<Checksum {0.id} {0.type} {0.value}>'.format(self)


class Search(Base):
    TYPES = [
        (str(SauceNao.API_HTML_TYPE), 'HTML type'),
        (str(SauceNao.API_JSON_TYPE), 'JSON type')
    ]
    output_type = db.Column(ChoiceType(TYPES))
    checksums = db.relationship(
        'Checksum', secondary=search_checksums, lazy='subquery',
        backref=db.backref('searchs', lazy=True))
    combine_api_types = db.Column(db.Boolean)
    results = db.relationship(
        'Result', secondary=search_results, lazy='subquery',
        backref=db.backref('searchs', lazy=True))


def get_or_create(session, model, **kwargs):
    """Creates an object or returns the object if exists."""
    instance = session.query(model).filter_by(**kwargs).first()
    created = False
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        created = True
    return instance, created
