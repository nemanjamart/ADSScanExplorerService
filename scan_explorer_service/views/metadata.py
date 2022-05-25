from urllib.parse import parse_qs
from flask import Blueprint, current_app, jsonify, request
from scan_explorer_service.models import Article, JournalVolume, Page
from flask_discoverer import advertise
from scan_explorer_service.search_utils import *
from flask_sqlalchemy import Pagination
from scan_explorer_service.elasticsearch import text_search_aggregate


bp_metadata = Blueprint('metadata', __name__, url_prefix='/metadata')


@advertise(scopes=['get_articles'], rate_limit=[300, 3600*24])
@bp_metadata.route('/articles', methods=['GET'])
def get_articles():
    """ Fetch all articles or all articles corresponding to a bibcode """
    with current_app.session_scope() as session:
        bibcode = request.args.get('bibcode')
        if bibcode:
            articles = session.query(Article).filter(
                Article.bibcode.ilike(f'%{bibcode}%')).all()
        else:
            articles = session.query(Article).all()

        return jsonify([article.serialized for article in articles])


@advertise(scopes=['get_article'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article', methods=['GET'])
def get_article():
    """ Tries to find an article that is an exact match of the provided bibcode"""
    with current_app.session_scope() as session:
        bibcode = request.args.get('bibcode')
        if bibcode:
            article = session.query(Article).filter(
                Article.bibcode == bibcode).first()
            if article:
                return jsonify(article.serialized)
            else:
                return ''
        else:
            return jsonify(message='No bibcode provided'), 400


@advertise(scopes=['article_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article/search', methods=['GET'])
def article_search():
    qs_dict, page, limit = parse_query_args(request.args)
    if 'full' in qs_dict.keys():
      return text_search(True)
    query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}
    jv_query_trans = {key: filter_func for key, filter_func in journal_volume_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(Article)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))

        if len(jv_query_trans) > 0:
            query = query.join(JournalVolume)
            for key, filter_func in jv_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        result: Pagination = query.group_by(Article.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result))



@advertise(scopes=['collection_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/collection/search', methods=['GET'])
def collection_search():
    qs_dict, page, limit = parse_query_args(request.args)
    if 'full' in qs_dict.keys():
        return text_search(False)

    query_trans = {key: filter_func for key, filter_func in journal_volume_query_translations.items() if key in qs_dict.keys()}
    a_query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(JournalVolume)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))
        
        if len(a_query_trans) > 0:
            query = query.join(Article)
            for key, filter_func in a_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))
                
        result: Pagination = query.group_by(JournalVolume.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result))

def text_search(is_article_search: bool):
    qs_dict, page, limit = parse_query_args(request.args)
    v_query_trans = {key: filter_func for key, filter_func in journal_volume_query_translations.items() if key in qs_dict.keys()}
    a_query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}

    volume_ids = []
    article_ids = []
    full_text = qs_dict['full']

    with current_app.session_scope() as session:
        if len(v_query_trans) > 0:
            query = session.query(JournalVolume)
            for key, filter_func in v_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))
            for vol in query.all():
                volume_ids.append(vol.id)

        if len(a_query_trans) > 0:
            query = session.query(Article)
            for key, filter_func in a_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))
            for article in query.all():
                article_ids.append(article.id)

        resp = text_search_aggregate(full_text, volume_ids, article_ids, is_article_search, page, limit)
        if is_article_search:
            return jsonify(serialize_es_article_result(session, resp, page, limit))
        else:
            return jsonify(serialize_es_volume_result(session, resp, page, limit))


@advertise(scopes=['page_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/page/search', methods=['GET'])
def page_search():
    qs_dict, page, limit = parse_query_args(request.args)
    query_trans = {key: filter_func for key, filter_func in page_query_translations.items() if key in qs_dict.keys()}
    a_query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}
    jw_query_trans = {key: filter_func for key, filter_func in journal_volume_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(Page)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))
        
        if len(a_query_trans) > 0:
            query = query.join(Article, Page.articles)
            for key, filter_func in a_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        if len(jw_query_trans) > 0:
            query = query.join(JournalVolume)
            for key, filter_func in jw_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))
                
        result: Pagination = query.group_by(Page.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result))