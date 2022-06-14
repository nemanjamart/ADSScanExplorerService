from flask import url_for, jsonify
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
        Base.metadata.create_all(bind=self.app.db.engine)

        self.collection = Collection('type', 'journal', 'volume')
        self.app.db.session.add(self.collection)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.collection)

        self.article = Article(bibcode='1988ApJ...333..341R',
                               collection_id=self.collection.id)
        self.app.db.session.add(self.article)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.article)

        self.page = Page('page', self.collection.id)
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


if __name__ == '__main__':
    unittest.main()
