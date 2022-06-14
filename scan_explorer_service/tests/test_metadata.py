from flask import url_for, jsonify
import unittest
from scan_explorer_service.models import Collection, Page, Article
from scan_explorer_service.tests.base import TestCaseDatabase
from scan_explorer_service.models import Base

class TestMetadata(TestCaseDatabase):

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

        self.article2 = Article(bibcode='1988ApJ...333..352S',
                               collection_id=self.collection.id)
        self.app.db.session.add(self.article2)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.article2)

        self.page = Page('page', self.collection.id)
        self.page.width = 1000
        self.page.height = 1000
        self.page.label = 'label'
        self.app.db.session.add(self.page)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.page)

        self.article.pages.append(self.page)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.article)

        self.article2.pages.append(self.page)
        self.app.db.session.commit()
        self.app.db.session.refresh(self.article2)
        
        # Serialize here since lazily loaded pages will disassociate with session
        self.article_serialized = self.article.serialized
        self.article2_serialized = self.article2.serialized

    def test_get_article(self):
        
        # Fetch article
        url = url_for("metadata.get_article", bibcode=self.article.bibcode)
        r = self.client.get(url)
        self.assertStatus(r, 200)
        self.assertEqual(r.data, jsonify(self.article_serialized).data)

        # Article not found
        url = url_for("metadata.get_article", bibcode='not_found')
        r = self.client.get(url)
        self.assertStatus(r, 200)
        self.assertEqual(r.data, b'')

        # No bibcode provided
        url = url_for("metadata.get_article")
        r = self.client.get(url)
        self.assertStatus(r, 400)

    def test_get_articles(self):
        
        # Fetch exactly one article
        url = url_for("metadata.get_articles", bibcode=self.article2.bibcode)
        r = self.client.get(url)
        self.assertStatus(r, 200)
        self.assertEqual(r.data, jsonify([self.article2_serialized]).data)

        #Fetch both articles
        url = url_for("metadata.get_articles", bibcode='1988ApJ...333')
        r = self.client.get(url)
        self.assertStatus(r, 200)
        self.assertEqual(r.data, jsonify([self.article_serialized, self.article2_serialized]).data)

        # Fetch ALL articles
        url = url_for("metadata.get_articles")
        r = self.client.get(url)
        self.assertStatus(r, 200)
        self.assertEqual(r.data, jsonify([self.article_serialized, self.article2_serialized]).data)



if __name__ == '__main__':
    unittest.main()
