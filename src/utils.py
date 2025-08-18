from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

RESPONSE_ERROR = 'Возникла ошибка при загрузке страницы {url}: {exc}'
TAG_NOT_FOUND = 'Не найден тег {tag} {message_attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as exc:
        raise ConnectionError(
            RESPONSE_ERROR.format(url=url, exc=exc)
        ) from exc


def find_tag(soup, tag, attrs=None):
    attrs_to_search = {} if attrs is None else attrs
    searched_tag = soup.find(tag, attrs=attrs_to_search)
    if searched_tag is None:
        message_attrs = None if not attrs_to_search else attrs_to_search
        raise ParserFindTagException(
            TAG_NOT_FOUND.format(tag=tag, message_attrs=message_attrs)
        )
    return searched_tag


def get_soup(session, url, parser="lxml"):
    response = get_response(session, url)
    return BeautifulSoup(response.text, parser)
