from requests import RequestException
from exceptions import ParserFindTagException


RESPONSE_ERROR_MSG = 'Возникла ошибка при загрузке страницы {url}: {exc}'
TAG_NOT_FOUND_MSG = 'Не найден тег {tag} с атрибутами {attrs}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as exc:
        raise RuntimeError(RESPONSE_ERROR_MSG.format(url=url, exc=exc))


def find_tag(soup, tag, attrs=None):
    attrs_to_search = {} if attrs is None else attrs
    searched_tag = soup.find(tag, attrs=attrs_to_search)
    if searched_tag is None:
        msg_attrs = None if not attrs_to_search else attrs_to_search
        raise ParserFindTagException(
            f"Не найден тег {tag} {msg_attrs}"
        )
    return searched_tag
