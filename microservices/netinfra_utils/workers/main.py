import time
from conductor.ConductorWorker import ConductorWorker
import cli_worker
import platform_worker
import l3vpn_worker
import lldp_worker
import inventory_worker
import unified_worker
import terraform_worker
import uniconfig_worker
import frinx_rest
from frinx_rest import conductor_url_base

def main():
    print('Starting FRINX workers')
    cc = ConductorWorker(conductor_url_base, 1, 0.1)

    cli_worker.start(cc)
    platform_worker.start(cc)
    l3vpn_worker.start(cc)
    lldp_worker.start(cc)
    inventory_worker.start(cc)
    unified_worker.start(cc)
    uniconfig_worker.start(cc)
    terraform_worker.start(cc)

    # block
    while 1:
        time.sleep(1)


if __name__ == '__main__':
    main()
