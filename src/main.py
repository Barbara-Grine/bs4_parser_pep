import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_URL
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_response


ERROR_MESSAGE = (
    '\n Несовпадающие статусы: '
    '\n {pep_card_link} '
    '\n Статус в карточке: {pep_card_status} '
    '\n Ожидаемые статусы: {expected_status} \n '
)
DOWNLOAD_SAVED_MSG = "Архив был загружен и сохранён: {archive_path}"


def get_soup(session, url):
    response = get_response(session, url)
    if response is None:
        logging.warning(f"Не удалось получить URL: {url}")
        return None
    return BeautifulSoup(response.text, "lxml")


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    soup = get_soup(session, whats_new_url)
    if soup is None:
        return []

    sections = soup.select(
        "#what-s-new-in-python div.toctree-wrapper li.toctree-l1"
    )
    results = [("Ссылка на статью", "Заголовок", "Редактор, автор")]

    for section in tqdm(sections, desc="Обработка whats-new"):
        version_link = urljoin(whats_new_url, section.find("a")["href"])
        soup_version = get_soup(session, version_link)
        if soup_version is None:
            continue
        try:
            dl_tag = find_tag(soup_version, "dl")
            dl_text = dl_tag.text.replace("\n", " ")
        except ParserFindTagException:
            dl_text = ""
        results.append(
            (version_link, find_tag(soup_version, "h1").text, dl_text)
        )

    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL)
    if soup is None:
        return []

    sidebar = find_tag(soup, "div", attrs={"class": "sphinxsidebarwrapper"})
    for ul in sidebar.find_all("ul"):
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
    else:
        raise ParserFindTagException("Список версий Python не найден")

    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    for a_tag in a_tags:
        link = a_tag["href"]
        match = re.search(pattern, a_tag.text)
        if match:
            version, status = match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session):
    DOWNLOADS_DIR = BASE_DIR / "downloads"
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    soup = get_soup(session, downloads_url)
    if soup is None:
        return []

    pdf_a4_link = soup.select_one(
        'div[role="main"] table.docutils a[href$="pdf-a4.zip"]'
    )['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split("/")[-1]
    archive_path = DOWNLOADS_DIR / filename

    response = session.get(archive_url)
    with open(archive_path, "wb") as f:
        f.write(response.content)

    logging.info(DOWNLOAD_SAVED_MSG.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_URL)
    if soup is None:
        return []

    section = find_tag(soup, "section", attrs={"id": "index-by-category"})
    tables = section.find_all("table")
    if not tables:
        raise ParserFindTagException(
            "Таблицы внутри секции 'index-by-category' не найдены"
        )

    temp_results = defaultdict(int)
    logs = []

    for table in tables:
        for pep_row in tqdm(table.select("tbody tr"), desc="Обработка PEP"):
            preview_status = find_tag(pep_row, "abbr").text.strip()[1:]
            expected_status = EXPECTED_STATUS.get(preview_status, [])

            pep_card_tag = find_tag(pep_row, "a")
            pep_card_url = urljoin(
                PEP_URL,
                pep_card_tag["href"].rstrip("/") + "/"
            )
            pep_soup = get_soup(session, pep_card_url)
            if pep_soup is None:
                continue

            pep_card_status = find_tag(pep_soup, "abbr").text.strip()
            if pep_card_status not in expected_status:
                logs.append(ERROR_MESSAGE.format(
                    pep_card_link=pep_card_url,
                    pep_card_status=pep_card_status,
                    expected_status=expected_status
                ))
            temp_results[pep_card_status] += 1

    list(map(logging.warning, logs))
    return [
        ("Статус", "Количество"),
        *temp_results.items(),
        ("Всего", sum(temp_results.values()))
    ]


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер запущен!")
    parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = parser.parse_args()
    logging.info(f"Аргументы командной строки: {args}")
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    try:
        results = MODE_TO_FUNCTION[args.mode](session)
        if results:
            control_output(results, args)
    except Exception as e:
        logging.exception(f"Ошибка при выполнении парсера: {e}")

    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()
