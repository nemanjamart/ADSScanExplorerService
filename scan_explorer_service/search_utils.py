import os
import math
import requests
from scan_explorer_service.models import Article, Collection, Page, PageType
from flask_sqlalchemy import Pagination
from flask import current_app
import shlex



collection_query_translations = dict({
    'bibstem': lambda val: Collection.journal.ilike(f'{val}%'),
    'journal': lambda val: Collection.journal.ilike(f'{val}%'),
    'volume': lambda val: Collection.volume.ilike(f'%{val}%'),
})

article_query_translations = dict({
    'bibcode': (lambda val: Article.bibcode.ilike(f'{val}%')),
})

page_query_translations = dict({
    'page': lambda val: Page.label == val,
    'page_collection': lambda val: Page.volume_running_page_num == val,
    'pagetype': lambda val: Page.page_type == PageType.from_string(val)
})


def parse_query_args(args):
    qs = args.get('q', '', str)
    qs_arr = [q for q in shlex.split(qs) if ':' in q]
    qs_dict = dict(kv.split(':') for kv in qs_arr)

    page = args.get('page', 1, int)
    limit = args.get('limit', 10, int)

    return qs_dict, page, limit


def serialize_result(db_session, result: Pagination, contentQuery = ''):
    return {'page': result.page, 'pageCount': result.pages, 'limit': result.per_page, 'total': result.total, 'query': contentQuery, 
    'items': [{**item.serialized, **fetch_ads_metadata(db_session, item.id)} for item in result.items]}

def serialize_os_agg_page_bucket(bucket: dict):
    id = bucket['_source']['page_id']
    volume_id = bucket['_source']['volume_id']
    label = bucket['_source']['page_label']
    journal = volume_id[0:5]
    volume = volume_id[5:9]
    page_number = bucket['_source']['page_number']
    return {'id': id, 'collection_id':volume_id, 'journal': journal, 'volume': volume, 'label':label, 'volume_page_num': page_number}

def serialize_os_page_result(result: dict, page: int, limit: int, contentQuery = ''):
    total_count = result['hits']['total']['value']
    page_count = int(math.ceil(total_count / limit))    
    es_buckets = result['hits']['hits']

    return {'page': page, 'pageCount': page_count, 'limit': limit, 'total': total_count, 'query': contentQuery,
        'items': [serialize_os_agg_page_bucket(b) for b in es_buckets]}

def serialize_os_agg_collection_bucket(bucket: dict):
    id = bucket['key']
    journal = id[0:5]
    volume = id[5:9]
    return {'id': id, 'journal': journal, 'volume': volume, 'pages': bucket['doc_count']}


def serialize_os_collection_result(result: dict, page: int, limit: int, contentQuery = ''):
    total_count = result['aggregations']['total_count']['value']
    page_count = int(math.ceil(total_count / limit))    
    es_buckets = result['aggregations']['ids']['buckets']

    return {'page': page, 'pageCount': page_count, 'limit': limit, 'total': total_count, 'query': contentQuery,
        'items': [serialize_os_agg_collection_bucket(b) for b in es_buckets]}

def serialize_os_agg_article_bucket(bucket: dict):
    id = bucket['key']
    return {'id': id, 'bibcode': id, 'pages': bucket['doc_count']}

def serialize_os_article_result(result: dict, page: int, limit: int, contentQuery = ''):
    total_count = result['aggregations']['total_count']['value']
    page_count = int(math.ceil(total_count / limit))    
    es_buckets = result['aggregations']['ids']['buckets']

    return {'page': page, 'pageCount': page_count, 'limit': limit, 'total': total_count, 'query': contentQuery,
        'items': [serialize_os_agg_article_bucket(b) for b in es_buckets]}

def fetch_ads_metadata(session, uuid: str):
    auth_token = os.getenv('ADS_API_AUTH_TOKEN')
    if auth_token:
        article = session.query(Article).filter_by(id=uuid).one_or_none()
        if article:
            params = {'q': f'bibcode:{article.bibcode}', 'fl':'title,author'}
            headers = {'Authorization': f'Bearer {auth_token}'}
            response = requests.get(current_app.config.get('ADS_API_URL'), params, headers=headers).json()
            docs = response.get('response').get('docs')

            if docs:
                return docs[0]
            
    return {}