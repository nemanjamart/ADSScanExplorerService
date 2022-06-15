import uuid
from flask import current_app
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import UUIDType
from sqlalchemy_utils.models import Timestamp
import enum

Base = declarative_base()

class PageColor(enum.Enum):
    """Page Color Type"""
    BW = 1
    Greyscale = 2
    Color = 3

class PageType(enum.Enum):
    """Page Type."""
    Normal = 1
    FrontMatter = 2
    BackMatter = 3
    Insert = 4
    Plate = 5

    @classmethod
    def from_string(self, val: str):
        elist = [{'name': e.name, 'value': e.value, 'enum': e} for e in PageType]

        for edict in elist:
            if edict.get('name').lower() == val.lower():
                return edict.get('enum')
            elif val.isnumeric() and int(val) == edict.get('value'):
                return edict.get('enum')

        return PageType.Normal

class Collection(Base, Timestamp):
    
    def __init__(self, type, journal, volume, articles = []):
        self.type = type
        self.journal = journal
        self.volume = volume

        for article in articles:
            article['collection_id'] = self.id
            self.articles.append(Article(**article))

    __tablename__ = 'collection'
    __table_args__ = (Index('volume_index', "journal", "volume"), )

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    journal = Column(String)
    volume = Column(String)
    type = Column(String)

    articles = relationship(
        'Article', primaryjoin='Collection.id==Article.collection_id', back_populates='collection')
    pages = relationship(
        'Page', primaryjoin='Collection.id==Page.collection_id', back_populates='collection',  lazy='dynamic', order_by="Page.volume_running_page_num")

    UniqueConstraint(journal, volume)

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'journal': self.journal,
            'volume': self.volume,
            'pages': self.pages.count(),
            'thumbnail': self.pages.first().thumbnail_url
        }


page_article_association_table = Table('page2article', Base.metadata,
                                       Column('page_id', ForeignKey(
                                           'page.id'), primary_key=True),
                                       Column('article_id', ForeignKey(
                                           'article.id'), primary_key=True)
                                       )


class Article(Base, Timestamp):
    __tablename__ = 'article'
    __table_args__ = (Index('article_volume_index', "collection_id"), Index('article_bibcode_index', "bibcode"))


    def __init__(self, bibcode, collection_id, pages=[]):
        self.bibcode = bibcode
        self.collection_id = collection_id
        for page in pages:
            page['collection_id'] = collection_id
            self.pages.append(Page(**page))

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    bibcode = Column(String)
    collection_id = Column(UUIDType, ForeignKey(Collection.id))

    collection = relationship('Collection', back_populates='articles')
    pages = relationship('Page', secondary=page_article_association_table,
                         back_populates='articles', lazy='dynamic', order_by="Page.volume_running_page_num")

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'type': 'article',
            'bibcode': self.bibcode,
            'pages': self.pages.count(),
            'thumbnail': self.pages.first().thumbnail_url,
            'collection_id': self.collection_id
        }


class Page(Base, Timestamp):
    __tablename__ = 'page'
    __table_args__ = (Index('page_volume_index', "collection_id"), Index('page_name_index', "name"))

    def __init__(self, name, label, format, color_type, page_type, width, height, collection_id, volume_running_page_num):
        self.name = name
        self.label = label
        self.format = format,
        self.color_type = color_type
        self.page_type = page_type
        self.width = width
        self.height = height
        self.collection_id = collection_id
        self.volume_running_page_num = volume_running_page_num

    id = Column(UUIDType, default=uuid.uuid4,  primary_key=True)
    name = Column(String)
    label = Column(String)
    format = Column(String, default='image/tiff')
    color_type = Column(Enum(PageColor))
    page_type = Column(Enum(PageType))
    width = Column(Integer)
    height = Column(Integer)
    collection_id = Column(UUIDType, ForeignKey(Collection.id))
    volume_running_page_num = Column(Integer)
    articles = relationship('Article', secondary=page_article_association_table, back_populates='pages')
    collection = relationship('Collection', back_populates='pages')

    UniqueConstraint(collection_id, volume_running_page_num)
    UniqueConstraint(collection_id, name)

    @property
    def image_url(self):
        image_api_url = current_app.config.get('IMAGE_API_BASE_URL')
        return f'{image_api_url}/{self.image_path}'
    
    @property
    def image_path(self):
        image_path = f'bitmaps%2F{self.collection.type}%2F{self.collection.journal}%2F{self.collection.volume}%2F600'
        image_path = image_path.replace('.', '_')
        image_path += f'%2F{self.name}'
        if self.color_type != PageColor.BW:
            image_path += '.tif'
        return image_path

    @property
    def thumbnail_url(self):
        return f'{self.image_url}/square/480,480/0/default.jpg'

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'label': self.label,
            'collection_id': self.collection_id,
            'volume_page_num': self.volume_running_page_num,
            'articles': [a.id for a in self.articles],
            'thumbnail': self.thumbnail_url
        }