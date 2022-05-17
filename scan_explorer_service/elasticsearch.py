from typing import Iterator
from elasticsearch import Elasticsearch
from flask import current_app

def volume_full_text_search( id: str, text: str) -> Iterator[str]:
    id_query = {
         "match": {
             "volume_id" : id
         }
    }
    query = create_query(id_query, text)
    return es_search(query)

def article_full_text_search( id: str, text: str):
    id_query = {
        "nested": {
            "path": "articles",
            "query": {
                "match": {
                    "articles.id" : id
                } 
            }
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

def es_search(query: dict) -> Iterator[str]:
    
    es = Elasticsearch(current_app.config.get('ELASTIC_SEARCH_URL'))
    resp = es.search(index=current_app.config.get('ELASTIC_SEARCH_INDEX'), body=query)
    for hit in resp['hits']['hits']:
        res = {
            "page_id" : hit['_source']['page_id'],
            "highlight": hit['highlight']['text']
        }
        yield res
