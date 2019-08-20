import uniconfig_worker

# Uniconfig RPCs


def replace_cfg_with_oper(device_1, device_2):
    return uniconfig_worker.replace_config_with_oper({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def sync_from_net(device_1, device_2):
    return uniconfig_worker.sync_from_network({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def dryrun_commit(device_1, device_2):
    return uniconfig_worker.dryrun_commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


def commit(device_1, device_2):
    return uniconfig_worker.commit({'inputData': {
        'devices': [device_1.id, device_2.id],
    }})


# Retval Macros


def fail(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'FAILED', 'output': output, 'logs': [log]}


def complete(log, **kwargs):
    output = {}
    output.update(kwargs)
    return {'status': 'COMPLETED', 'output': output, 'logs': [log]}


def task_failed(task_response):
    return task_response['status'] is not 'COMPLETED'


def uniconfig_task_failed(task_response):
    config_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-configuration-status', 'fail')
    sync_status = task_response.get('output', {}).get('response_body', {}).get('output', {}).get('overall-sync-status', 'fail')
    return config_status == "fail" and sync_status == "fail"
