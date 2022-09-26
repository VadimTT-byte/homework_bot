import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework_bot.log',
    format='%(asctime)s - %(name)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
    filemode='w'
)