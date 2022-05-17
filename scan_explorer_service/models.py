import uuid
from flask import current_app
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import UUIDType
from sqlalchemy_utils.models import Timestamp
import enum

Base = declarative_base()


class VolumeStatus(enum.Enum):
    """Volume ingestion status"""
    New = 1
    Processing = 2
    Update = 3
    Db_done = 4
    Bucket_done = 5
    Done = 6
    Error = 7

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

class JournalVolume(Base, Timestamp):
    
    def __init__(self, type, journal, volume):
        self.type = type
        self.journal = journal
        self.volume = volume

    __tablename__ = 'journal_volume'
    __table_args__ = (Index('volume_index', "journal", "volume"), )

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    journal = Column(String)
    volume = Column(String)
    type = Column(String)
    status = Column(Enum(VolumeStatus))
    status_message = Column(String)
    file_hash = Column(String)

    articles = relationship(
        'Article', primaryjoin='JournalVolume.id==Article.journal_volume_id', back_populates='volume')
    pages = relationship(
        'Page', primaryjoin='JournalVolume.id==Page.journal_volume_id', back_populates='volume', order_by="Page.volume_running_page_num")

    UniqueConstraint(journal, volume)

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'journal': self.journal,
            'volume': self.volume,
        }


page_article_association_table = Table('page2article', Base.metadata,
                                       Column('page_id', ForeignKey(
                                           'page.id'), primary_key=True),
                                       Column('article_id', ForeignKey(
                                           'article.id'), primary_key=True)
                                       )


class Article(Base, Timestamp):
    __tablename__ = 'article'
    __table_args__ = (Index('article_volume_index', "journal_volume_id"), Index('article_bibcode_index', "bibcode"))


    def __init__(self, bibcode, journal_volume_id):
        self.bibcode = bibcode
        self.journal_volume_id = journal_volume_id

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    bibcode = Column(String)
    journal_volume_id = Column(UUIDType, ForeignKey(JournalVolume.id))

    volume = relationship('JournalVolume', back_populates='articles')
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
            'journal_volume_id': self.journal_volume_id
        }


class Page(Base, Timestamp):
    __tablename__ = 'page'
    __table_args__ = (Index('page_volume_index', "journal_volume_id"), Index('page_name_index', "name"))

    def __init__(self, name, journal_volume_id):
        self.name = name
        self.journal_volume_id = journal_volume_id
        self.color_type = PageColor.BW

    id = Column(UUIDType, default=uuid.uuid4,  primary_key=True)
    name = Column(String)
    label = Column(String)
    format = Column(String, default='image/tiff')
    color_type = Column(Enum(PageColor))
    page_type = Column(Enum(PageType))
    width = Column(Integer)
    height = Column(Integer)
    journal_volume_id = Column(UUIDType, ForeignKey(JournalVolume.id))
    volume_running_page_num = Column(Integer)
    articles = relationship(
        'Article', secondary=page_article_association_table, back_populates='pages')

    volume = relationship('JournalVolume', back_populates='pages')
    UniqueConstraint(journal_volume_id, volume_running_page_num)
    UniqueConstraint(journal_volume_id, name)

    @property
    def image_url(self):
        image_api_url = current_app.config.get('IMAGE_API_BASE_URL')
       
        return f'{image_api_url}/{self.image_path}'
    
    @property
    def image_path(self):
        image_path = f'bitmaps%2F{self.volume.type}%2F{self.volume.journal}%2F{self.volume.volume}%2F600'
        image_path = image_path.replace('.', '_')
        return f'{image_path}%2F{self.name}'

    @property
    def thumbnail_url(self):
        return f'{self.image_url}/square/480,480/0/default.png'