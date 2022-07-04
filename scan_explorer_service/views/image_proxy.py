import re
from flask import Blueprint, Response, current_app, request, stream_with_context, jsonify
from flask_discoverer import advertise
from urllib import parse as urlparse
import requests
from scan_explorer_service.models import Article, Collection, Page


bp_proxy = Blueprint('proxy', __name__, url_prefix='/image')

@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_proxy.route('/iiif/2/<path:path>', methods=['GET'])
def image_proxy(path):
        req_url = urlparse.urljoin(f'{current_app.config.get("IMAGE_API_BASE_URL")}/', path)
        req_headers= {key: value for (key, value) in request.headers if key != 'Host' and key != 'Accept'}

        req_headers['X-Forwarded-Host'] = request.headers['HOST']
        req_headers['X-Forwarded-Path'] = req_headers.get('X-Forwarded-Prefix', '') + '/image'
        
        r = requests.request(request.method, req_url, params=request.args, stream=True, headers=req_headers, allow_redirects=False, data=request.form)
       
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in r.headers.items() if name.lower() not in excluded_headers]

        @stream_with_context
        def generate():
            for chunk in r.raw.stream(decode_content=False):
                yield chunk

        return Response(generate(), status=r.status_code, headers=headers)


@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_proxy.route('/thumbnail', methods=['GET'])
def image_proxy_thumbnail():
        id = request.args.get('id')
        type = request.args.get('type')
        try:
                thumbnail_path = get_thumbnail_path(type, id)
                return image_proxy(thumbnail_path)
        except Exception as e:
                return jsonify(Message=str(e)), 400

def get_thumbnail_path(type: str, id: str):
        with current_app.session_scope() as session:
                if type == 'page':
                        page = session.query(Page).filter(Page.id == id).one()
                        return page.thumbnail_url
                if type == 'article':
                        page = session.query(Page).join(Article, Page.articles).filter(Article.id == id).order_by(Page.volume_running_page_num.asc()).first()
                        return page.thumbnail_url
                if type == 'collection':
                        page = session.query(Page).filter(Page.collection_id == id).order_by(Page.volume_running_page_num.asc()).first()
                        return page.thumbnail_url
                else:
                        raise Exception("Wrong type")