import functools
import json
from time import monotonic

import prompt


def handle_db_errors(func):
    """
    Этот декоратор реализован не так, как указано в задании,
    поскольку я изначально передавал в исключениях информацию
    о контексте ошибки для выдачи развёрнутой информации пользователю.
    
    Чтобы сохранить эту возможность и выполнить учебное задание по
    созданию декоратора, я бросаю из функций исключение со значениями
    параметров, а в декораторе формирую сообщение об ошибке.
    
    Это сообщение снова помещается в исключение, которое обрабатывется
    на уровне диалога с пользователем, где сообщение дополняется
    информацией, в зависимости от контекста выполнения.
    
    Например, если исключение возникло при выполнении команды,
    оно дополняется информацией, при выполнении какой команды
    возникла ошибка.
    """
    def make_message(exc, data_message):
        template = func.exceptions[exc.__class__]
        data = {}
        for pair in data_message.split(";"):
            key, val = pair.split("=")
            data[key] = val
        return template.format(**data)
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as exc:
            data_message = exc.args[1]
            message = make_message(exc, data_message)
            raise exc.__class__(exc.errno, message)
        except (KeyError, TypeError, UnicodeDecodeError,
                json.JSONDecodeError) as exc:
            args = exc.args
            data_message = args[0] if len(args) == 1 else str(args)
            message = make_message(exc, data_message)
            raise exc.__class__(message)
    return wrap
    
def confirm_action(action_name):
    def deco(func):
        def wrap(*args, **kwargs):
            answer = prompt.string(
            'Вы уверены, что хотите выполнить "{action_name}"? [y/n]')
            if answer.lower() == 'y':
                return func(*args, **kwargs)
        return wrap
    return deco
    
def log_time(func):
    def wrap(*args, **kwargs):
        start_time = monotonic()
        result = func(*args, **kwargs)
        end_time = monotonic()
        print(f"Функция {func.__name__} выполнилась за" +\
              f" {end_time-start_time:0.3f} секунд")
        return result
    return wrap
    
def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            print("Результат из кеша")
            return cache[key]
        else:
            print("Результат из БД")
            result = value_func(key)
            cache[key] = result
            return result
            
    return cache_result
