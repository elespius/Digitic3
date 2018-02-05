from constance import config
from django.conf import settings
from elasticsearch_dsl import DocType, Text, Integer, InnerObjectWrapper, \
    Nested, String, Date, char_filter
from elasticsearch_dsl import Keyword
from elasticsearch_dsl import MetaField
from elasticsearch_dsl import Search
from elasticsearch_dsl import analyzer
from elasticsearch_dsl import token_filter
from elasticsearch_dsl.connections import connections

__author__ = 'tkolter'

connections.create_connection()


OYE_RELEASES_INDEX = 'oye-{}releases'.format("" if settings.ENVIRONMENT is None else settings.ENVIRONMENT + "-")
OYE_ARTISTS_INDEX = 'oye-{}artists'.format("" if settings.ENVIRONMENT is None else settings.ENVIRONMENT + "-")
OYE_LABELS_INDEX = 'oye-{}labels'.format("" if settings.ENVIRONMENT is None else settings.ENVIRONMENT + "-")


MAIN_SEARCH_FIELDS = {
    'release': ['title', 'artist_name'],
    'artist': ['name'],
    'label': ['name']
}


def get_fuzziness(field, doc_type):
    return (
        config.SEARCH_FUZZINESS
        if field in MAIN_SEARCH_FIELDS.get(doc_type, [])
        else 0
    )


ngram_analyzer = analyzer(
    'autocomplete_analyzer',
    tokenizer='uax_url_email',
    filter=[
        'lowercase',
        token_filter('autocomplete_filter', type="edgeNGram", min_gram=1, max_gram=20)
    ]
)

oye_char_filter = char_filter(
    'oye_char_filter',
    type='mapping',
    mappings=[
        "$ => s"
    ]
)

lowercase_analyzer = analyzer(
    'lowercase_analyzer',
    char_filter=[
        oye_char_filter
    ],
    tokenizer='standard',
    filter=[
        'lowercase'
    ]
)


class Track(InnerObjectWrapper):
    pass


class Release(DocType):
    artist_name = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        fields={'raw': Keyword()})
    title = Text(search_analyzer=lowercase_analyzer, analyzer=lowercase_analyzer)
    released_at = Date()
    description = Text(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        include_in_all=False,
    )
    label = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        fields={'raw': Keyword()}
    )
    cat_no = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        fields={'raw': Keyword()}
    )

    tracks = Nested({
        'track_pk': Integer(index='not_analyzed'),
        'title': Text(),
        'url': Text(index='not_analyzed')
    })

    class Meta:
        all = MetaField(store=True, analyzer=lowercase_analyzer, search_analyzer=lowercase_analyzer)
        index = OYE_RELEASES_INDEX


class Artist(DocType):
    name = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer
    )

    class Meta:
        index = OYE_ARTISTS_INDEX


class Label(DocType):
    name = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
    )

    class Meta:
        index = OYE_LABELS_INDEX


QUERY_FIELDS = [
    'title.token',
    'artist_name',
    # 'description',
    'label',
    '_all',
]


def search(query, size=10, page=1, doc_type=None, fields=QUERY_FIELDS):
    should_queries = []

    search_params = {}
    if doc_type == 'artist':
        search_params['index'] = OYE_ARTISTS_INDEX
    elif doc_type == 'release':
        search_params['index'] = OYE_RELEASES_INDEX
    elif doc_type == 'label':
        search_params['index'] = OYE_LABELS_INDEX
        fields = ['name']

    match_prefix = config.SEARCH_PHRASE_PREFIX
    match_phrase = "match_phrase_prefix" if match_prefix else "match_phrase"
    for field in fields:

        should_queries.append({
            match_phrase: {
                field: {
                    "query": query,
                    "analyzer": "standard",
                    "boost": 5
                }
            }
        })

    should_queries.append({
        "match_phrase": {
            "cat_no": {
                "query": query,
                "analyzer": "standard",
                "boost": 100,
            }
        }
    })

    should_queries.extend(
        [
            {
                "match": {
                    field: {
                        "query": query,
                        "fuzziness": get_fuzziness(field, doc_type),
                        "operator": "and",
                        "prefix_length": config.SEARCH_PREFIX_LENGTH,
                        "max_expansions": 10,
                     }
                 }
            }
            for field in fields
        ]
    )

    sort_criterias = list()
    if doc_type == 'release':
        sort_criterias.append({"released_at": "desc"})

    sort_criterias.append({"_score": "desc"})

    query_dict = {
        "size": size,
        "from": size * (page - 1),
        "sort": sort_criterias,
        "query": {
            "bool": {
                "should": should_queries
            }
        }
    }

    s = Search(**search_params).from_dict(query_dict).index(search_params['index']).doc_type(doc_type)
    response = s.execute()
    return response
