from scan_explorer_service.models import Article, JournalVolume, Page
from flask_sqlalchemy import Pagination


class QueryBuilder():
    # Supported Journal queries
    journal_volume_query_def = dict(

    )

    article_query_def = dict({
        'bibcode': lambda val: Article.bibcode.ilike(f'{val}%'),
        'bibstem': lambda val: Article.bibcode.ilike(f'%{val}%')
    })

    page_query_def = dict(
        {'journalPage': lambda val: Page.volume_running_page_num == val}
    )

    def __init__(self, request):
        qs = request.args.get('q')
        qs_split = list(qs.split())
        self.queries = dict(kv.split(':') for kv in qs_split)

        # Intersection of cient queries and supported queries
        self.journal_volume_queries = {
            k: v for k, v in self.journal_volume_query_def.items() if k in self.queries}
        self.article_queries = {
            k: v for k, v in self.article_query_def.items() if k in self.queries}
        self.page_queries = {
            k: v for k, v in self.page_query_def.items() if k in self.queries}

        self.page = int(request.args.get('page', 1))
        self.limit = int(request.args.get('limit', 15))

        if self.page < 1 or self.limit < 1:
            raise Exception("Invalid page")

    def query(self, app):
        with app.session_scope() as session:

            article_query = session.query(Article)
            for query_key, filter_func in self.article_queries.items():
                article_query = article_query.filter(
                    filter_func(self.queries.get(query_key)))

            article_query = article_query.join(JournalVolume)
            for query_key, filter_func in self.journal_volume_queries.items():
                article_query = article_query.filter(
                    filter_func(self.queries.get(query_key)))

            if len(self.page_queries) > 0:
                article_query = article_query.join(Page)
                for query_key, filter_func in self.page_queries.items():
                    article_query = article_query.filter(
                        filter_func(self.queries.get(query_key)))

            pagination: Pagination = article_query.group_by(
                JournalVolume.id, Article.id).paginate(self.page, self.limit, False)

            collections = set()
            [collections.add(
                article.volume) or article for article in pagination.items if article.journal_volume_id not in collections]

            return {'page': pagination.page, 'pageCount': pagination.pages, 'total': pagination.total, 'articles': [
                a.serialized | {'journalPage': self.queries.get('journalPage', 1)} for a in pagination.items], 'collections': [v.serialized for v in collections]}
