from flask import Blueprint, current_app
from presentation_api.extensions import manifest_factory
from presentation_api.models import Article

bp_manifest = Blueprint('manifest', __name__)

@bp_manifest.route('<string:article_id>/manifest.json', methods=['GET'])
def get_manifest(article_id: str):
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=article_id).first()

        if article:
            manifest = manifest_factory.create_manifest(article)

            # Adding a search service:
            # search_url = f'{current_app.config.get("BASE_URL")}/{article.id}/search'
            # service = manifest.add_service(ident=search_url, label=f'Search', context='http://iiif.io/api/search/1/context.json', profile='http://iiif.io/api/search/1/search')
            return manifest.toJSON(top = True)
        else:
            return 

