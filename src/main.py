import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DOWNLOADS_DIR, EXPECTED_STATUS, MAIN_DOC_URL,
                       PEP_URL)
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, get_soup

ERROR_MESSAGE = (
    "\n Несовпадающие статусы: "
    "\n {pep_card_link} "
    "\n Статус в карточке: {pep_card_status} "
    "\n Ожидаемые статусы: {expected_status} \n "
)
DOWNLOAD_SAVED = "Архив был загружен и сохранён: {archive_path}"
VERSION_NOT_FOUND = "Список версий Python не найден"
VERSION_PATTERN = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
PARSER_START = "Парсер запущен!"
ARGS = "Аргументы командной строки: {args}"
PARSER_END = "Парсер завершил работу."
ERROR = "Ошибка при выполнении парсера: {error}"


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    soup = get_soup(session, whats_new_url)
    results = [("Ссылка на статью", "Заголовок", "Редактор, автор")]
    sections = soup.select(
        '#what-s-new-in-python div.toctree-wrapper > ul > li.toctree-l1 > a'
    )

    for link in tqdm(sections, desc="Обработка нововведений"):
        version_link = urljoin(whats_new_url, link['href'])
        soup_version = get_soup(session, version_link)
        dl_text = ""
        try:
            dl = find_tag(soup_version, 'dl')
            dl_text = dl.text.replace('\n', ' ')
        except ParserFindTagException:
            pass

        results.append(
            (version_link, find_tag(soup_version, 'h1').text, dl_text)
        )

    return results


def latest_versions(session):
    if (soup := get_soup(session, MAIN_DOC_URL)) is None:
        return []

    sidebar = find_tag(soup, "div", attrs={"class": "sphinxsidebarwrapper"})
    versions_ul = None

    for ul in sidebar.find_all("ul"):
        if "All versions" in ul.text:
            versions_ul = ul
            break

    if versions_ul is None:
        raise RuntimeError(VERSION_NOT_FOUND)

    results = [("Ссылка на документацию", "Версия", "Статус")]
    for a_tag in versions_ul.find_all("a"):
        link = a_tag["href"]
        if match := re.search(VERSION_PATTERN, a_tag.text):
            version, status = match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session):
    downloads_dir = BASE_DIR / DOWNLOADS_DIR
    downloads_dir.mkdir(exist_ok=True)
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    soup = get_soup(session, downloads_url)

    pdf_a4_link = soup.select_one(
        'div[role="main"] table.docutils a[href$="pdf-a4.zip"]'
    )["href"]
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split("/")[-1]
    archive_path = downloads_dir / filename

    response = session.get(archive_url)
    with open(archive_path, "wb") as f:
        f.write(response.content)

    logging.info(DOWNLOAD_SAVED.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_URL)
    section = find_tag(soup, "section", attrs={"id": "index-by-category"})
    if not (tables := section.find_all("table")):
        raise RuntimeError(
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
                PEP_URL, pep_card_tag["href"].rstrip("/") + "/"
            )

            try:
                pep_soup = get_soup(session, pep_card_url)
                pep_card_status = find_tag(pep_soup, "abbr").text.strip()

                if pep_card_status not in expected_status:
                    logs.append(ERROR_MESSAGE.format(
                        pep_card_link=pep_card_url,
                        pep_card_status=pep_card_status,
                        expected_status=expected_status
                    ))
                temp_results[pep_card_status] += 1

            except Exception as e:
                logging.warning(
                    f"Не удалось обработать {pep_card_url}: {str(e)}"
                )
                continue

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
    logging.info(PARSER_START)
    try:
        parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = parser.parse_args()
        logging.info(ARGS.format(args=args))

        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()

        results = MODE_TO_FUNCTION[args.mode](session)
        if results:
            control_output(results, args)

    except Exception as e:
        logging.exception(ERROR.format(error=e))

    logging.info(PARSER_END)


if __name__ == "__main__":
    main()
