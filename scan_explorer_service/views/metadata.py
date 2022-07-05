from flask import Blueprint, current_app, jsonify, request
from scan_explorer_service.db_utils import article_get_or_create, article_overwrite, collection_overwrite, page_get_or_create, page_overwrite
from scan_explorer_service.models import Article, Collection, Page
from flask_discoverer import advertise
from scan_explorer_service.search_utils import *
from scan_explorer_service.views.view_utils import ApiErrors
from scan_explorer_service.open_search import EsFields, page_os_search, aggregate_search
from sqlalchemy.orm import load_only
from sqlalchemy import func

bp_metadata = Blueprint('metadata', __name__, url_prefix='/metadata')


@advertise(scopes=['ads:scan-explorer'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article', methods=['PUT'])
def put_article():
    json = request.get_json()
    if json:
        with current_app.session_scope() as session:
            try:
                article = Article(**json)
                article_overwrite(session, article)
                return jsonify({'id': article.bibcode}), 200
            except:
                session.rollback()
                return jsonify(message='Failed to create article'), 500
    else:
        return jsonify(message='Invalid article json'), 400


@advertise(scopes=['ads:scan-explorer'], rate_limit=[300, 3600*24])
@bp_metadata.route('/collection', methods=['PUT'])
def put_collection():
    json = request.get_json()
    if json:
        with current_app.session_scope() as session:
            try:
                collection = Collection(**json)
                collection_overwrite(session, collection)
                
                for page_json in json.get('pages', []):
                    page_json['collection_id'] = collection.id
                    page = page_get_or_create(session, **page_json)

                    for article_json in page_json.get('articles', []):
                        article_json['collection_id'] = collection.id
                        page.articles.append(article_get_or_create(session, **article_json))

                    session.add(page)
                session.commit()

                return jsonify({'id': collection.id}), 200
            except:
                session.rollback()
                return jsonify(message='Failed to create collection'), 500
    else:
        return jsonify(message='Invalid collection json'), 400


@advertise(scopes=['ads:scan-explorer'], rate_limit=[300, 3600*24])
@bp_metadata.route('/page', methods=['PUT'])
def put_page():
    json = request.get_json()
    if json:
        with current_app.session_scope() as session:
            try:
                page = Page(**json)
                page_overwrite(session, page)

                for article_json in json.get('articles', []):
                    article_json['collection_id'] = page.collection_id
                    page.articles.append(article_get_or_create(session, **article_json))

                session.add(page)
                session.commit()
                session.refresh(page)
                return jsonify({'id': page.id}), 200
            except:
                session.rollback()
                return jsonify(message='Failed to create page'), 500
    else:
        return jsonify(message='Invalid page json'), 400


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_metadata.route('/article/search', methods=['GET'])
def article_search():
    try:
        qs_dict, page, limit = parse_query_args(request.args)
        result = aggregate_search(qs_dict, EsFields.article_id, page, limit)
        text_query = ''
        if SearchOptions.FullText.value in qs_dict.keys():
            text_query = qs_dict[SearchOptions.FullText.value]
        return jsonify(serialize_os_article_result(result, page, limit, text_query))
    except Exception as e:
        return jsonify(message=str(e), type=ApiErrors.SearchError.value), 400


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_metadata.route('/collection/search', methods=['GET'])
def collection_search():
    try:
        qs_dict, page, limit = parse_query_args(request.args)
        result = aggregate_search(qs_dict, EsFields.volume_id, page, limit)
        text_query = ''
        if SearchOptions.FullText.value in qs_dict.keys():
            text_query = qs_dict[SearchOptions.FullText.value]
        return jsonify(serialize_os_collection_result(result, page, limit, text_query))
    except Exception as e:
        return jsonify(message=str(e), type=ApiErrors.SearchError.value), 400

@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_metadata.route('/page/search', methods=['GET'])
def page_search():
    try:
        qs_dict, page, limit = parse_query_args(request.args)
        result = page_os_search(qs_dict, page, limit)
        text_query = ''
        if SearchOptions.FullText.value in qs_dict.keys():
            text_query = qs_dict[SearchOptions.FullText.value]
        return jsonify(serialize_os_page_result(result, page, limit, text_query))
    except Exception as e:
        return jsonify(message=str(e), type=ApiErrors.SearchError.value), 400