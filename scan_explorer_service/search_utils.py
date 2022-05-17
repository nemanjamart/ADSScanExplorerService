

from scan_explorer_service.models import Article, JournalVolume, Page
from flask_sqlalchemy import Pagination


def ilike_filter(col, value):
    return col.ilike(f'{value}%')


def exact_filter(col, value):
    return col == value


class QueryBuilder():
    # Supported Journal queries
    journal_volume_query_def = dict(
        {'bibstem': lambda val: ilike_filter(JournalVolume.journal, val)}
    )

    # Supported article queries
    article_query_def = dict(
        {'bibcode': lambda val: ilike_filter(Article.bibcode, val)}
    )

    page_query_def = dict(
        {'journalPage': lambda val: exact_filter(
            Page.volume_running_page_num, val)}
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

            serialized = {'page': pagination.page, 'pageCount': pagination.pages, 'total': pagination.total, 'items': [
                a.serialized | {'journalPage': self.queries.get('journalPage', 1)} for a in pagination.items]}
            return serialized
