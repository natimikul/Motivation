# Motivation Streamlit App (Prototype)

Прототип Streamlit‑приложения для автоматизации расчёта мотиваций на основе загружаемых отгрузочных документов.

Содержит ETL-скрипт для парсинга ваших текущих файлов и генерации примера файла мотивации.


Локальный запуск — кратко:

1. Создайте виртуальное окружение и установите зависимости:
   python -m venv .venv
   .\.venv\Scripts\Activate
   pip install --upgrade pip
   pip install -r requirements.txt

2. Запустите парсер (чтение папки "строки"):
   python prototyping/parse_and_aggregate.py

3. Запустите Streamlit UI:
   streamlit run app.py

Подробная инструкция: docs/LOCAL_RUN.md
