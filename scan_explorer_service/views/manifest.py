from flask import Blueprint, Response, current_app, jsonify, url_for, request
from requests import get
from scan_explorer_service.extensions import manifest_factory
from scan_explorer_service.models import Article, Page, Collection
from flask_discoverer import advertise
from scan_explorer_service.open_search import EsFields, text_search_highlight
from urllib import parse as urlparse
from typing import Union
import requests

bp_manifest = Blueprint('manifest', __name__, url_prefix='/manifest')


@bp_manifest.before_request
def before_request():
    base_uri = urlparse.urljoin(request.host_url, bp_manifest.url_prefix)
    manifest_factory.set_base_prezi_uri(base_uri)

    image_proxy = urlparse.urljoin(request.host_url, url_for('proxy.image_proxy', path=''))
    manifest_factory.set_base_image_uri(image_proxy)


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_manifest.route('/<string:id>/manifest.json', methods=['GET'])
def get_manifest(id: str):
    """ Creates an IIIF manifest from an article or Collection"""
    with current_app.session_scope() as session:
        item: Union[Article, Collection] = (
            session.query(Article).filter(Article.id == id).one_or_none()
            or session.query(Collection).filter(Collection.id == id).one_or_none())

        if item:
            manifest = manifest_factory.create_manifest(item)
            search_url = urlparse.urljoin(
                request.host_url, url_for('manifest.search', id=id))
            manifest_factory.add_search_service(manifest, search_url)

            return manifest.toJSON(top=True)
        else:
            return jsonify(exception='Article not found'), 404


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_manifest.route('/canvas/<string:page_id>.json', methods=['GET'])
def get_canvas(page_id: str):
    """ Creates an IIIF canvas from a page"""
    with current_app.session_scope() as session:
        page = session.query(Page).filter(Page.id == page_id).first()
        if page:
            canvas = manifest_factory.get_or_create_canvas(page)
            return canvas.toJSON(top=True)
        else:
            return jsonify(exception='Page not found'), 404


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_manifest.route('/<string:id>/search', methods=['GET'])
def search(id: str):
    """ Searches the content of an article """

    query = request.args.get('q')
    if not query or len(query) <= 0:
        return jsonify(exception='No search query specified'), 400

    with current_app.session_scope() as session:
        item: Union[Article, Collection] = (
                    session.query(Article).filter(Article.id == id).one_or_none()
                    or session.query(Collection).filter(Collection.id == id).one_or_none())
        if item:
            annotation_list = manifest_factory.annotationList(request.url)
            annotation_list.resources = []
            
            es_field = EsFields.article_id if isinstance(item, Article) else EsFields.volume_id
            results = text_search_highlight(query, es_field, [item.id])

            for res in results:
                annotation = annotation_list.annotation(res['page_id'])
                canvas_slice_url = ''.join([url_for('manifest.get_canvas', page_id=res['page_id'])])
                annotation.on = urlparse.urljoin(request.url_root, canvas_slice_url)
                highlight_text = "<br><br>".join(res['highlight']).replace("em>", "b>")
                annotation.text(highlight_text, format="text/html")

            return annotation_list.toJSON(top=True)


        else:
            return jsonify(exception='Article or volume not found'), 404
