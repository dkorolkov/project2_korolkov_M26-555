import re
import shlex
from collections.abc import Callable

import prompt

from decorators import create_cacher

from .core import (
    create_table_handler,
    delete_handler,
    drop_table_handler,
    info_handler,
    insert_handler,
    list_tables_handler,
    select_handler,
    update_handler,
)

first_message = "Первая попытка запустить проект!\n\n***"
command_prompt = "Введите команду: "

def welcome():
    print(first_message)
    print_help()
    
def run():
    while True:
        command_string = prompt.string(command_prompt)
        try:
            command, command_data, handler = parse(command_string)
        except KeyError:
            print(f"Неизвестная команда {command_string}")
            continue
        except (TypeError, ValueError) as exc:
            print(f"Ошибка при чтении команды {command_string}: {exc!s}")
            continue

        if command == 'exit':
            break

        result = cache_manager(command, command_data, handler)
        if result is not None:
            print(result)

def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    for cmd in ("create_table", "list_tables", "drop_table"):
        print(f"<command> {cmd} {command_handlers[cmd][2]}")

    print("\n***Процесс работы с данными***")
    for cmd in ("insert", "select", "update", "delete", "info"):
        print(f"<command> {cmd} {command_handlers[cmd][2]}")
    
    print("\nОбщие команды:")
    for cmd in ("exit", "help"):
        print(f"<command> {cmd} {command_handlers[cmd][2]}")
    
def parse(command_string: str) -> (str, dict, Callable):
    tokens = shlex.shlex(command_string, posix=False, punctuation_chars=":=!<>()")
    tokens.whitespace_split = True
    tokens.commenters = ""
    tokens = list(tokens)
    command = tokens[0]
    if command not in command_handlers:
        raise KeyError(f"Неизвестная команда {command}")

    parser, handler = command_handlers[command][:2]
    if parser is None:
        return command, {}, None
        
    try:
        return parser(tokens) + (handler,)
    except ValueError as exc:
        raise ValueError(
        f"Неверный формат команды {command}: {exc!s}")
        
keywords = {"create_table", "drop_table", "list_tables",
            "select", "insert", "update", "delete",
            "from", "where"
            }
identifier_templare = re.compile(r"[A-Za-z_]\w*", re.ASCII)
def is_identtifier(word: str) -> bool:
    return identifier_templare.fullmatch(word) is not None and word not in keywords

def not_parse(tokens: list) -> dict:
    return tokens[0], {}

def create_table_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 2:
        raise ValueError("укажите имя таблицы")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    idx = 2
    columns = []
    column_set = set()
    while True:
        if len(tokens) == idx:
            break
        if len(tokens) < idx + 3:
            raise ValueError("Ошибка в описании столбцов")
        col_name = tokens[idx]
        if tokens[idx+1] != ':':
            raise ValueError("Ошибка в описании столбцов")
        col_type = tokens[idx+2]
        if not is_identtifier(col_name):
            raise ValueError(f"Имя столбца {col_name}" +\
                             " не является допустимым идентификатором")
        if col_name in column_set:
            raise ValueError(f"Имя столбца {col_name} повторяется")
            
        columns.append((col_name.lower(), col_type.lower()))
        idx += 3

    return command, {
        "table_name": table_name.lower(),
        "columns": columns,
    }

def drop_table_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 2:
        raise ValueError("Укажите имя таблицы")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")

    return command, {
        "table_name": table_name.lower(),
    }

def make_value(val: str):
    bool_values = {
        "true": True,
        "false": False,
    }
    if val.lower() in bool_values:
        return bool_values[val]
        
    if val[0] == '"' and val[-1] == '"':
        return val[1:-1]
        
    return int(val)

def insert_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 6:
        raise ValueError("Ошибка синтаксиса")
    if tokens[1] != "into":
        raise ValueError("Ошибка синтаксиса")
    table_name = tokens[2]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    if tokens[3] != "values":
        raise ValueError("Ошибка синтаксиса")
    if tokens[4] != "(" or tokens[-1] != ")":
        raise ValueError("Ошибка синтаксиса")

    values = []
    for val in tokens[5:-1]:
        try:
            values.append(make_value(val))
        except ValueError:
            raise TypeError(f"Недопустимый тип значения {val}")

    return command, {
        "table_name": table_name.lower(),
        "values": values,
    }

def select_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 3:
        raise ValueError("Ошибка синтаксиса")
    if tokens[1] != "from":
        raise ValueError("Ошибка синтаксиса")
    table_name = tokens[2]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    if len(tokens) == 3:
        return command, {
            "table_name": table_name.lower(),
        }
        
    if len(tokens) < 7:
        raise ValueError("Ошибка синтаксиса")

    if tokens[3] != "where":
        raise ValueError("Ошибка синтаксиса")

    col_name = tokens[4]
    if not is_identtifier(col_name):
        raise ValueError(f"Имя столбца {col_name}" +\
                         " не является допустимым идентификатором")
    cmp_operation = tokens[5]
    value_str = tokens[6]
    try:
        value = make_value(value_str)
    except ValueError:
        raise TypeError(f"Недопустимый тип значения {value_str}")

    return command, {
        "table_name": table_name.lower(),
        "where_clause": (col_name.lower(), cmp_operation, value),
    }

