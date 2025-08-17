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


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, "whatsnew/")
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features="lxml")

    main_div = find_tag(soup, "section", attrs={"id": "what-s-new-in-python"})

    div_with_ul = find_tag(main_div, "div", attrs={"class": "toctree-wrapper"})

    sections_by_python = div_with_ul.find_all(
        "li",
        attrs={"class": "toctree-l1"}
    )

    results = [("Ссылка на статью", "Заголовок", "Редактор, автор")]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find("a")
        version_link = urljoin(whats_new_url, version_a_tag["href"])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, "lxml")
        h1 = find_tag(soup, "h1")
        dl = find_tag(soup, "dl")
        dl_text = dl.text.replace("\n", " ")
        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, "lxml")
    sidebar = find_tag(soup, "div", attrs={"class": "sphinxsidebarwrapper"})
    ul_tags = sidebar.find_all("ul")
    for ul in ul_tags:
        if "All versions" in ul.text:
            a_tags = ul.find_all("a")
            break
    else:
        raise Exception("Не найден список c версиями Python")

    results = [("Ссылка на документацию", "Версия", "Статус")]
    pattern = r"Python (?P<version>\d\.\d+) \((?P<status>.*)\)"
    for a_tag in a_tags:
        link = a_tag["href"]
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ""
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, "download.html")
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, "lxml")
    main_tag = find_tag(soup, "div", attrs={"role": "main"})
    table_tag = find_tag(main_tag, "table", attrs={"class": "docutils"})
    pdf_a4_tag = find_tag(
        table_tag,
        "a",
        attrs={"href": re.compile(r".+pdf-a4\.zip$")}
    )
    pdf_a4_link = pdf_a4_tag["href"]
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split("/")[-1]
    downloads_dir = BASE_DIR / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, "wb") as file:
        file.write(response.content)
    logging.info(f"Архив был загружен и сохранён: {archive_path}")


def pep(session):
    response = get_response(session, PEP_URL)
    soup = BeautifulSoup(response.text, "lxml")
    section = find_tag(soup, "section", attrs={"id": "index-by-category"})
    tables = section.find_all("table")
    if not tables:
        raise ParserFindTagException(
            "Таблицы внутри секции 'index-by-category' не найдены"
        )

    results = [("Статус", "Количество")]
    temp_results = defaultdict(int)
    logs = []

    for table in tables:
        tbody = find_tag(table, "tbody")
        pep_rows = tbody.find_all("tr")
        for pep_row in tqdm(pep_rows, desc="Обработка PEP"):
            list_status = find_tag(pep_row, "abbr")
            preview_status = list_status.text.strip()[1:]
            expected_status = EXPECTED_STATUS.get(preview_status, [])

            pep_card_link_tag = find_tag(pep_row, "a")
            pep_href = pep_card_link_tag["href"].rstrip("/") + "/"
            pep_card_url = urljoin(PEP_URL, pep_href)

            response = get_response(session, pep_card_url)
            pep_soup = BeautifulSoup(response.text, "lxml")
            card_abbr = find_tag(pep_soup, "abbr")
            pep_card_status = card_abbr.text.strip()

            if pep_card_status not in expected_status:
                logs.append(
                    ERROR_MESSAGE.format(
                        pep_card_link=pep_card_url,
                        pep_card_status=pep_card_status,
                        expected_status=expected_status
                    )
                )

            temp_results[pep_card_status] += 1

    list(map(logging.warning, logs))
    temp_results["Total"] = sum(temp_results.values())
    results += list(temp_results.items())
    return results


MODE_TO_FUNCTION = {
    "whats-new": whats_new,
    "latest-versions": latest_versions,
    "download": download,
    "pep": pep,
}


def main():
    configure_logging()
    logging.info("Парсер запущен!")
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f"Аргументы командной строки: {args}")
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info("Парсер завершил работу.")


if __name__ == "__main__":
    main()
