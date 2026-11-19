import re
import glob
import os
import openpyxl
import pandas as pd


def find_itogo_value(ws, target_col_idx=7):
    """
    Ищет строку содержащую "Итого" (case-insensitive) и возвращает значение в целевой колонке (1-based index).
    Если не найдено, суммирует все числовые значения в целевой колонке и возвращает сумму.
    """
    itogo_regex = re.compile(r"итог", re.IGNORECASE)
    for row in ws.iter_rows(values_only=True):
        # check if any cell in row contains 'итог'
        for cell in row:
            try:
                if isinstance(cell, str) and itogo_regex.search(cell):
                    # return cell in target column (convert to 0-based index)
                    val = row[target_col_idx - 1]
                    return val if val is not None else 0
            except Exception:
                continue

    # fallback: sum numeric values in target column
    s = 0
    found_any = False
    for row in ws.iter_rows(values_only=True):
        try:
            val = row[target_col_idx - 1]
        except Exception:
            val = None
        if isinstance(val, (int, float)):
            s += val
            found_any = True
        else:
            # try to parse numbers from strings
            if isinstance(val, str):
                cleaned = val.replace('\xa0', '').replace(' ', '').replace(',', '.')
                try:
                    num = float(cleaned)
                    s += num
                    found_any = True
                except Exception:
                    pass

    return s if found_any else None


def parse_filename(fname):
    """Extract date (dd.mm.yyyy) and curator (last word before extension) from filename"""
    base = os.path.basename(fname)
    name, _ = os.path.splitext(base)
    # date
    date_match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", name)
    date = date_match.group(1) if date_match else None
    # curator: last word (Cyrillic or latin) after last space
    parts = name.split()
    curator = parts[-1] if len(parts) > 0 else None
    return date, curator


def detect_type(fname):
    base = os.path.basename(fname).lower()
    if 'тдк' in base or 'tdk' in base:
        return 'TDK'
    else:
        return 'STI'


def process_file(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    value = find_itogo_value(ws, target_col_idx=7)
    date, curator = parse_filename(path)
    typ = detect_type(path)
    return {
        'file': os.path.basename(path),
        'path': path,
        'date': date,
        'curator': curator,
        'type': typ,
        'value_col7_itogo': value,
    }


def main():
    # try several plausible locations for the 'строки' folder
    candidates = [
        os.path.join(os.getcwd(), 'строки', '*.xlsx'),
        os.path.join(os.getcwd(), '..', 'строки', '*.xlsx'),
        os.path.join(os.getcwd(), 'строки', '*.xls'),
    ]
    files = []
    for c in candidates:
        files.extend(glob.glob(c))
    rows = []
    for f in files:
        try:
            r = process_file(f)
            rows.append(r)
            print('OK', r['file'], r['type'], r['curator'], r['value_col7_itogo'])
        except Exception as e:
            print('ERR', f, e)

    df = pd.DataFrame(rows)
    if df.empty:
        print('No files processed')
        return

    # aggregate by month and curator
    df['month'] = df['date'].apply(lambda x: x[-7:] if isinstance(x, str) and len(x) >= 7 else 'unknown')
    agg = df.groupby(['month', 'curator', 'type']).agg(
        files_count=('file', 'count'),
        total_value=('value_col7_itogo', 'sum')
    ).reset_index()

    # write to explicit example_output folder in workspace root
    out_dir = os.path.join(r'C:\Users\COMP\AppData\Local\Temp\opencode', 'example_output')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'motivation_example.xlsx')
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='raw_files', index=False)
        agg[agg['type'] == 'STI'].to_excel(writer, sheet_name='отгрузки_STI', index=False)
        agg[agg['type'] == 'TDK'].to_excel(writer, sheet_name='отгрузки_TDK', index=False)

    print('Wrote', out_path)


if __name__ == '__main__':
    main()
