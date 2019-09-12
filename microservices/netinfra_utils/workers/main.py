import time
import worker_wrapper
from frinx_rest import conductor_url_base
import cli_worker
import inventory_worker
import l3vpn_worker
import lldp_worker
import netconf_worker
import platform_worker
import terraform_worker
import uniconfig_worker
import unified_worker
import vll_worker
import vll_service_worker


def main():
    print('Starting FRINX workers')
    cc = worker_wrapper.ExceptionHandlingConductorWrapper(conductor_url_base, 1, 1)
    register_workers(cc)

    # block
    while 1:
        time.sleep(1000)


def register_workers(cc):
    cli_worker.start(cc)
    netconf_worker.start(cc)
    platform_worker.start(cc)
    l3vpn_worker.start(cc)
    lldp_worker.start(cc)
    inventory_worker.start(cc)
    unified_worker.start(cc)
    uniconfig_worker.start(cc)
    terraform_worker.start(cc)
    vll_worker.start(cc)
    vll_service_worker.start(cc)


if __name__ == '__main__':
    main()
