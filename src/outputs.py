import csv
import logging
from datetime import datetime

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, RESULTS_DIR

OUTPUT_SAVED = "Файл с результатами был сохранён: {file_path}"


def default_output(results, **kwargs):
    for row in results:
        print(*row)


def pretty_output(results, **kwargs):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = "l"
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args, **kwargs):
    results_dir = BASE_DIR / RESULTS_DIR
    results_dir.mkdir(exist_ok=True)
    datetime_formatted = datetime.now().strftime(DATETIME_FORMAT)
    file_path = results_dir / "{}_{}.csv".format(
        cli_args.mode,
        datetime_formatted
    )
    with open(file_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(OUTPUT_SAVED.format(file_path=file_path))


OUTPUT_HANDLERS = {
    "pretty": pretty_output,
    "file": file_output,
    None: default_output,
}


def control_output(results, cli_args):
    handler = OUTPUT_HANDLERS.get(cli_args.output)
    handler(results, cli_args=cli_args)
