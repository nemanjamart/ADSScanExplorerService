import re
from flask import Blueprint, Response, current_app, request, stream_with_context
from flask_discoverer import advertise
from urllib import parse as urlparse
import requests

bp_proxy = Blueprint('proxy', __name__, url_prefix='/image/iiif/2')

@advertise(scopes=['api'], rate_limit=[300, 3600*24])
@bp_proxy.route('/<path:path>', methods=['GET'])
def image_proxy(path):
        req_url = urlparse.urljoin(f'{current_app.config.get("IMAGE_API_BASE_URL")}/', path)
        req_headers={key: value for (key, value) in request.headers if key != 'Host' and key != 'Accept'}

        if 'localhost' in request.root_url:
                addr = re.sub('http[s]?://', '', request.root_url).split(':')
                req_headers['X-Forwarded-Host'] = addr[0].strip('/')
                req_headers['X-Forwarded-Port'] = addr[1].strip('/')
        else:
                req_headers['X-Forwarded-Host'] = request.root_url

        req_headers['X-Forwarded-Path'] = '/image'
  
        r = requests.request(request.method, req_url, params=request.args, stream=True, headers=req_headers, allow_redirects=False, data=request.form)
       
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in r.headers.items() if name.lower() not in excluded_headers]

        @stream_with_context
        def generate():
            for chunk in r.raw.stream(decode_content=False):
                yield chunk

        return Response(generate(), status=r.status_code, headers=headers)


