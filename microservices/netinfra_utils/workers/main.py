import time
import worker_wrapper
from frinx_rest import conductor_url_base

def main():
    print('Starting FRINX workers')
    cc = worker_wrapper.WorkerWrapper(conductor_url_base, 1, 0.1)
    worker_wrapper.register_workers(cc)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
