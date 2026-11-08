import json
import os
import os.path

TABLES_IN_META = "tables"

# Чтение и запись json
def load_json(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except OSError as exc:
        message = f"level:file;operation:read;path:{filepath};error:{exc.strerror}"
        raise OSError(exc.errno, message)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"level:json;operation:load;error:{exc}"
        raise ValueError(message)
    
def dump_json(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f)
            return True
    except OSError as exc:
        message = f"level:file;operation:write;path:{filepath};error:{exc.strerror}"
        raise OSError(exc.errno, message)
    except (TypeError, ValueError) as exc:
        message = f"level:json;operation:dump;error:{exc}"
        raise ValueError(message)

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
    
def load_meta_for_table(table_name: str) -> dict:
    meta = read_meta()
    try:
        return meta[TABLES_IN_META][table_name]
    except KeyError:
        raise KeyError(f"level:sql;error:Таблица {table_name} не найдена")

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
