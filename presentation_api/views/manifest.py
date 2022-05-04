from flask import Blueprint, current_app, jsonify
from presentation_api.extensions import manifest_factory
from presentation_api.models import Article, Page
from flask_discoverer import advertise

bp_manifest = Blueprint('manifest', __name__)

@advertise(scopes=['get_manifest'], rate_limit = [300, 3600*24])
@bp_manifest.route('/<string:article_id>/manifest.json', methods=['GET'])
def get_manifest(article_id: str):
    """ Creates an IIIF manifest from an article"""
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            manifest = manifest_factory.create_manifest(article)

            # Adding a search service:
            #search_url = f'{current_app.config.get("BASE_URL")}/{article.id}/search'
            #service = manifest.add_service(ident=search_url, label=f'Search', context='http://iiif.io/api/search/1/context.json', profile='http://iiif.io/api/search/1/search')
            return manifest.toJSON(top=True)
        else:
            return jsonify(exception='Article not found'), 404


@advertise(scopes=['get_canvas'], rate_limit = [300, 3600*24])
@bp_manifest.route('/canvas/<string:page_id>.json', methods=['GET'])
def get_canvas(page_id: str):
    """ Creates an IIIF canvas from a page"""
    with current_app.session_scope() as session:
        page = session.query(Page).filter(Page.id == page_id).first()

        if page:
            page = manifest_factory.create_canvas(page)
            return page.toJSON(top=True)
        else:
            return jsonify(exception='Page not found'), 404
