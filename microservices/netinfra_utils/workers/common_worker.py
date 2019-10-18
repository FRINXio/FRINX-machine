import uniconfig_worker

INTERFACE_PRIORITY = 3                          #set the priority level on interface
INTERFACE_PRIORITY_FORCE = True                 #set the force priority on interface
INTERFACE_ISIS_PASSIVE = True                   #set passive mode on isis interface
INTERFACE_PREFIX = "IUP-"                       #set prefix to interface and router interface description
INTERFACE_PREFIX_2 = "IUP-phys-"                #set prefix to interface if description is not present
FREE_DESCRIPTION = "available"                  #set description on interface that is no longer needed in configuration and is free for next use





# Uniconfig RPCs


def replace_cfg_with_oper(device_ids):
    return uniconfig_worker.replace_config_with_oper({'inputData': {
        'devices': device_ids
    }})


def sync_from_net(device_ids):
    return uniconfig_worker.sync_from_network({'inputData': {
        'devices': device_ids,
    }})


def dryrun_commit(device_ids):
    response = uniconfig_worker.dryrun_commit({'inputData': {
        'devices': device_ids,
    }})
    replace_cfg_with_oper(device_ids)
    return response


def commit(device_ids):
    return uniconfig_worker.commit({'inputData': {
        'devices': device_ids,
    }})


# Retval Macros


def dryrun_response(description, debug, **kwargs):
    response = kwargs.get('response_dryrun')
    if task_failed(response) or uniconfig_task_failed(response):
        if debug:
            return fail(description, **kwargs)
        else:
            return fail(description, response_dryrun=response)

    description = description.replace("FAIL", "SUCCESS")
    if debug:
        # TODO attach journal
        return complete(description, **kwargs)
    else:
        return complete(description, response_dryrun=response)


def commit_response(device_ids, description, debug, **kwargs):
    response = kwargs.get('response_commit')
    if task_failed(response) or uniconfig_task_failed(response):
        replace_cfg_with_oper(device_ids)
        if debug:
            return fail(description, **kwargs)
        else:
            return fail(description, response_commit=response)

    description = description.replace("FAIL", "SUCCESS")
    if debug:
        return complete(description, **kwargs)
    else:
        return complete(description, response_commit=response)


def fail(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'FAILED', 'output': output, 'logs': [log]}


def complete(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'COMPLETED', 'output': output, 'logs': [log]}


def task_failed(task_response):
    return 'status' in task_response and task_response['status'] is not 'COMPLETED'


def uniconfig_task_failed(task_response):
    config_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-configuration-status', 'fail')
    sync_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-sync-status', 'fail')
    return config_status == "fail" and sync_status == "fail"


# Filter Strategies


def default_filter_strategy(type):
    return lambda ni: ni['config']['type'] == type


def name_filter_strategy(type, name):
    return lambda ni: ni['config']['type'] == type and ni['name'] == name


def vccid_filter_strategy(type, vccid):
    return lambda ni: ni['config']['type'] == type and 'connection-points' in ni \
                      and vccid in [cp['endpoints']['endpoint'][0]['remote']['config']['virtual-circuit-identifier'] for cp in
                                    filter(lambda cp: 'frinx-openconfig-network-instance-types:REMOTE' == cp['endpoints']['endpoint'][0]['config']['type'], ni['connection-points']['connection-point'])]
