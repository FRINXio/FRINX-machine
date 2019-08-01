import time
from frinx_rest import conductor_url_base
import worker_wrapper
import standalone_main


def main():
    print('Starting FRINX workers')
    cc = worker_wrapper.ExceptionHandlingConductorWrapper(conductor_url_base, 1, 0.1)
    standalone_main.register_workers(cc)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
