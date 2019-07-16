import time
from conductor.ConductorWorker import ConductorWorker
from frinx_rest import conductor_url_base
import standalone_main


def main():
    print('Starting FRINX workers')
    cc = ConductorWorker(conductor_url_base, 1, 0.1)
    standalone_main.register_workers(cc)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
