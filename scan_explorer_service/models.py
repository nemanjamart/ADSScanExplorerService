from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship

Base = declarative_base()


class JournalVolume(Base):
    __tablename__ = 'journal_volume'

    id = Column(Integer, primary_key=True, autoincrement=True)
    journal = Column(String)
    volume = Column(String)
    type = Column(String)


page_article_association_table = Table('page2article', Base.metadata,
    Column('page_id', ForeignKey('page.id'), primary_key=True),
    Column('article_id', ForeignKey('article.id'), primary_key=True)
)

class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bibcode = Column(String)
    journal_volume_id = Column(Integer, ForeignKey(JournalVolume.id))
    pages = relationship('Page', secondary=page_article_association_table, back_populates='articles', lazy='dynamic')

class Page(Base):
    __tablename__ = 'page'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    label = Column(String)
    format = Column(String, default='image/tiff')
    color_type = Column(String)
    page_type = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    journal_volume_id = Column(Integer, ForeignKey(JournalVolume.id))
    volume_running_page_num = Column(Integer)
    articles = relationship('Article', secondary=page_article_association_table, back_populates='pages')

    UniqueConstraint(journal_volume_id, volume_running_page_num)