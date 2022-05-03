from flask import Blueprint, current_app
from presentation_api.models import Article, Page
from presentation_api.extensions import manifest_factory

# define the blueprint
bp_canvas= Blueprint('canvas', __name__)

@bp_canvas.route('/<string:article_id>/canvas/<string:page_id>.json', methods=['GET'])
def get_canvas(article_id: str, page_id: str):
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            page = session.query(Page).filter_by(id=page_id).first()
            if page:
                canvas = manifest_factory.canvas(ident=page.id, label=page.label)
                canvas.height = page.height
                canvas.width = page.width

                annotation = canvas.annotation(ident=page.id)

                image = annotation.image(ident=page.id, label=page.label, iiif=True)
                image.format = page.format
                image.height = page.height
                image.width = page.width
        
                return canvas.toJSON(top = True)


