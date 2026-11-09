import json
import os
import os.path

from decorators import handle_db_errors

TABLES_IN_META = "tables"

# Чтение и запись json

@handle_db_errors
def load_json(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except OSError as exc:
        message = f"{filepath=}"
        raise OSError(exc.errno, message)
    except (UnicodeDecodeError, json.JSONDecodeError):
        message = f"{filepath=}"
        raise ValueError(message)
load_json.__wrapped__.exceptions = {
    OSError: "Ошибка чтения файла {filepath}",
    UnicodeDecodeError: "Ошибка чтения json из файла {filepath}",
    json.JSONDecodeError: "Ошибка чтения json из файла {filepath}",
}
    
@handle_db_errors
def dump_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f)
            return True
    except OSError as exc:
        message = f"{filepath=}"
        raise OSError(exc.errno, message)
    except (UnicodeDecodeError, json.JSONDecodeError):
        message = f"{filepath=}"
        raise ValueError(message)
dump_json.__wrapped__.exceptions = {
    OSError: "Ошибка записи файла {filepath}",
    FileNotFoundError: "Ошибка записи файла {filepath}",
    UnicodeDecodeError: "Ошибка записи json в файл {filepath}",
    json.JSONDecodeError: "Ошибка записи json в файл {filepath}",
}

load_metadata = load_json
save_metadata = dump_json
        
DATA_DIR = "data"
META_FILE_NAME = "db_meta.json"
META_PATH = os.path.join(DATA_DIR, META_FILE_NAME)

# Работа с метаинформацией
def init_meta():
    if not os.path.isfile(META_PATH):
        save_metadata(META_PATH, {TABLES_IN_META:{}})

def read_meta() -> dict:
    return load_metadata(META_PATH)

def write_meta(meta: dict):
    save_metadata(META_PATH, meta)
    
@handle_db_errors
def load_meta_for_table(table_name: str) -> dict:
    meta = read_meta()
    try:
        return meta[TABLES_IN_META][table_name]
    except KeyError:
        raise KeyError(f"{table_name=}")
load_meta_for_table.__wrapped__.exceptions = {
    KeyError: "Таблица {table_name} не найдена"
}
# Чтение и запись содержимого таблиц
def make_table_path(table_name: str) -> str:
    return os.path.join(DATA_DIR, f"{table_name}.json")

def load_table_data(table_name: str) -> list:
    path = make_table_path(table_name)
    return load_json(path)

def save_table_data(table_name: str, data: list):
    path = make_table_path(table_name)
    return dump_json(path, data)

def delete_table(table_name: str):
    path = make_table_path(table_name)
    os.remove(path)
