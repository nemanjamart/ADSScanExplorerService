from flask import Blueprint, current_app, jsonify, request
from scan_explorer_service.models import Article, JournalVolume, Page
from flask_discoverer import advertise
from scan_explorer_service.search_utils import QueryBuilder

bp_metadata = Blueprint('metadata', __name__, url_prefix='/service/metadata')


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


@advertise(scopes=['search'], rate_limit=[300, 3600*24])
@bp_metadata.route('/search', methods=['GET'])
def search():
    qb = QueryBuilder(request)
    result = qb.query(current_app)
    return jsonify(result)
