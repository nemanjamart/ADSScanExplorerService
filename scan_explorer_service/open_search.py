from typing import Iterator, List
from opensearchpy import OpenSearch
from flask import current_app
from enum import Enum
from typing import Union


class EsFields(str, Enum):
    article_id = 'article_ids'
    volume_id = 'volume_id'
    page_id = 'page_id'


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

def append_aggregate(query: dict, agg_field: EsFields):
    query['size'] = 0
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
                            "_count": {
                                "order": "desc"
                            }
                        }],
                        "size": 10000
                    }
                }
            }
        }
    }

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

def text_search_aggregate_ids(text: str, filter_field: EsFields, aggregate_field: EsFields, filter_values: List[str]) -> List[str]:
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = append_aggregate(base_query, aggregate_field)
    es_result = es_search(query)
    es_buckets = es_result['aggregations']['ids']['buckets']
    return [b.get('key') for b in es_buckets], [b.get('doc_count') for b in es_buckets]

