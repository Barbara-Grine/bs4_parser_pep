import csv
import logging
from datetime import datetime

from prettytable import PrettyTable

from constants import (BASE_DIR, DATETIME_FORMAT, OUTPUT_FILE, OUTPUT_PRETTY,
                       RESULTS_DIR)

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
    file_path = results_dir / "{}_{}.csv".format(
        cli_args.mode,
        datetime.now().strftime(DATETIME_FORMAT)
    )
    with open(file_path, "w", encoding="utf-8") as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(OUTPUT_SAVED.format(file_path=file_path))


OUTPUT_HANDLERS = {
    OUTPUT_PRETTY: pretty_output,
    OUTPUT_FILE: file_output,
    None: default_output,
}


def control_output(results, cli_args):
    OUTPUT_HANDLERS.get(cli_args.output)(results, cli_args=cli_args)
