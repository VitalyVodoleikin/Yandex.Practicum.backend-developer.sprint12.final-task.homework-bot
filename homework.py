import json
import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
import telebot

from exceptions import (
    CheckTokensError,
    EmptyDataError,
    RequestExceptError,
    UnknownStatusError,
    UnsuccessfulHTTPStatusCodeError)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('YANDEX_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


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
logger.addHandler(logging.FileHandler(
    filename='bot_check_homework_logs.log',
    mode='a',
    encoding='utf-8'))


def check_tokens():
    """Доступность токенов."""
    env_variables = {'practicum_token': PRACTICUM_TOKEN,
                     'telegram_token': TELEGRAM_TOKEN,
                     'telegram_chat_id': TELEGRAM_CHAT_ID}
    env_variables_stack = []
    for key, value in env_variables.items():
        if value is None:
            logger.critical(f'Не указана переменная окружения: {key}')
            env_variables_stack.append(key)
    if len(env_variables_stack) > 0:
        logger.critical('Необходимо указать все переменные окружения!')
        raise CheckTokensError(*env_variables_stack)
    return True


def get_api_answer(timestamp_label):
    """Отправка запроса и получение данных с API."""
    current_timestamp = timestamp_label or int(time.time())
    payload = {'from_date': current_timestamp}
    response_data = {'endpoint': ENDPOINT,
                     'headers': HEADERS,
                     'params': payload}
    try:
        logger.debug('Программа начала запрос '
                     f'на адрес {response_data['endpoint']} '
                     f'данные заголовка {response_data['headers']} '
                     f'с параметрами {response_data['params']}.')
        response = requests.get(response_data['endpoint'],
                                headers=response_data['headers'],
                                params=response_data['params'])
    except requests.exceptions.RequestException as err:
        msg = f'Код ответа API: {err}'
        raise RequestExceptError(msg)
    except json.JSONDecodeError as err:
        msg = f'Код ответа API: {err}'
        raise json.JSONDecodeError(msg)
    if response.status_code != HTTPStatus.OK:
        msg = ('Статус-код ответа отличается от успешного: '
               f'{response.status_code}.')
        raise UnsuccessfulHTTPStatusCodeError(msg)
    return response.json()


def check_response(response):
    """Проверка данных запроса."""
    if 'homeworks' in response:
        response_homeworks = response.get('homeworks')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не имеет структуры словаря. '
                        f'Получен тип данных {type(response)}.')
    if 'homeworks' not in response or not isinstance(response_homeworks, list):
        raise TypeError('Данные под ключом "homeworks" не являются списком.')
    if response_homeworks is None:
        msg = 'Получены некорректные данные.'
        raise EmptyDataError(msg)
    return response_homeworks[0]


def parse_status(homework):
    """Анализируем статус если изменился."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status is None:
        msg = f'Ошибка значения status: {status}.'
        raise UnknownStatusError(msg)
    if homework_name is None:
        msg = f'Ошибка значения homework_name: {homework_name}.'
        raise UnknownStatusError(msg)
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        msg = f'Неизвестный статус проверки: {status}.'
        raise UnknownStatusError(msg)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, msg):
    """Отправка сообщения в Телеграм."""
    try:
        logger.debug(f'Началась отправка сообщения в Telegram: {msg}')
        bot.send_message(TELEGRAM_CHAT_ID, msg)
        logger.debug(f'В Telegram отправлено сообщение: {msg}')
    except (telebot.apihelper.ApiException,
            requests.exceptions.RequestException) as err:
        logger.error(f'Ошибка при отправке сообщения: {err}. '
                     f'(Тип ошибки: {type(err).__name__})')
        return False
    return True


def main():
    """Основная логика работы бота."""
    check_tokens()
    # Создаем объект класса бота
    bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
    homework_status = 'reviewing'
    timestamp_label = int(time.time())
    errors_list = []
    while True:
        try:
            response = get_api_answer(timestamp_label)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                homework_status = homework['status']
                logger.info(f'Статус проверки изменился: {homework_status}')
                if send_message(bot, message):
                    if response.get('current_date'):
                        timestamp_label = response['current_date']
                    else:
                        raise Exception
            logger.info(
                'Статус проверки не изменился. '
                f'Повторная проверка через {RETRY_PERIOD / 60} минут.')
            errors_list.clear()
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if len(errors_list) > 0:
                if errors_list[0] != error:
                    send_message(bot, message)
                    logger.error(message)
            errors_list.append[error]
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        filename='bot_check_homework_logs.log',
        filemode='a',
        encoding='utf-8',)
    main()
