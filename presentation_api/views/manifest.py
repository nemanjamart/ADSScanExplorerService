from flask import Blueprint, current_app
from presentation_api.extensions import manifest_factory
from iiif_prezi.factory import Sequence, Canvas, Image, Annotation
from presentation_api.models import Article, Page

# define the blueprint
bp_manifest = Blueprint('manifest', __name__)

@bp_manifest.route('<string:article_id>/manifest.json', methods=['GET'])
def get_manifest(article_id: str):
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            manifest_factory.set_base_prezi_uri(f'{current_app.config.get("BASE_URL")}/{str(article.id)}')
            manifest = manifest_factory.manifest(label="journal.volume")
            manifest.description = 'journal.description'

            sequence : Sequence = manifest.sequence()

            for page in article.pages:
                canvas : Canvas = sequence.canvas(ident=str(page.id), label=page.label)
                canvas.height = page.height
                canvas.width = page.width

                annotation : Annotation = canvas.annotation(ident=str(page.id))
                
                image : Image = annotation.image(ident=page.name, label=page.label, iiif=True)
                image.format = page.format
                image.height = page.height
                image.width = page.width
            
            #search_url = f'{current_app.config.get("BASE_URL")}/{article.id}/search'
            #service = manifest.add_service(ident=search_url, label=f'Search', context='http://iiif.io/api/search/1/context.json', profile='http://iiif.io/api/search/1/search')

            return manifest.toJSON(top = True)
