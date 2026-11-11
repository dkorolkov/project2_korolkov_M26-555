import json
import os
import os.path

from decorators import handle_db_errors

TABLES_IN_META = "tables"

# Чтение и запись json

@handle_db_errors
def load_json(filepath):
    with open(filepath) as f:
        return json.load(f)
    
@handle_db_errors
def dump_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f)

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
    return meta[TABLES_IN_META][table_name]

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
