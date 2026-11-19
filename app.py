import streamlit as st
from prototyping.parse_and_aggregate import process_file
import sqlite3
import os
import pandas as pd
from io import BytesIO

DB_PATH = 'motivation.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shipments (id INTEGER PRIMARY KEY, file TEXT, date TEXT, curator TEXT, type TEXT, value REAL)''')
    conn.commit()
    conn.close()


def save_record(rec):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO shipments (file,date,curator,type,value) VALUES (?,?,?,?,?)', (rec['file'], rec['date'], rec['curator'], rec['type'], rec['value_col7_itogo']))
    conn.commit()
    conn.close()


def get_shipments_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM shipments', conn)
    conn.close()
    return df


def generate_motivation_excel(df: pd.DataFrame) -> bytes:
    """Создаёт Excel файл в памяти с листами: raw_files, отгрузки_STI, отгрузки_TDK"""
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='raw_files', index=False)
        # try to ensure date month grouping
        df['month'] = df['date'].apply(lambda x: x[-7:] if isinstance(x, str) and len(x) >= 7 else 'unknown')
        agg = df.groupby(['month', 'curator', 'type']).agg(files_count=('file', 'count'), total_value=('value', 'sum')).reset_index()
        sti = agg[agg['type'] == 'STI']
        tdk = agg[agg['type'] == 'TDK']
        sti.to_excel(writer, sheet_name='статистика отгрузки СТИ', index=False)
        tdk.to_excel(writer, sheet_name='статистика отгрузки ТДК', index=False)
    out.seek(0)
    return out.read()


def main():
    st.title('Motivation uploader (prototype)')
    init_db()
    os.makedirs('uploads', exist_ok=True)

    st.subheader('Upload files')
    uploaded = st.file_uploader('Upload XLSX files', accept_multiple_files=True, type=['xlsx'])

    override_curator = st.text_input('Default curator override (leave empty to use value from filename)')

    if uploaded:
        for up in uploaded:
            save_path = os.path.join('uploads', up.name)
            with open(save_path, 'wb') as f:
                f.write(up.getbuffer())
            rec = process_file(save_path)
            if override_curator:
                rec['curator'] = override_curator
            st.write(rec)
            save_record(rec)

    st.markdown('---')
    st.subheader('Database & export')
    if st.button('Show DB'):
        df = get_shipments_df()
        st.dataframe(df)

    df = get_shipments_df()
    if not df.empty:
        if st.button('Generate мотивация.xlsx'):
            excel_bytes = generate_motivation_excel(df)
            st.download_button('Download мотивация.xlsx', data=excel_bytes, file_name='мотивация_output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


if __name__ == '__main__':
    main()
