from operator import eq, ge, gt, le, lt, ne

from prettytable import PrettyTable

from decorators import confirm_action, handle_db_errors, log_time

from .utils import (
    TABLES_IN_META,
    delete_table,
    load_meta_for_table,
    load_table_data,
    read_meta,
    save_table_data,
    write_meta,
)


def _read_meta(command):
    try:
        return read_meta()
    except OSError as exc:
        message = "Не удалось получить метаданные"
        raise OSError(exc.errno, message)
    except (TypeError, ValueError):
        message = "Не удалось получить метаданные"
        raise ValueError(message)

def _write_meta(command, meta):
    try:
        write_meta(meta)
    except OSError as exc:
        message = "Не удалось получить метаданные"
        raise OSError(exc.errno, message)
    except (TypeError, ValueError):
        message = "Не удалось получить метаданные"
        raise ValueError(message)

COLUMN_TYPES = {
    'int': int,
    'str': str,
    'bool': bool,
}
ID_COLUNM_NAME = 'id'
ID_COLUNM_TYPE = 'int'

TABLE_NAME_IN_META = "name"
COLUMNS_IN_META = "columns"

# Управление таблицами

@handle_db_errors
def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    # Проверить наличие столбца id
    id_idx = None
    for idx, (col_name, col_type) in enumerate(columns):
        if col_name == ID_COLUNM_NAME:
            id_idx = idx
            break
        else:
            if col_type not in COLUMN_TYPES:
                raise TypeError(f"{col_type=};{col_name=}")

    # Удалить столбец id, если есть
    if id_idx is not None:
        del columns[id_idx]

    # Добавить столбец id в начало списка
    columns.insert(0, (ID_COLUNM_NAME, ID_COLUNM_TYPE))
    
    if table_name in metadata[TABLES_IN_META]:
        raise KeyError(f"{table_name=}")
    table = {
        TABLE_NAME_IN_META: table_name,
        COLUMNS_IN_META: columns,
    }

    metadata[TABLES_IN_META][table_name] = table
    
    return metadata

create_table.__wrapped__.exceptions = {
    TypeError: "Недопустимый тип {col_type} в столбце {col_name}",
    KeyError: "Таблица {table_name} уже существует"
}

@confirm_action("Удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name in metadata[TABLES_IN_META]:
        del metadata[TABLES_IN_META][table_name]
    else:
        raise KeyError(f"Таблица {table_name} не найдена")

    return metadata
    
# Работа с данными

@log_time
def insert(table_data: list, table_name: str, values: list):
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META][1:]
    if len(values) != len(columns):
        raise ValueError("Количество входных данных не соответствует " +\
        "количеству столбцов в таблице")
    
    #col_dict = dict(columns)
    for (col_name, col_type), value in zip(columns, values):
        if not isinstance(value, COLUMN_TYPES[col_type]):
            raise TypeError(f"Элемент данных {value}" +\
            f" не соответствует типу столбца {col_name}, ожидается {col_type}")
            
    new_id = max((row[ID_COLUNM_NAME] for row in table_data), default=0) + 1
    col_names = next(zip(*columns))
    new_row = dict(zip(col_names, values))
    new_row[ID_COLUNM_NAME] = new_id
    table_data.append(new_row)
    
    return table_data

def predicat(val1, cmp_op, val2):
    ops = {
        '<': lt,
        '<=': le,
        '>': gt,
        '>=': ge,
        '=': eq,
        "!=": ne,
        "<>": ne,
    }
    
    if not cmp_op in ops:
        raise ValueError(f"Недопустимая операция сравнения: {cmp_op}")
    
    return ops[cmp_op](val1, val2)
    
@log_time
def select(table_data: list, table_name: str, where_clause=None) -> list:
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META]
    if where_clause is None:
        return table_data
        
    col_name, cmp_op, value = where_clause
    col_dict = dict(columns)
    col_type = col_dict[col_name]
    if not isinstance(value, COLUMN_TYPES[col_type]):
        raise TypeError(f"Элемент данных {value}" +\
        f" не соответствует типу столбца {col_name}, ожидается {col_type}")

    filtered_data = []
    for row in table_data:
        try:
            if predicat(row[col_name], cmp_op, value):
                filtered_data.append(row)
        except KeyError:
            raise KeyError(
            f"Столбца {col_name} нет в таблице {table_name}")
        
    return filtered_data
    
