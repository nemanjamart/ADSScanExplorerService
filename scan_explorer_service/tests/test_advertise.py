import unittest
from scan_explorer_service.app import create_app
from scan_explorer_service.tests.base import TestCaseDatabase


class TestAdvertise(TestCaseDatabase):
    '''Tests that each route is an http response'''

    def create_app(self):
        '''Start the wsgi application'''
        a = create_app(**{
            'SQLALCHEMY_DATABASE_URI': self.postgresql_url
        })
        return a

    def test_ResourcesRoute(self):
        '''Tests for the existence of a /resources route, and that it returns properly formatted JSON data'''
        r = self.client.get('/resources')
        self.assertEqual(r.status_code, 200)
        # Assert each key is a string-type
        [self.assertIsInstance(k, str) for k in r.json]

        for expected_field, _type in {'scopes': list,
                                      'methods': list,
                                      'description': str,
                                      'rate_limit': list}.items():
            # Assert each resource is described has the expected_field
            [self.assertIn(expected_field, v) for v in r.json.values()]
            # Assert every expected_field has the proper type
            [self.assertIsInstance(v[expected_field], _type)
             for v in r.json.values()]


if __name__ == '__main__':
    unittest.main()
