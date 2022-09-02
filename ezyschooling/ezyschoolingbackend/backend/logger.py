import logging
logger = logging.getLogger(__name__)
gunicorn_error_logger = logging.getLogger('gunicorn.error')
logger.handlers.extend(gunicorn_error_logger.handlers)
logger.setLevel(logging.INFO)

def log(msg,error=False):
    if error:
        logger.error("*"*30+"\n\t\t\t\t\t\t" + msg +"\n\t\t\t\t\t   "+"*"*30)
    else:
        logger.info(">"*30 +"\n\t\t\t\t\t\t" + msg +"\n\t\t\t\t\t   "+">"*30)

def error_logger(msg):
    logger.error("*"*30+"\n\t\t\t\t\t\t" + msg +"\n\t\t\t\t\t   "+"*"*30)

def info_logger(msg):
    logger.info(">"*30 +"\n\t\t\t\t\t\t" + msg +"\n\t\t\t\t\t   "+">"*30)
