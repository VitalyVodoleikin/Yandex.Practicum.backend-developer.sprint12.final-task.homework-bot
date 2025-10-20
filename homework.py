import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telebot
from dotenv import load_dotenv

from exceptions import (
    CheckTokensError,
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
logger.addHandler(logging.StreamHandler(sys.stdout))
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
    if len(env_variables_stack):
        logger.critical('Необходимо указать все переменные окружения!')
        raise CheckTokensError(*env_variables_stack)


def get_api_answer(timestamp_label):
    """Отправка запроса и получение данных с API."""
    payload = {'from_date': timestamp_label}
    response_data = {'url': ENDPOINT,
                     'headers': HEADERS,
                     'params': payload}
    try:
        logger.debug(str.format(('Программа начала запрос '
                                 'на адрес {url} '
                                 'данные заголовка {headers} '
                                 'с параметрами {params}.'), **response_data))
        response = requests.get(**response_data)
    except requests.exceptions.RequestException as err:
        msg = f'Код ответа API: {err}'
        raise RequestExceptError(msg)
    if response.status_code != HTTPStatus.OK:
        msg = ('Статус-код ответа отличается от успешного: '
               f'{response.status_code}.')
        raise UnsuccessfulHTTPStatusCodeError(msg)
    return response.json()


def check_response(response):
    """Проверка данных запроса."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не имеет структуры словаря. '
                        f'Получен тип данных {type(response)}.')
    if 'homeworks' not in response:
        raise TypeError('В ответе нет ключа "homeworks".')
    response_homeworks = response.get('homeworks')
    if not isinstance(response_homeworks, list):
        raise TypeError('Данные под ключом "homeworks" не являются списком.'
                        f'Ключ "homeworks" содержит данные типа {
                            type(response_homeworks)}.')
    return response_homeworks


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
    timestamp_label = int(time.time())
    last_timestamp_label = None
    last_error = None
    while True:
        try:
            response = get_api_answer(timestamp_label)
            homework = check_response(response)
            if homework:
                homework = homework[0]
                message = parse_status(homework)
                homework_status = homework['status']
                logger.info(f'Статус проверки изменился: {homework_status}')
                if send_message(bot, message):
                    if response.get('from_date', last_timestamp_label):
                        last_timestamp_label = timestamp_label
                        timestamp_label = response['from_date']
            logger.info(
                'Статус проверки не изменился. '
                f'Повторная проверка через {RETRY_PERIOD / 60} минут.')
            last_error = None
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if last_error != error:
                send_message(bot, message)
                logger.error(message)
            last_error = error
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
