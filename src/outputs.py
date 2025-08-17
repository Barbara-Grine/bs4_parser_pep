import csv
from datetime import datetime

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT


OUTPUT_SAVED_MSG = "Файл с результатами был сохранён: {file_path}"


def control_output(results, cli_args):
    output_handlers = {
        "pretty": pretty_output,
        "file": file_output,
    }
    handler = output_handlers.get(cli_args.output, default_output)
    handler(results, cli_args=cli_args)


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
    RESULTS_DIR = BASE_DIR / "results"
    RESULTS_DIR.mkdir(exist_ok=True)
    file_path = RESULTS_DIR / (
        f"{cli_args.mode}_{datetime.now().strftime(DATETIME_FORMAT)}.csv"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f, dialect=csv.unix_dialect)
        writer.writerows(results)
    print(OUTPUT_SAVED_MSG.format(file_path=file_path))
