from flask import url_for
from unittest.mock import patch
import unittest
from scan_explorer_service.models import Collection, Page, Article
from scan_explorer_service.tests.base import TestCaseDatabase
from scan_explorer_service.models import Base
import json

class TestManifest(TestCaseDatabase):

    def create_app(self):
        '''Start the wsgi application'''
        from scan_explorer_service.app import create_app
        return create_app(**{
            'SQLALCHEMY_DATABASE_URI': self.postgresql_url,
            'SQLALCHEMY_ECHO': False,
            'TESTING': True,
            'PROPAGATE_EXCEPTIONS': True,
            'TRAP_BAD_REQUEST_ERRORS': True,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False
        })

    def setUp(self):
        Base.metadata.drop_all(bind=self.app.db.engine)
        Base.metadata.create_all(bind=self.app.db.engine)

        self.collection = Collection(type = 'type', journal = 'journal', volume = 'volume')
        self.app.db.session.add(self.collection)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.collection)

        self.article = Article(bibcode='1988ApJ...333..341R',
                               collection_id=self.collection.id)
        self.app.db.session.add(self.article)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.article)

        self.page = Page(name='page', collection_id = self.collection.id)
        self.page.width = 1000
        self.page.height = 1000
        self.page.label = 'label'
        self.app.db.session.add(self.page)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.page)

        self.article.pages.append(self.page)
        self.app.db.session.commit()
            

    def test_get_manifest(self):
        url = url_for("manifest.get_manifest", id=self.article.id)
        r = self.client.get(url)
        data = json.loads(r.data)

        self.assertStatus(r, 200)
        self.assertEqual(data['@type'], 'sc:Manifest')

    def test_get_canvas(self):
        url = url_for("manifest.get_canvas", page_id=self.page.id)
        r = self.client.get(url)
        data = json.loads(r.data)
        self.assertStatus(r, 200)
        self.assertEqual(data['@type'], 'sc:Canvas')

    @patch('opensearchpy.OpenSearch')
    def test_search_article_with_highlight(self, OpenSearch):
        open_search_highlight_response = {"hits":{"total":{"value":1,"relation":"eq"},"max_score":None,"hits":[{'_source':{'page_id':self.page.id, 'volume_id':self.page.collection_id, 'page_label':self.page.label, 'page_number': self.page.volume_running_page_num}, "highlight":{'text':'some <b>highlighted</b> text'}}]}}
        article_id = self.article.id
        es = OpenSearch.return_value
        es.search.return_value = open_search_highlight_response

        url = url_for("manifest.search", id=article_id, q='text')
        r = self.client.get(url)
        data = json.loads(r.data)
        self.assertStatus(r, 200)
        self.assertEqual(data['@type'], 'sc:AnnotationList')
        call_args, call_kwargs = es.search.call_args
        expected_query = {'query': {'bool': {'must': {'query_string': {'query': 'text article_bibcodes:' + article_id, 'default_field': 'text', 'default_operator': 'AND'}}}}, '_source': {'include': ['page_id', 'volume_id', 'page_label', 'page_number']}, 'highlight': {'fields': {'text': {}}, 'type': 'unified'}}
        self.assertEqual(expected_query, call_kwargs.get('body'))


if __name__ == '__main__':
    unittest.main()
