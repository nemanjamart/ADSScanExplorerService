from urllib.parse import parse_qs
from flask import Blueprint, current_app, jsonify, request
from scan_explorer_service.models import Article, Collection, Page
from flask_discoverer import advertise
from scan_explorer_service.search_utils import *
from flask_sqlalchemy import Pagination
from scan_explorer_service.open_search import EsFields, text_search_aggregate_ids
from sqlalchemy.orm import load_only


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

    
@advertise(scopes=['post_article'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article', methods=['POST'])
def post_article():
    json = request.get_json()
    if json:
        try:
            article = Article(**json)
            with current_app.session_scope() as session:
                session.add(article)
                session.commit()
                session.refresh(article)
                return jsonify({'id': article.id}), 200
        except:
            return jsonify(message='Failed to create article'), 500
    else:
        return jsonify(message='Invalid article json'), 400

@advertise(scopes=['post_collection'], rate_limit=[300, 3600*24])
@bp_metadata.route('/collection', methods=['POST'])
def post_collection():
    json = request.get_json()
    if json:
        try:
            collection = Collection(**json)
            with current_app.session_scope() as session:
                session.add(collection)
                session.commit()
                session.refresh(collection)
                return jsonify({'id': collection.id}), 200
        except:
            return jsonify(message='Failed to create collection'), 500
    else:
        return jsonify(message='Invalid collection json'), 400


@advertise(scopes=['post_page'], rate_limit=[300, 3600*24])
@bp_metadata.route('/page', methods=['POST'])
def post_page():
    json = request.get_json()
    if json:
        try:
            page = Page(**json)
            with current_app.session_scope() as session:
                session.add(page)
                session.commit()
                session.refresh(page)
                return jsonify({'id': page.id}), 200
        except:
            return jsonify(message='Failed to create page'), 500
    else:
        return jsonify(message='Invalid page json'), 400


@advertise(scopes=['article_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article/search', methods=['GET'])
def article_search():
    qs_dict, page, limit = parse_query_args(request.args)

    query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}
    jv_query_trans = {key: filter_func for key, filter_func in collection_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(Article)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))

        if len(jv_query_trans) > 0:
            query = query.join(Collection)
            for key, filter_func in jv_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        if 'full' in qs_dict.keys():
            item_ids = [str(a.id) for a in query.options(load_only('id')).all()]
            es_ids = text_search_aggregate_ids(qs_dict.get('full'), EsFields.article_id, item_ids)
            query = query.filter(Article.id.in_(es_ids))

        result: Pagination = query.group_by(Article.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result, qs_dict.get('full', '')))


@advertise(scopes=['collection_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/collection/search', methods=['GET'])
def collection_search():
    qs_dict, page, limit = parse_query_args(request.args)

    query_trans = {key: filter_func for key, filter_func in collection_query_translations.items() if key in qs_dict.keys()}
    a_query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(Collection)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))
        
        if len(a_query_trans) > 0:
            query = query.join(Article)
            for key, filter_func in a_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        
        if 'full' in qs_dict.keys():
            item_ids = [str(a.id) for a in query.options(load_only('id')).all()]
            es_ids = text_search_aggregate_ids(qs_dict.get('full'), EsFields.volume_id, item_ids)
            query = query.filter(Collection.id.in_(es_ids))

        result: Pagination = query.group_by(Collection.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result, qs_dict.get('full', '')))


@advertise(scopes=['page_search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/page/search', methods=['GET'])
def page_search():
    qs_dict, page, limit = parse_query_args(request.args)
    query_trans = {key: filter_func for key, filter_func in page_query_translations.items() if key in qs_dict.keys()}
    a_query_trans = {key: filter_func for key, filter_func in article_query_translations.items() if key in qs_dict.keys()}
    jw_query_trans = {key: filter_func for key, filter_func in collection_query_translations.items() if key in qs_dict.keys()}

    with current_app.session_scope() as session:
        query = session.query(Page)
        for key, filter_func in query_trans.items():
            query = query.filter(filter_func(qs_dict.get(key)))
        
        if len(a_query_trans) > 0:
            query = query.join(Article, Page.articles)
            for key, filter_func in a_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        if len(jw_query_trans) > 0:
            query = query.join(Collection)
            for key, filter_func in jw_query_trans.items():
                query = query.filter(filter_func(qs_dict.get(key)))

        if 'full' in qs_dict.keys():
            item_ids = [str(a.id) for a in query.options(load_only('id')).all()]
            es_ids = text_search_aggregate_ids(qs_dict.get('full'), EsFields.page_id, item_ids)
            query = query.filter(Page.id.in_(es_ids))
                
        result: Pagination = query.group_by(Page.id).paginate(page, limit, False)

        return jsonify(serialize_result(session, result, qs_dict.get('full', '')))


