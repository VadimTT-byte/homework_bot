import os
import sys
import exceptions
import time
import logging
import logger_config
import requests
from telegram.ext import Updater
from telegram import Bot
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger_config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except Exception as error:
        raise exceptions.MessageNotSendError(
            f'Не удалось отправить сообщение :( ошибка - {error}'
        )
    else:
        logger.info(f'Сообщение {message[:15]}... отправлено')


def get_api_answer(current_timestamp):
    """Получаем ответ от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        homework_response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
        STATUS_CODE = homework_response.status_code
        logger.info(f'Status code: {STATUS_CODE}')
        logger.info(
            f'Параметры params={params}, headers={HEADERS}'
        )
    except Exception as error:
        raise exceptions.RequestError(
            f'Ошибка при запросе к API: {error}'
        )
    if STATUS_CODE != HTTPStatus.OK:
        raise exceptions.ResponseNotEqualOK(
            f'Ответ API не равен 200 {STATUS_CODE}'
        )
    logger.info('Ответ от API получен! OK!')
    return homework_response.json()


def check_response(response):
    """Проверка API response на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')

    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise TypeError('Список работ не является списком')

    if len(homeworks) == 0:
        logger.debug('Нет новых статусов.')

    return homeworks


def parse_status(homework):
    """Информация о конкретной домашней работе и статус этой работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if homework_status not in HOMEWORK_STATUSES:
            raise exceptions.UnregisteredStatus(
                f'Неизвестный статус {homework_status}'
            )
    except exceptions.UnregisteredStatus as error:
        logger.error(
            f'Незадокументированный статус домашней работы {error}'
        )
    except Exception as error:
        raise KeyError(f'Не найден ключ - {error}')

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def find_tokens_or_exit():
    """Проверка проверки токенов."""
    if not check_tokens():
        logger.critical('Не найдены токены! Программа остановлена')
        sys.exit()


def main():
    """Основная логика работы бота."""
    find_tokens_or_exit()
    logger.info('Токены загружены')
    try:
        current_timestamp = int(time.time())
        bot = Bot(token=TELEGRAM_TOKEN)
        update = Updater(token=TELEGRAM_TOKEN)
        update.start_polling()
    except Exception as error:
        logger.exception(f'Соединение разорвано {error}')

    temp_status = 'reviewing'
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks and temp_status != homeworks['status']:
                message = parse_status(homeworks)
                send_message(bot, message)
                logger.info('Сообщение отправлено')
                temp_status = homeworks['status']
            current_timestamp = int(time.time())

        except KeyError as error:
            logger.error(f'Не удалось получить статус работы {error}')
        except exceptions.RequestError as error:
            logger.exception(f'Ошибка при запросе к API: {error}')
        except exceptions.MessageNotSendError as error:
            logger.exception(
                f'Не удалось отправить сообщение :( ошибка - {error}'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)
            send_message(bot, message)
        finally:
            logger.info('Новых изменений нет...Время ожидания 10 мин.')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
