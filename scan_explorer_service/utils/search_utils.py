import math
from scan_explorer_service.models import PageType, PageColor
import shlex
import enum
import re

class SearchOptions(enum.Enum):
    """Available Search Options"""
    Bibcode = 'bibcode'
    Bibstem = 'bibstem'
    FullText = 'full'
    PageCollection = 'page_sequence'
    PageLabel = 'page'
    PageType = 'pagetype'
    PageColor = 'pagecolor'
    Project = 'project'
    Volume = 'volume'

def parse_query_args(args):
    qs = re.sub(':\s*', ':', args.get('q', '', str))
    qs_arr = [q for q in shlex.split(qs) if ':' in q]
    qs_dict = {}
    for kv in qs_arr:
        kv_arr = kv.split(':', maxsplit=1)
        if len(kv_arr) == 2:
            qs_dict[kv_arr[0].lower()] = kv_arr[1].strip()
    check_query(qs_dict)

    page = args.get('page', 1, int)
    limit = args.get('limit', 10, int)

    return qs_dict, page, limit

def check_query(qs_dict: dict):
    """
        Checks that all queries have correct keys
    """
    for key in qs_dict.keys():
        # Will raise error if not in enum
        SearchOptions(key)
    check_page_type(qs_dict)
    check_page_color(qs_dict)
    check_project(qs_dict)

def check_page_type(qs_dict: dict): 
    if SearchOptions.PageType.value in qs_dict.keys():
        page_type = qs_dict[SearchOptions.PageType.value]
        valid_types = [p.name for p in PageType]
        if page_type in valid_types:
            return
        # Check lowercased and updated to cased
        for p in PageType:
            if page_type.lower() == p.name.lower():
                qs_dict[SearchOptions.PageType.value] = p.name
                return
        raise Exception("%s is not a valid page type, %s is possible choices"% (page_type, str(valid_types)))

def check_page_color(qs_dict: dict): 
    if SearchOptions.PageColor.value in qs_dict.keys():
        page_color = qs_dict[SearchOptions.PageColor.value]
        valid_types = [p.name for p in PageColor]
        if page_color in valid_types:
            return
        # Check lowercased and updated to cased
        for p in PageColor:
            if page_color.lower() == p.name.lower():
                qs_dict[SearchOptions.PageColor.value] = p.name
                return
        raise Exception("%s is not a valid page color, %s is possible choices"% (page_color, str(valid_types)))

def check_project(qs_dict: dict): 
    if SearchOptions.Project.value in qs_dict.keys():
        project = qs_dict[SearchOptions.Project.value]
        valid_types = ['PHaEDRA', 'Historical Literature', 'Microfilm Scanning']
        if project in valid_types:
            qs_dict[SearchOptions.Project.value] =  project.replace('Microfilm Scanning', 'Historical Literature')
            return
        # Check lowercased and updated to cased
        for p in valid_types:
            if project.lower() == p.lower():
                qs_dict[SearchOptions.Project.value] = p.replace('Microfilm Scanning', 'Historical Literature')
                return
        raise Exception("%s is not a valid project, %s is possible choices"% (project, str(valid_types)))

def serialize_os_agg_page_bucket(bucket: dict):
    id = bucket['_source']['page_id']
    volume_id = bucket['_source']['volume_id']
    label = bucket['_source']['page_label']
    journal = volume_id[0:5]
    volume = volume_id[5:9]
    page_number = bucket['_source']['page_number']
    return {'id': id, 'collection_id':volume_id, 'journal': journal, 'volume': volume, 'label':label, 'volume_page_num': page_number}

def serialize_os_page_result(result: dict, page: int, limit: int, contentQuery):
    total_count = result['hits']['total']['value']
    page_count = int(math.ceil(total_count / limit))    
    es_buckets = result['hits']['hits']

    return {'page': page, 'pageCount': page_count, 'limit': limit, 'total': total_count, 'query': contentQuery,
        'items': [serialize_os_agg_page_bucket(b) for b in es_buckets]}

def serialize_os_page_ocr_result(result: dict):
    es_buckets = result['hits']['hits']
    if len(es_buckets) < 1:
        raise Exception("No page with those parameters found")
    return es_buckets[0]['_source']['text']

def serialize_os_agg_collection_bucket(bucket: dict):
    id = bucket['key']
    journal = id[0:5]
    volume = id[5:9]
    return {'id': id, 'journal': journal, 'volume': volume, 'pages': bucket['doc_count']}

def serialize_os_collection_result(result: dict, page: int, limit: int, contentQuery):
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

