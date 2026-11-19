Локальный запуск прототипа (подробно)

1) Установка Git (опционально)
- Скачайте и установите Git: https://git-scm.com/download/win

2) Установка Python и виртуального окружения
- Убедитесь, что установлен Python 3.10+ (https://www.python.org/downloads/)
- Откройте PowerShell и выполните:
  python -m venv .venv
  .\.venv\Scripts\Activate
  pip install --upgrade pip
  pip install -r requirements.txt

3) Запуск парсера для ваших текущих файлов
- В этом проекте парсер ищет папку "строки" рядом с репозиторием. Если у вас она в другом месте — измените путь в prototyping/parse_and_aggregate.py
- Выполните:
  python prototyping/parse_and_aggregate.py
  # скрипт напечатает обработанные файлы и создаст примерный Excel в C:\Users\<user>\AppData\Local\Temp\opencode\example_output\motivation_example.xlsx

4) Запуск Streamlit UI
- Выполните:
  streamlit run app.py
- Откройте браузер: http://localhost:8501
- На странице: загрузите xlsx‑файлы, при необходимости укажите override curator и нажмите Generate мотивация.xlsx — затем скачайте файл.

5) Где искать результаты
- Локальная БД: motivation.db (файл исключён из репо .gitignore)
- Загруженные файлы: uploads/ (также в .gitignore)
- Пример выхода: файл мотивация_example.xlsx (временный путь, указан в выводе парсера)
