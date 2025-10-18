from http import HTTPStatus
import json
import logging
import os
import time

import requests

from exceptions import (
    EmptyDataError, RequestExceptError,
    TelegramMsgError, UnknownStatusError,
    UnsuccessfulHTTPStatusCodeError)
from telebot import TeleBot
from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('YANDEX_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

env_variables = {
    'practicum_token': PRACTICUM_TOKEN,
    'telegram_token': TELEGRAM_TOKEN,
    'telegram_chat_id': TELEGRAM_CHAT_ID}

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def check_tokens():
    """Доступность токенов."""
    msg = ('Не указана переменная окружения:')
    tokens_availability = True
    if PRACTICUM_TOKEN is None:
        tokens_availability = False
        logger.critical(f'{msg} PRACTICUM_TOKEN')
    if TELEGRAM_TOKEN is None:
        tokens_availability = False
        logger.critical(f'{msg} TELEGRAM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        tokens_availability = False
        logger.critical(f'{msg} TELEGRAM_CHAT_ID')
    return tokens_availability


def get_api_answer(timestamp_label):
    """Отправка запроса и получение данных с API."""
    current_timestamp = timestamp_label or int(time.time())
    payload = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            msg = 'Нет доступа к эндпоинту.'
            # logger.error(msg)
            raise UnsuccessfulHTTPStatusCodeError(msg)
        return response.json()
    except requests.exceptions.RequestException as err:
        msg = f'Код ответа API: {err}'
        # logger.error(msg)
        raise RequestExceptError(msg)
    except json.JSONDecodeError as err:
        msg = f'Код ответа API: {err}'
        # logger.error(msg)
        raise json.JSONDecodeError(msg)


def check_response(response):
    """Проверка данных запроса."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не имеет структуры словаря')
    if 'homeworks' not in response or not isinstance(
        response['homeworks'],
        list
    ):
        raise TypeError('Данные под ключом "homeworks" не являются списком')
    if response.get('homeworks') is None:
        msg = 'Получены некорректные данные.'
        # logger.error(msg)
        raise EmptyDataError(msg)
    # if response['homeworks'] == []:
    #     msg = 'Получен пустой ответ.'
    #     logger.debug(msg)
    #     return {}
    # status = response['homeworks'][0].get('status')
    # if status not in HOMEWORK_VERDICTS:
    #     msg = f'Неизвестный статус проверки работы: {status}'
    #     logger.error(msg)
    #     raise UnknownStatusError(msg)
    return response['homeworks'][0]


def parse_status(homework):
    """Анализируем статус если изменился."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status is None:
        msg = f'Ошибка значения status: {status}.'
        # logger.error(msg)
        raise UnknownStatusError(msg)
    if homework_name is None:
        msg = f'Ошибка значения homework_name: {homework_name}.'
        # logger.error(msg)
        raise UnknownStatusError(msg)
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        msg = f'Неизвестный статус проверки: {status}.'
        # logger.error(msg)
        raise UnknownStatusError(msg)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, msg):
    """Отправка сообщения в Телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, msg)
        logger.debug(f'В Telegram отправлено сообщение: {msg}')
    # except TelegramMsgError as err:
    #     logger.error(f'Сообщение в Telegram не отправлено: {err}')
    except Exception as err:  # Ловим все возможные ошибки отправки
        logger.error(f'Ошибка при отправке сообщения: {err}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    homework_status = 'reviewing'
    timestamp_label = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp_label)
            homework = check_response(response)
            if homework and homework_status != homework['status']:
                message = parse_status(homework)
                homework_status = homework['status']
                logger.info(f'Статус проверки изменился: {homework_status}')
                send_message(bot, message)
            logger.info(
                'Статус проверки не изменился. '
                f'Повторная проверка через {RETRY_PERIOD / 60} минут.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        filename='bot_check_homework_logs.log',
        filemode='a',
        encoding='utf-8',)

    main()


















# ----------


























# # ==========>>>>>>>>>>
# from http import HTTPStatus
# import json
# import logging
# import os
# import time

# import requests

# from exceptions import (
#     EmptyDataError, RequestExceptError,
#     TelegramMsgError, UnknownStatusError,
#     UnsuccessfulHTTPStatusCodeError)
# from telebot import TeleBot
# from dotenv import load_dotenv


# load_dotenv()


# PRACTICUM_TOKEN = os.getenv('YANDEX_TOKEN')
# TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# env_variables = {
#     'practicum_token': PRACTICUM_TOKEN,
#     'telegram_token': TELEGRAM_TOKEN,
#     'telegram_chat_id': TELEGRAM_CHAT_ID}

# RETRY_PERIOD = 600
# ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
# HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


# HOMEWORK_VERDICTS = {
#     'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
#     'reviewing': 'Работа взята на проверку ревьюером.',
#     'rejected': 'Работа проверена: у ревьюера есть замечания.'}


# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.DEBUG,
#     filename='bot_check_homework_logs.log',
#     filemode='a',
#     encoding='utf-8',)

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())


# def check_tokens():
#     """Доступность токенов."""
#     msg = ('Не указана переменная окружения:')
#     tokens_availability = True
#     if PRACTICUM_TOKEN is None:
#         tokens_availability = False
#         logger.critical(f'{msg} PRACTICUM_TOKEN')
#     if TELEGRAM_TOKEN is None:
#         tokens_availability = False
#         logger.critical(f'{msg} TELEGRAM_TOKEN')
#     if TELEGRAM_CHAT_ID is None:
#         tokens_availability = False
#         logger.critical(f'{msg} TELEGRAM_CHAT_ID')
#     return tokens_availability


# def get_api_answer(endpoint):
#     """Отправка запроса и получение данных с API."""
#     current_timestamp = int(time.time())
#     headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
#     payload = {'from_date': current_timestamp}
#     try:
#         response = requests.get(endpoint, headers=headers, params=payload)
#         if response.status_code != HTTPStatus.OK:
#             msg = 'Нет доступа к эндпоинту.'
#             logger.error(msg)
#             raise UnsuccessfulHTTPStatusCodeError(msg)
#         return response.json()
#     except requests.exceptions.RequestException as err:
#         msg = f'Код ответа API: {err}'
#         logger.error(msg)
#         raise RequestExceptError(msg)
#     except json.JSONDecodeError as err:
#         msg = f'Код ответа API: {err}'
#         logger.error(msg)
#         raise json.JSONDecodeError(msg)


# def check_response(response):
#     """Проверка данных запроса."""
#     if not isinstance(response, dict):
#         raise TypeError('Ответ API не имеет структуры словаря')
#     if 'homeworks' not in response or not isinstance(
#         response['homeworks'],
#         list
#     ):
#         raise TypeError('Данные под ключом "homeworks" не являются списком')
#     if response.get('homeworks') is None:
#         msg = 'Получены некорректные данные.'
#         logger.error(msg)
#         raise EmptyDataError(msg)
#     if response['homeworks'] == []:
#         msg = 'Получен пустой ответ.'
#         logger.debug(msg)
#         return {}
#     status = response['homeworks'][0].get('status')
#     if status not in HOMEWORK_VERDICTS:
#         msg = f'Неизвестный статус проверки работы: {status}'
#         logger.error(msg)
#         raise UnknownStatusError(msg)
#     return response['homeworks'][0]


# def parse_status(homework):
#     """Анализируем статус если изменился."""
#     status = homework.get('status')
#     homework_name = homework.get('homework_name')
#     if status is None:
#         msg = f'Ошибка значения status: {status}.'
#         logger.error(msg)
#         raise UnknownStatusError(msg)
#     if homework_name is None:
#         msg = f'Ошибка значения homework_name: {homework_name}.'
#         logger.error(msg)
#         raise UnknownStatusError(msg)
#     try:
#         verdict = HOMEWORK_VERDICTS[status]
#     except KeyError:
#         msg = f'Неизвестный статус проверки: {status}.'
#         logger.error(msg)
#         raise UnknownStatusError(msg)
#     return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# def send_message(bot, msg):
#     """Отправка сообщения в Телеграм."""
#     try:
#         bot.send_message(TELEGRAM_CHAT_ID, msg)
#         logger.debug(f'В Telegram отправлено сообщение: {msg}')
#     except TelegramMsgError as err:
#         logger.error(f'Сообщение в Telegram не отправлено: {err}')
#     except Exception as err:  # Ловим все возможные ошибки отправки
#         logger.error(f'Ошибка при отправке сообщения: {err}')


# def main():
#     """Основная логика работы бота."""
#     if not check_tokens():
#         exit()
#     # Создаем объект класса бота
#     bot = TeleBot(token=TELEGRAM_TOKEN)
#     homework_status = 'reviewing'
#     while True:
#         try:
#             response = get_api_answer(ENDPOINT)
#             homework = check_response(response)
#             if homework and homework_status != homework['status']:
#                 message = parse_status(homework)
#                 homework_status = homework['status']
#                 logger.info(f'Статус проверки изменился: {homework_status}')
#                 send_message(bot, message)
#             logger.info(
#                 'Статус проверки не изменился. '
#                 f'Повторная проверка через {RETRY_PERIOD / 60} минут.')
#         except Exception as error:
#             message = f'Сбой в работе программы: {error}'
#             send_message(bot, message)
#             logger.error(message)
#         time.sleep(RETRY_PERIOD)


# if __name__ == '__main__':
#     main()
# # <<<<<<<<<<==========