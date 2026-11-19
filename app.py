import os
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st

from prototyping.parse_and_aggregate import process_file

DB_PATH = "motivation.db"

TYPE_LABELS = {"STI": "СТИ", "TDK": "ТДК"}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY,
            file TEXT,
            date TEXT,
            curator TEXT,
            type TEXT,
            value REAL
        )"""
    )
    conn.commit()
    conn.close()


def save_record(rec):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO shipments (file, date, curator, type, value) VALUES (?, ?, ?, ?, ?)",
        (
            rec["file"],
            rec["date"],
            rec["curator"],
            rec["type"],
            rec["value_col7_itogo"],
        ),
    )
    conn.commit()
    conn.close()


def get_shipments_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM shipments ORDER BY id", conn)
    conn.close()
    return df


def file_already_loaded(file_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM shipments WHERE file = ?", (file_name,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def to_month(date_str):
    """'08.10.2026' -> '10.2026'"""
    if isinstance(date_str, str) and len(date_str) >= 7 and date_str[2] == "." and date_str[5] == ".":
        return date_str[3:10]
    return "не определён"


def generate_motivation_excel(df: pd.DataFrame) -> bytes:
    """Собирает Excel: сырые данные + агрегаты по СТИ и ТДК."""
    out = BytesIO()
    data = df.copy()
    data["month"] = data["date"].apply(to_month)
    data["Тип"] = data["type"].map(TYPE_LABELS).fillna(data["type"])
    data = data.rename(
        columns={
            "file": "Файл",
            "date": "Дата",
            "curator": "Куратор",
            "value": "Итого (колонка 7)",
            "month": "Месяц",
        }
    )

    agg = (
        data.groupby(["Месяц", "Куратор", "Тип"], dropna=False)
        .agg(**{"Файлов": ("Файл", "count"), "Итого (колонка 7)": ("Итого (колонка 7)", "sum")})
        .reset_index()
    )

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        data[["Файл", "Дата", "Куратор", "Тип", "Итого (колонка 7)", "Месяц"]].to_excel(
            writer, sheet_name="Все загрузки", index=False
        )
        agg[agg["Тип"] == "СТИ"].to_excel(writer, sheet_name="Статистика СТИ", index=False)
        agg[agg["Тип"] == "ТДК"].to_excel(writer, sheet_name="Статистика ТДК", index=False)
        agg.to_excel(writer, sheet_name="Сводка", index=False)

    out.seek(0)
    return out.read()


def main():
    st.set_page_config(page_title="Мотивация — загрузка данных", page_icon="📊", layout="wide")
    init_db()
    os.makedirs("uploads", exist_ok=True)

    st.title("Мотивация — загрузка данных")
    st.caption("Загрузите отгрузочные документы. Данные попадут в статистику СТИ и ТДК.")

    tab_upload, tab_data, tab_export = st.tabs(["Загрузка", "Данные", "Выгрузка"])

    with tab_upload:
        uploaded = st.file_uploader(
            "Выберите файлы Excel (.xlsx)", accept_multiple_files=True, type=["xlsx"]
        )
        override_curator = st.text_input(
            "Куратор (необязательно)",
            help="Если заполнить — это имя заменит имя, определённое из названия файла.",
        )

        if uploaded:
            for up in uploaded:
                save_path = os.path.join("uploads", up.name)
                with open(save_path, "wb") as f:
                    f.write(up.getbuffer())

                if file_already_loaded(up.name):
                    st.warning(f"Файл «{up.name}» уже загружался ранее. Запись добавлена повторно.")

                try:
                    rec = process_file(save_path)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Не удалось обработать файл «{up.name}»: {e}")
                    continue

                if override_curator.strip():
                    rec["curator"] = override_curator.strip()

                save_record(rec)

                st.success(f"Файл «{rec['file']}» обработан и добавлен в статистику.")
                st.write(
                    {
                        "Файл": rec["file"],
                        "Дата": rec["date"],
                        "Куратор": rec["curator"],
                        "Тип": TYPE_LABELS.get(rec["type"], rec["type"]),
                        "Итого (колонка 7)": rec["value_col7_itogo"],
                    }
                )

    with tab_data:
        df = get_shipments_df()
        if df.empty:
            st.info("Пока нет загруженных файлов.")
        else:
            view = df.copy()
            view["type"] = view["type"].map(TYPE_LABELS).fillna(view["type"])
            view["month"] = view["date"].apply(to_month)
            view = view.rename(
                columns={
                    "id": "№",
                    "file": "Файл",
                    "date": "Дата",
                    "curator": "Куратор",
                    "type": "Тип",
                    "value": "Итого (колонка 7)",
                    "month": "Месяц",
                }
            )
            st.dataframe(view, use_container_width=True, hide_index=True)

            st.markdown("**Итоги по месяцам и кураторам**")
            summary = (
                view.groupby(["Месяц", "Куратор", "Тип"], dropna=False)
                .agg(**{"Файлов": ("Файл", "count"), "Итого (колонка 7)": ("Итого (колонка 7)", "sum")})
                .reset_index()
            )
            st.dataframe(summary, use_container_width=True, hide_index=True)

    with tab_export:
        df = get_shipments_df()
        if df.empty:
            st.info("Нет данных для выгрузки. Сначала загрузите файлы.")
        else:
            st.write(f"Записей в базе: **{len(df)}**")
            excel_bytes = generate_motivation_excel(df)
            st.download_button(
                "Скачать мотивация.xlsx",
                data=excel_bytes,
                file_name="мотивация_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )


if __name__ == "__main__":
    main()
