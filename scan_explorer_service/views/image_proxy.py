from flask import Blueprint, Response, current_app, request, stream_with_context, jsonify
from flask_discoverer import advertise
from urllib import parse as urlparse
from PIL import Image
from io import BytesIO

import requests
from scan_explorer_service.models import Page, Article
from scan_explorer_service.utils.db_utils import item_thumbnail
from scan_explorer_service.utils.utils import url_for_proxy


bp_proxy = Blueprint('proxy', __name__, url_prefix='/image')


@advertise(scopes=['api'], rate_limit=[5000, 3600*24])
@bp_proxy.route('/iiif/2/<path:path>', methods=['GET'])
def image_proxy(path):
    """Proxy in between the image server and the user"""
    req_url = urlparse.urljoin(f'{current_app.config.get("IMAGE_API_BASE_URL")}/', path)
    req_headers = {key: value for (key, value) in request.headers if key != 'Host' and key != 'Accept'}

    req_headers['X-Forwarded-Host'] = current_app.config.get('PROXY_SERVER')
    req_headers['X-Forwarded-Path'] = current_app.config.get('PROXY_PREFIX').rstrip('/') + '/image'

    r = requests.request(request.method, req_url, params=request.args, stream=True,
                         headers=req_headers, allow_redirects=False, data=request.form)

    excluded_headers = ['content-encoding','content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in r.headers.items() if name.lower() not in excluded_headers]

    @stream_with_context
    def generate():
        for chunk in r.raw.stream(decode_content=False):
            yield chunk

    return Response(generate(), status=r.status_code, headers=headers)


@advertise(scopes=['api'], rate_limit=[5000, 3600*24])
@bp_proxy.route('/thumbnail', methods=['GET'])
def image_proxy_thumbnail():
    """Helper to generate the correct url for a thumbnail given an ID and type"""
    try:
        id = request.args.get('id')
        type = request.args.get('type')
        with current_app.session_scope() as session:
            thumbnail_path = item_thumbnail(session, id, type)
            path = urlparse.urlparse(thumbnail_path).path
            remove = urlparse.urlparse(url_for_proxy('proxy.image_proxy', path='')).path
            path = path.replace(remove, '')
            return image_proxy(path)
    except Exception as e:
        return jsonify(Message=str(e)), 400

@advertise(scopes=['api'], rate_limit=[5000, 3600*24])
@bp_proxy.route('/pdf', methods=['GET'])
def pdf_save():
    """Proxy in between the image server and the user"""
    try:
        collection_id = request.args.get('collection_id')
        article_id = request.args.get('article_id')
        page_start = request.args.get('page_start')
        page_end = request.args.get('page_end')
        dpi = request.args.get('dpi')
        
        @stream_with_context
        def loop_image_io(collection, page_start, page_end):

            img_io = BytesIO()
            append = False
            start_byte = 0
            with current_app.session_scope() as session:
                if article_id:
                    query = session.query(Page).filter(Page.articles.any(Article.id == article_id)).order_by(Page.volume_running_page_num)
                elif collection_id:
                    query = session.query(Page).filter(Page.collection_id == collection_id, Page.volume_running_page_num >= page_start, Page.volume_running_page_num <= page_end).order_by(Page.volume_running_page_num)
                for page in query.all():
                    image_url = page.image_url + "/full/" + str(int(page.height/3.0)) + ",/0/default.png"
                    image = Image.open(requests.get(image_url, stream=True).raw)
                    im = image.convert('RGB')
                    start_byte = img_io.tell()
                    im.save(img_io, save_all=True, format='pdf', append=append)
                    append = True
                    img_io.seek(start_byte)
                    yield img_io.read()
        return Response(loop_image_io(collection_id, page_start, page_end), mimetype='application/pdf')
    except Exception as e:
        return jsonify(Message=str(e)), 400
