from flask import Blueprint, current_app
from presentation_api.models import Page
from presentation_api.extensions import manifest_factory

bp_canvas = Blueprint('canvas', __name__)

@bp_canvas.route('/canvas/<string:page_id>.json', methods=['GET'])
def get_canvas(page_id: str):
    with current_app.session_scope() as session:
        page = session.query(Page).filter(Page.id == page_id).first()

        if page:
            page = manifest_factory.create_canvas(page)
            return page.toJSON(top=True)
