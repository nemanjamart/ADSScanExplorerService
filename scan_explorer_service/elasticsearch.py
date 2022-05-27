from typing import Iterator, List
from elasticsearch import Elasticsearch
from flask import current_app
from enum import Enum


class EsFields(str, Enum):
    article_id = 'article_ids'
    volume_id = 'volume_id'
    page_id = 'page_id'


def volume_full_text_search(id: str, text: str) -> Iterator[str]:
    id_query = {
        "terms": {
            "volume_id": id
        }
    }
    query = create_query(id_query, text)
    return es_search(query)


def article_full_text_search(id: str, text: str):
    id_query = {
        "terms": {
            "article_ids": id
        }
    }
    query = create_query(id_query, text)
    return es_search(query)


def create_query(id_query: dict, text: str) -> dict:
    query = {
        "query": {
            "bool": {
                "must": [
                    id_query,
                    {
                        "query_string": {
                            "query": text,
                            "default_field": "text",
                            "default_operator": "AND"
                        }
                    }
                ]
            }
        },
        "highlight": {
            "fields": {
                "text": {}
            },
            "type": "unified"
        }
    }
    return query


def es_text_search(query: dict) -> Iterator[str]:
    resp = es_search(query)
    for hit in resp['hits']['hits']:
        res = {
            "page_id": hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }
        yield res


def es_aggs_search(query: dict) -> Iterator[str]:
    resp = es_search(query)
    return resp


def es_search(query: dict) -> Iterator[str]:
    es = Elasticsearch(current_app.config.get('ELASTIC_SEARCH_URL'))
    resp = es.search(index=current_app.config.get(
        'ELASTIC_SEARCH_INDEX'), body=query)
    return resp


def text_search_aggregate_ids(text: str, filter_field: EsFields, filter_values: List[str]) -> List[str]:
    es_result = text_search_aggregate(text, filter_field, filter_values)
    es_buckets = es_result['aggregations']['ids']['buckets']
    key_list = [b.get('key') for b in es_buckets]
    return key_list


def text_search_aggregate(text: str, filter_field: EsFields, filter_values: List[str]) -> Iterator[str]:

    query = {
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
        },
        "aggs": {
            "total_count": {
                "cardinality": {
                    "field": filter_field
                }
            },
            "ids": {
                "terms": {"field": filter_field},
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
        "size": 0
    }

    return es_search(query)
