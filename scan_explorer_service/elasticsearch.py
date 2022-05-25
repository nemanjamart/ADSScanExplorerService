from typing import Iterator, List
from elasticsearch import Elasticsearch
from flask import current_app

def volume_full_text_search( id: str, text: str) -> Iterator[str]:
    id_query = {
        "terms":{
            "volume_id" : id
        }
    }
    query = create_query(id_query, text)
    return es_search(query)

def article_full_text_search( id: str, text: str):
    id_query = {
         "terms": {
             "article_ids" : id
         }
    }
    query = create_query(id_query, text)
    return es_search(query)

def create_query(id_query: dict, text: str) -> dict:
    query = {
        "query":{
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
            "page_id" : hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }
        yield res

def es_aggs_search(query: dict) -> Iterator[str]:
    resp = es_search(query)
    return resp

def es_search(query: dict) -> Iterator[str]:
    es = Elasticsearch(current_app.config.get('ELASTIC_SEARCH_URL'))
    resp = es.search(index=current_app.config.get('ELASTIC_SEARCH_INDEX'), body=query)
    return resp

def create_aggs_query(queries: List[dict], field: str, page: int, size: int) -> dict:
    start = (page - 1)  * size
    query = {
        "query":{
            "bool": {
                "must": queries
            }
        },
        "aggs": {
            "total_count": {
                "cardinality": { 
                  "field": field
                }
            },
            "ids": {
                "terms": { "field": field },
                "aggs": {
                    "bucket_sort": {
                        "bucket_sort": {                                 
                            "sort": [{
                                "_count": {
                                    "order": "desc"
                                }
                            }],
                            "from": start,
                            "size": size
                        }
                    }
                }
            }
        },
        "size":0
    }
    return query

def text_search_aggregate(text: str, volume_ids: List[str], article_ids: List[str],  is_article_query: bool, page: int, size: int) -> Iterator[str]:
    text_query = {
        "query_string": {
            "query": text,
            "default_field": "text",
            "default_operator": "AND"
        }
    }
    queries = [text_query]

    if volume_ids and len(volume_ids) > 0:
        volume_query = {
            "terms":{
                "volume_id" : volume_ids
            }
        }
        queries.append(volume_query)

    if article_ids and len(article_ids) > 0:
        article_query = {
            "terms": {
                "article_ids" : article_ids
            }
        }
        queries.append(article_query)
    field = "volume_id"
    if is_article_query:
        field = "article_ids"

    query = create_aggs_query(queries, field, page, size)
    return es_search(query)