@confirm_action("Удаление строк")
def delete(table_data: list, table_name: str, where_clause: tuple) -> list:
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META]
    if where_clause is None:
        return table_data
        
    col_name, cmp_op, value = where_clause
    col_dict = dict(columns)
    col_type = col_dict[col_name]
    if not isinstance(value, COLUMN_TYPES[col_type]):
        raise TypeError(f"Элемент данных {value}" +\
        f" не соответствует типу столбца {col_name}, ожидается {col_type}")

    filtered_data = []
    for row in table_data:
        try:
            if not predicat(row[col_name], cmp_op, value):
                filtered_data.append(row)
        except KeyError:
            raise KeyError(
            f"Столбца {col_name} нет в таблице {table_name}")
        
    return filtered_data
    
@log_time
def update(table_data: list, table_name: str, set_clause: tuple, where_clause: tuple) -> list:
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META]
 
    set_col_name, set_value = set_clause
    where_col_name, where_cmp_op, where_value = where_clause
 
    col_dict = dict(columns)
    set_col_type = col_dict[set_col_name]
    if not isinstance(set_value, COLUMN_TYPES[set_col_type]):
        raise TypeError(f"Элемент данных {set_value}" +\
        f" не соответствует типу столбца {set_col_name}," +\
        f" ожидается {set_col_type}")
    where_col_type = col_dict[where_col_name]
    if not isinstance(where_value, COLUMN_TYPES[where_col_type]):
        raise TypeError(f"Элемент данных {where_value}" +\
        f" не соответствует типу столбца {where_col_name}," +\
        f" ожидается {where_col_type}")
  
    updated_data = []
    for row in table_data:
        try:
            if predicat(row[where_col_name], where_cmp_op, where_value):
                row[set_col_name] = set_value
            updated_data.append(row)
        except KeyError:
            raise KeyError(
            f"Столбца {where_col_name} нет в таблице {table_name}")
        
    return updated_data
    
def info(table_data: list, table_name: str) -> dict:
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META]

    return {
        "table_name": table_name,
        "columns": columns,
        "num_rows": len(table_data),
    }
    

# Обработчики команд
def create_table_handler(table_name: str, columns: list):
    meta = _read_meta("create_table")
    meta = create_table(meta, table_name, columns)
    _write_meta("create_table", meta)
    save_table_data(table_name, [])
    return f"Таблица {table_name} успешно создана"

def drop_table_handler(table_name: str):
    meta = _read_meta("drop_table")
    meta = drop_table(meta, table_name)
    if meta is None:
        return "Удаление не производилось"
    _write_meta("drop_table", meta)
    delete_table(table_name)
    return f"Таблица {table_name} успешно удалена"

def list_tables_handler():
    meta = _read_meta("list_tables")

    if meta[TABLES_IN_META]:
        return "\n".join(meta[TABLES_IN_META])
    else:
        return "База данных не содержит ни одной таблицы"

def insert_handler(table_name: str, values: list):
    table_data = load_table_data(table_name)
    table_data = insert(table_data, table_name, values)
    save_table_data(table_name, table_data)
    
    return f"Строка в таблицу {table_name} успешно добавлена"


def select_handler(table_name: str, where_clause: tuple | None = None):
    table_data = load_table_data(table_name)
    table_data = select(table_data, table_name, where_clause)
 
    table_meta = load_meta_for_table(table_name)
    columns = table_meta[COLUMNS_IN_META]
    col_names = next(zip(*columns))
    table = PrettyTable()
    table.field_names = col_names

    for row in table_data:
        table.add_row([row[col] for col in col_names])
   
    return table

def update_handler(table_name: str, set_clause: tuple, where_clause: tuple):
    table_data = load_table_data(table_name)
    table_data = update(table_data, table_name, set_clause, where_clause)
    save_table_data(table_name, table_data)
    
    return f"Таблица {table_name} успешно обновлена"
 
def delete_handler(table_name: str, where_clause: tuple):
    table_data = load_table_data(table_name)
    table_data = delete(table_data, table_name, where_clause)
    if table_data is None:
        return "Удаление строк не выполнено"
    save_table_data(table_name, table_data)
    
    return f"В таблице {table_name} произведено удаление строк"
 
 
def info_handler(table_name: str):
    table_data = load_table_data(table_name)
    table_info = info(table_data, table_name)
    
    col_info = ", ".join(f"{cname}:{ctype}"
                         for cname, ctype in table_info["columns"])

    return f"""Таблица: {table_info["table_name"]}
Столбцы: {col_info}
Количество записей: {table_info["num_rows"]}
"""
