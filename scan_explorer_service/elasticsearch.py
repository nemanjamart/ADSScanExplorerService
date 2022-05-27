from typing import Iterator, List
from elasticsearch import Elasticsearch
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
    return {
        "query": {
            "bool": {
                "must": {
                    "query_string": {
                        "query": text,
                        "default_field": "text",
                        "default_operator": "AND"
                    }
                },
                "filter": {
                    "terms": {
                        filter_field: filter_values
                    }
                }
            }
        }
    }


def append_aggregate(query: dict, agg_field):
    query['aggs'] = {
        "total_count": {
            "cardinality": {
                "field": agg_field
            }
        },
        "ids": {
            "terms": {"field": agg_field},
            "aggs": {
                "bucket_sort": {
                    "bucket_sort": {
                        "sort": [{
                            "_count": {
                                "order": "desc"
                            }
                        }]
                    }
                }
            }
        }
    },

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
    es = Elasticsearch(current_app.config.get('ELASTIC_SEARCH_URL'))
    resp = es.search(index=current_app.config.get(
        'ELASTIC_SEARCH_INDEX'), body=query)
    return resp

def highlight_text_search(text: str, filter_field: EsFields, filter_values: List[str]):
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = append_highlight(base_query)
    for hit in es_search(query)['hits']['hits']:
        yield {
            "page_id": hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }

def text_search_aggregate_ids(text: str, filter_field: EsFields, filter_values: List[str]) -> List[str]:
    base_query = create_base_query_filter(text, filter_field, filter_values)
    query = append_aggregate(base_query, filter_field)
    es_result = es_search(query)
    es_buckets = es_result['aggregations']['ids']['buckets']
    return [b.get('key') for b in es_buckets]

