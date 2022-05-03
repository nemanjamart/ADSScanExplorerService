from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String

Base = declarative_base()


class Article(Base):
    __tablename__ = 'article'

    id = Column(String, primary_key=True)


class Page(Base):
    __tablename__ = 'page'

    id = Column(String, primary_key=True)
    format = Column(String)
    label = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    article_id = Column(String, ForeignKey(Article.id))