[README.md](https://github.com/user-attachments/files/35089281/README.md)
# Motivation Streamlit App (Prototype)

Прототип Streamlit‑приложения для автоматизации расчёта мотиваций на основе загружаемых отгрузочных документов.

Содержит ETL-скрипт для парсинга ваших текущих файлов и генерации примера файла мотивации.

Запуск локально:

1. Установите зависимости:
   pip install -r requirements.txt

2. Запустите прототип парсера (считывает файлы из папки "строки"):
   python prototyping/parse_and_aggregate.py

3. Запуск Streamlit (скелет приложения будет добавлен в следующих шагах):
   streamlit run app.py
