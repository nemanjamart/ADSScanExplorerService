import uuid
from flask import current_app
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Session
from sqlalchemy_utils.types import UUIDType
import enum

Base = declarative_base()


class VolumeStatus(enum.Enum):
    """Volume ingestion status"""
    New = 1
    Processing = 2
    Update = 3
    Done = 4
    Error = 5


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


class JournalVolume(Base):
    __tablename__ = 'journal_volume'

    def __init__(self, type, journal, volume):
        self.type = type
        self.journal = journal
        self.volume = volume

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    journal = Column(String)
    volume = Column(String)
    type = Column(String)
    status = Column(Enum(VolumeStatus))
    file_hash = Column(String)


page_article_association_table = Table('page2article', Base.metadata,
                                       Column('page_id', ForeignKey(
                                           'page.id'), primary_key=True),
                                       Column('article_id', ForeignKey(
                                           'article.id'), primary_key=True)
                                       )


class Article(Base):
    __tablename__ = 'article'

    def __init__(self, bibcode, journal_volume_id):
        self.bibcode = bibcode
        self.journal_volume_id = journal_volume_id

    id = Column(UUIDType, default=uuid.uuid4, primary_key=True)
    bibcode = Column(String)
    journal_volume_id = Column(UUIDType, ForeignKey(JournalVolume.id))
    pages = relationship('Page', secondary=page_article_association_table,
                         back_populates='articles', lazy='dynamic')
    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'bibcode': self.bibcode,
            'pages': self.pages.count(),
            'thumbnail': f'{current_app.config.get("IMAGE_API_BASE_URL")}/{self.pages.first().name}/square/480,480/0/default.png'
        }

class Page(Base):
    __tablename__ = 'page'

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

    UniqueConstraint(journal_volume_id, volume_running_page_num)
