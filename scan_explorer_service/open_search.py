from typing import Dict, Iterator, List
from opensearchpy import OpenSearch
from flask import current_app
from enum import Enum
from typing import Union


class EsFields(str, Enum):
    article_id = 'article_bibcodes'
    volume_id = 'volume_id'
    page_id = 'page_id'


query_translations = dict({
    'bibstem': lambda val: wildcard_search('volume_id_lowercase', val),
    'bibcode': lambda val: wildcard_search('article_bibcodes_lowercase', val),
    'journal': lambda val: keyword_search('journal', val),
    'pagetype': lambda val: keyword_search('page_type', val),
    'page_collection': lambda val: keyword_search('page_number', val),
    'page': lambda val: text_search('page_label', val),
    'full': lambda val: text_search('text', val)
})

def wildcard_search(field: str, key: str):
    if len(key) == 9:
        #Changes leading . in volume to 0 which is the convention in this app but not everywhere on ADS 
        key = key[0:5] + key[5:9].replace('.','0')
    return {
        "wildcard":{
            field:{
                "value": key + "*"
            }
        }
    }

def keyword_search(field: str, key: str):
    return {
        "term":{
            field:key
        }
    }

def text_search(field: str, text: str):
    return {
        "query_string": {
                "query": text,
                "default_field": field,
                "default_operator": "AND"
            }
        }

def create_base_query(text: str) -> dict:
    return {
        "query": {
            "bool": {
                "must": {
                    "query_string": {
                        "query": text,
                        "default_field": "text",
                        "default_operator": "AND"
                    }
                }
            }
        }
    }

def create_filter_query(qs_dict: dict):

    query_trans = {key: filter_func for key,
                   filter_func in query_translations.items() if key in qs_dict.keys()}
    if len(query_trans) ==  0:
        raise Exception("Empty")

    filters = []
    for key, filter_func in query_trans.items():
        filters.append(filter_func(qs_dict.get(key)))
    query =  {
        "query": {
            "bool": {
                "must": filters
            }
        }
    }
    return query
        

def create_base_query_filter(text: str, filter_field: EsFields, filter_values: List[str]) -> dict:
    query =  {
        "query": {
            "bool": {
                "must": {
                    "query_string": {
                        "query": text,
                        "default_field": "text",
                        "default_operator": "AND"
                    }
                },
            }
        }
    }
    if filter_field:
        query["query"]["bool"]["filter"] = {
                "terms": {
                    filter_field.value: filter_values
                }
            }
    return query

def append_aggregate(query: dict, agg_field: EsFields, page: int, size: int):
    from_number = (page - 1) * size
    query['size'] = 0
    sort_field = '_count'
    sort_order = 'desc'
    if agg_field == EsFields.article_id:
        sort_field = 'page_start'
        sort_order = 'asc'
    query['aggs'] = {   
        "total_count": {
            "cardinality": {
                "field": agg_field.value
            }
        },
        "ids": {
            "terms": {"field": agg_field.value,  "size": 10000},
            "aggs": {
                "bucket_sort": {
                    "bucket_sort": {
                        "sort": [{
                           sort_field: {
                                "order": sort_order
                            }
                        }],
                        "size": size,
                        "from": from_number
                    }
                }
            }
        }
    }
    if agg_field == EsFields.article_id:
        query['aggs']['ids']['aggs']['page_start'] = { "min": { "field": "page_number" } }
    return query


def append_highlight(query: dict):
    query['highlight'] = {
        "fields": {
            "text": {}
        },
        "type": "unified"
    }
    return query


def es_search(query: dict) -> Iterator[str]:
    es = OpenSearch(current_app.config.get('OPEN_SEARCH_URL'))
    resp = es.search(index=current_app.config.get(
        'OPEN_SEARCH_INDEX'), body=query)
    return resp

def text_search_highlight(text: str, filter_field: EsFields, filter_values: List[str]):
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = append_highlight(base_query)
    for hit in es_search(query)['hits']['hits']:
        yield {
            "page_id": hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }

def page_os_search(qs_dict: Dict, page, limit):
    query = create_filter_query(qs_dict)
    from_number = (page - 1) * limit
    query['size'] = limit
    query['from'] = from_number
    query['sort'] = [{'volume_id':{'order': 'asc'}}, {'page_number':{'order':'asc'}} ]
    es_result = es_search(query)
    return es_result

def aggregate_search(qs_dict: Dict, aggregate_field, page, limit):
    query = create_filter_query(qs_dict)
    query = append_aggregate(query, aggregate_field, page, limit)
    es_result = es_search(query)
    return es_result

def text_search_aggregate_ids(text: str, filter_field: EsFields, aggregate_field: EsFields, filter_values: List[str]) -> List[str]:
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = append_aggregate(base_query, aggregate_field)
    return es_search(query)


