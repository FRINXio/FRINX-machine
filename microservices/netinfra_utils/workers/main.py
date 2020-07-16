import logging
import os
import time
import worker_wrapper
from frinx_rest import conductor_url_base
import cli_worker
import netconf_worker
import uniconfig_worker
import common_worker
import http_worker

logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


def setup_logging():
    log_level_str = os.getenv('LOG_LEVEL') or 'INFO'
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)


def main():
    setup_logging()
    logger.info('Starting FRINX workers')
    cc = worker_wrapper.ExceptionHandlingConductorWrapper(conductor_url_base, 1, 1)
    register_workers(cc)

    # block
    while 1:
        time.sleep(1000)


def register_workers(cc):
    cli_worker.start(cc)
    netconf_worker.start(cc)
    uniconfig_worker.start(cc)
    common_worker.start(cc)
    http_worker.start(cc)


if __name__ == '__main__':
    main()
