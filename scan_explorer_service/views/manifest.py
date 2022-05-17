from flask import Blueprint, current_app, jsonify, url_for, request
from scan_explorer_service.extensions import manifest_factory
from scan_explorer_service.models import Article, Page, JournalVolume
from flask_discoverer import advertise
from urllib import parse as urlparse

bp_manifest = Blueprint('manifest', __name__, url_prefix='/service/manifest')


@bp_manifest.before_request
def before_request():
    base_uri = urlparse.urljoin(request.url_root, bp_manifest.url_prefix)
    manifest_factory.set_base_prezi_uri(base_uri)

@advertise(scopes=['get_manifest'], rate_limit = [300, 3600*24])
@bp_manifest.route('/<string:id>/manifest.json', methods=['GET'])
def get_manifest(id: str):
    """ Creates an IIIF manifest from an article"""
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=id).one_or_none()
        volume = session.query(JournalVolume).filter_by(id=id).one_or_none()
        if article or volume:
            if article:
                manifest = manifest_factory.create_manifest(article)
            else:
                manifest = manifest_factory.create_manifest_from_volume(volume)

            # TODO: Check if OCR is available before adding search service..
            search_url = urlparse.urljoin(request.url_root, url_for('manifest.search', id = id))
            manifest_factory.add_search_service(manifest, search_url)

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


@advertise(scopes=['search'], rate_limit = [300, 3600*24])
@bp_manifest.route('/<string:article_id>/search', methods=['GET'])
def search(article_id: str):
    """ Searches the content of an article """
    with current_app.session_scope() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            query = request.args.get('q')
            if query and len(query) > 0:
                

                # TODO: Here we should perform a search in the OCR text.
                # We need to know the page, x, y coordinates, width & height of
                # the OCR text matching the query.

                # Below code is an hard coded example.
                annotation_list = manifest_factory.annotationList(request.url)
                annotation_list.resources = []
                annotation = annotation_list.annotation('any_id')
                annotation.text('near-infrared')
                page = article.pages.first()
                canvas_slice_url = ''.join([url_for('manifest.get_canvas', page_id=page.id), '#xywh=675,2500,520,102'])
                annotation.on = urlparse.urljoin(request.url_root, canvas_slice_url)

                return annotation_list.toJSON(top=True)
            else:
                return jsonify(exception='No search query specified'), 400
        else:
            return jsonify(exception='Article not found'), 404
