# Парсер PEP и документации Python

## Описание
Парсер собирает информацию о версиях Pyton и PEP документацию с официальных сайтов:
[peps.python.org](https://peps.python.org/)
[docs.python.org](https://docs.python.org/3/)

Парсер поддерживает несколько режимов работы через аргументы командной строки, логирует ошибки и работу в консоль, а также может сохранять результаты в файл или отображать их в виде таблицы.

## Технологии
- Python 3.9+
- BeautifulSoup4
- Prettytable
- Logging

## Запуск проекта
1. Клонируйте репозиторий на свой компьютер:

    ```bash
    git clone git@github.com:Barbara-Grine/foodgram.git
    ```
2. Создайте и активируйте виртуальное окружение:

    ```bash
    python -m venv venv
    source venv/Scripts/activate
    ```
3. Обновите pip и установите зависимости:

    ```bash
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Аргументы и режимы работы
Запускать парсер необходимо из директории "src"

### Аргументы
1. Справка о режимах парсера:

    ```bash
    python main.py -h
    ```
2. Очистка кэша:

    ```bash
    python main.py <mode> -c
    python main.py <mode> --clear-cache
    ```

3. Сохранение результатов в CSV:

    ```bash
    python main.py <mode> --output file
    ```

4. Отображение таблицы в консоли:

    ```bash
    python main.py <mode> --output pretty
    ```

### Режимы парсера
1. whats-new — нововведения Python:

    ```bash
    python main.py whats-new
    ```

2. latest-versions — последние версии Python

    ```bash
    python main.py latest-versions
    ```

3. download — загрузка архива документации:

    ```bash
    python main.py download
    ```

4. pep — парсинг статусов PEP:

    ```bash
    python main.py pep
    ```

## Автор
Ваулина Варвара Максимовна

[Telegram](https://t.me/evanidis_re)