from sqlalchemy import or_
from scan_explorer_service.models import Article, Collection, Page


def collection_exists(session, journal, volume):
    return session.query(Collection).filter(Collection.journal == journal).filter(Collection.volume == volume).first() is not None


def collection_get(session, journal, volume):
    return session.query(Collection).filter(Collection.journal == journal).filter(Collection.volume == volume).one_or_none()


def article_exists(session, bibcode):
    return session.query(Article).filter(Article.bibcode == bibcode).first() is not None


def article_get(session, bibcode):
    return session.query(Article).filter(Article.bibcode == bibcode).one_or_none()


def page_exists(session, collection_id, name, page_num):
    return session.query(Page).filter(Page.collection_id == collection_id).filter(
        or_(Page.name == name, Page.volume_running_page_num == page_num)).first() is not None


def page_get(session, collection_id, name, page_num):
    return session.query(Page).filter(Page.collection_id == collection_id).filter(
        or_(Page.name == name, Page.volume_running_page_num == page_num)).one_or_none()