def delete_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 3:
        raise ValueError("Ошибка синтаксиса")
    if tokens[1] != "from":
        raise ValueError("Ошибка синтаксиса")
    table_name = tokens[2]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    if len(tokens) == 3:
        return command, {
            "table_name": table_name.lower(),
        }
        
    if len(tokens) < 7:
        raise ValueError("Ошибка синтаксиса")

    if tokens[3] != "where":
        raise ValueError("Ошибка синтаксиса")

    col_name = tokens[4]
    if not is_identtifier(col_name):
        raise ValueError(f"Имя столбца {col_name}" +\
                         " не является допустимым идентификатором")
    cmp_operation = tokens[5]
    value_str = tokens[6]
    try:
        value = make_value(value_str)
    except ValueError:
        raise TypeError(f"Недопустимый тип значения {value_str}")

    return command, {
        "table_name": table_name.lower(),
        "where_clause": (col_name.lower(), cmp_operation, value),
    }

def update_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) != 10:
        raise ValueError("Ошибка синтаксиса")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    if tokens[2] != "set":
        raise ValueError("Ошибка синтаксиса")

    set_col_name = tokens[3]
    if not is_identtifier(set_col_name):
        raise ValueError(f"Имя столбца {set_col_name}" +\
                         " не является допустимым идентификатором")
    if tokens[4] != "=":
        raise ValueError("Ошибка синтаксиса")

    set_value_str = tokens[5]
    try:
        set_value = make_value(set_value_str)
    except ValueError:
        raise TypeError(f"Недопустимый тип значения {set_value_str}")

    if tokens[6] != "where":
        raise ValueError("Ошибка синтаксиса")

    where_col_name = tokens[7]
    if not is_identtifier(where_col_name):
        raise ValueError(f"Имя столбца {where_col_name}" +\
                         " не является допустимым идентификатором")
    where_cmp_operation = tokens[8]
    where_value_str = tokens[9]
    try:
        where_value = make_value(where_value_str)
    except ValueError:
        raise TypeError(f"Недопустимый тип значения {where_value_str}")

    return command, {
        "table_name": table_name.lower(),
        "set_clause": (set_col_name.lower(), set_value),
        "where_clause": (where_col_name.lower(), where_cmp_operation, where_value),
    }

def info_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 2:
        raise ValueError("Укажите имя таблицы")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")

    return command, {
        "table_name": table_name.lower(),
    }

cachers = {}
cache_reset_commands = {"insert", "update", "delete", "drop_table"}
def select_table_closure(table_name, handler):
    def value_func(where_clause):
        return handler(table_name, where_clause)

    return value_func

def cache_manager(command, command_data, handler):
    if command == "select":
        table_name = command_data["table_name"]
        if table_name not in cachers:
            cachers[table_name] = create_cacher()

        return cachers[table_name](command_data.get("where_clause", None),
                        select_table_closure(table_name, handler)
               )
    elif command in cache_reset_commands:
        result = handler(**command_data)
        if result != "Ошибка":
            table_name = command_data["table_name"]
            cachers.pop(table_name, None)
        return result

    return handler(**command_data)

# Словарь команд.
# Ключ -- имя команды
# Значение -- кортеж из трёх элементов:
#             парсер команды, обработчик команды, описание команды
command_handlers = {
    "exit": (not_parse, None, "- выход из программы"),
    "help": (not_parse, print_help, "- справочная информация"),
    "create_table": (create_table_parser, create_table_handler,
                     "<имя_таблицы> <столбец1:тип> .. - создать таблицу"),
    "drop_table": (drop_table_parser, drop_table_handler,
                   "<имя_таблицы> - удалить таблицу"),
    "list_tables": (not_parse, list_tables_handler,
                   "- показать список всех таблиц"),
    "insert": (insert_parser, insert_handler,
        "into <имя_таблицы> values (<значение1>, <значение2>, ...)" +\
        " - создать запись."),
    "select": (select_parser, select_handler,
    "from <имя_таблицы>\n" +\
    "<command> select from <имя_таблицы> where <столбец> = <значение>" +\
    " - прочитать записи по условию."),
    "update": (update_parser, update_handler,
        "<имя_таблицы> set <столбец1> = <новое_значение1>" +\
        " where <столбец_условия> = <значение_условия> - обновить запись."),
    "delete": (delete_parser, delete_handler,
        "delete from <имя_таблицы> where <столбец> = <значение> " +\
        "- удалить запись."),
    "info": (info_parser, info_handler,
                   "<имя_таблицы> - вывести информацию о таблице."),
}
