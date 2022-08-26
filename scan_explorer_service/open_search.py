from typing import Dict, Iterator, List
import opensearchpy
from flask import current_app
from enum import Enum
from scan_explorer_service.utils.search_utils import SearchOptions


class EsFields(str, Enum):
    article_id = 'article_bibcodes'
    article_id_lowercase = 'article_bibcodes_lowercase'
    volume_id = 'volume_id'
    volume_id_lowercase = 'volume_id_lowercase'
    page_id = 'page_id'
    text = 'text'
    journal = 'journal'
    volume = 'volume'
    page_type = 'page_type'
    page_number = 'page_number'
    page_label = 'page_label'
    page_color = 'page_color'
    project = 'project'


query_translations = dict({
    SearchOptions.Bibstem.value: lambda val: keyword_search(EsFields.journal.value, val.ljust(5, '.')),
    SearchOptions.Bibcode.value: lambda val: keyword_search(EsFields.article_id_lowercase.value, val),
    SearchOptions.Volume.value: lambda val: keyword_search(EsFields.volume.value, val.rjust(4, '0')),
    SearchOptions.PageType.value: lambda val: keyword_search(EsFields.page_type.value, val),
    SearchOptions.PageCollection.value: lambda val: keyword_search(EsFields.page_number.value, val),
    SearchOptions.PageLabel.value: lambda val: text_search(EsFields.page_label.value, val),
    SearchOptions.PageColor.value: lambda val: keyword_search(EsFields.page_color.value, val),
    SearchOptions.Project.value: lambda val: keyword_search(EsFields.project.value, val),
    SearchOptions.FullText.value: lambda val: text_search(EsFields.text.value, val)
})

def keyword_search(field: str, key: str):
    if '*' in key:
        return {
            "wildcard":{
                field:{
                    "value": key
                }
            }           
        }
    else:
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

def create_query_string_query(query_string: str):
    query =  {
        "query": {
            "query_string": {
                "query": query_string,
                "default_field": "volume_id",
                "default_operator": "AND"
            }
        }
    }
    return query

def create_filter_query(qs_dict: dict):

    query_trans = {key: filter_func for key,
                   filter_func in query_translations.items() if key in qs_dict.keys()}
    if len(query_trans) ==  0:
        raise Exception("No valid keyword specified")

    filters = []
    for key, filter_func in query_trans.items(): filters.append(filter_func(qs_dict.get(key)))
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
    es = opensearchpy.OpenSearch(current_app.config.get('OPEN_SEARCH_URL'))
    resp = es.search(index=current_app.config.get(
        'OPEN_SEARCH_INDEX'), body=query)
    return resp

def text_search_highlight(text: str, filter_field: EsFields, filter_values: List[str]):
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = set_page_search_fields(base_query)
    query = append_highlight(query)
    for hit in es_search(query)['hits']['hits']:
        yield {
            "page_id": hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }

def set_page_ocr_fields(query: dict) -> dict:
    if 'fields' in query.keys():
        query["fields"].append("text")
    else:
        query["fields"] = ['text']
    return query

def set_page_search_fields(query: dict) -> dict:
    query["fields"] = ["id", "volume_id", "label", "page_number"]
    return query

def page_os_search(qs_dict: Dict, page, limit):
    query = create_filter_query(qs_dict)
    query = set_page_search_fields(query)
    from_number = (page - 1) * limit
    query['size'] = limit
    query['from'] = from_number
    query['sort'] = [{'volume_id':{'order': 'asc'}}, {'page_number':{'order':'asc'}} ]
    es_result = es_search(query)
    return es_result

def page_ocr_os_search(collection_id: str, page_number:int):
    qs = EsFields.volume_id_lowercase + ":" + collection_id + " " + EsFields.page_number + ":" + str(page_number)
    query = create_query_string_query(qs)
    query = set_page_ocr_fields(query)
    es_result = es_search(query)
    return es_result

def aggregate_search(qs_dict: Dict, aggregate_field, page, limit):
    query = create_filter_query(qs_dict)
    query = append_aggregate(query, aggregate_field, page, limit)
    es_result = es_search(query)
    return es_result