from __future__ import print_function

import json
import os
import shutil
import subprocess
import tempfile
from string import Template


def execute_terraform_apply(task):
    params = task['inputData']['params'] if task['inputData']['params'] else {}
    main_template = task['inputData']['main_template']
    output_template = task['inputData']['output_template'] if task['inputData']['output_template'] else ""
    output_template = output_template.replace("$#{", "${")
    env_vars = task['inputData']['env_vars'] if task['inputData']['env_vars'] else {}
    env_vars = env_vars if isinstance(env_vars, dict) else eval(env_vars)

    env = get_env(env_vars)

    tmp_dir = tempfile.mkdtemp()

    main_content = Template(main_template).substitute(params)
    write_file(tmp_dir, 'main.tf', main_content)

    if output_template is not "":
        write_file(tmp_dir, 'output.tf', output_template)

    init_output, error = invoke(tmp_dir, "terraform init -no-color -input=false", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'error': error},
                'logs': ["Unable to invoke terraform init in: %s, due to: %s" % (tmp_dir, error)]}

    apply_output, error = invoke(tmp_dir, "terraform apply -no-color -input=false -auto-approve", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'init': init_output, 'error': error},
                'logs': ["Unable to invoke terraform apply in: %s, due to: %s" % (tmp_dir, error)]}

    output, error = invoke(tmp_dir, "terraform output -no-color -json", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'init': init_output, 'apply': output, 'error': error},
                'logs': ["Unable to invoke terraform output in: %s, due to: %s" % (tmp_dir, error)]}

    output_json = json.loads(output)
    tfstate = parse_json(read_file(tmp_dir, "terraform.tfstate"))

    # Cleanup
    shutil.rmtree(tmp_dir)

    return {'status': 'COMPLETED',
            'output': {"init": init_output,
                       "apply": apply_output,
                       "output": output_json,
                       "tmp_dir": tmp_dir,
                       "main_tf": main_content,
                       "tf_state": tfstate},
            'logs': []}


def parse_json(string):
    try:
        json_content = json.loads(string if string else "{}")
    except ValueError as e:
        json_content = json.loads("{}")

    return json_content


def execute_terraform_plan(task):
    params = task['inputData']['params'] if task['inputData']['params'] else {}
    main_template = task['inputData']['main_template']
    env_vars = task['inputData']['env_vars'] if task['inputData']['env_vars'] else {}
    env_vars = env_vars if isinstance(env_vars, dict) else eval(env_vars)

    env = get_env(env_vars)

    tmp_dir = tempfile.mkdtemp()

    main_content = Template(main_template).substitute(params)
    write_file(tmp_dir, 'main.tf', main_content)

    init_output, error = invoke(tmp_dir, "terraform init -no-color -input=false", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'error': error},
                'logs': ["Unable to invoke terraform init in: %s, due to: %s" % (tmp_dir, error)]}

    output, error = invoke(tmp_dir, "terraform plan -no-color -input=false", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'init': init_output, 'error': error},
                'logs': ["Unable to invoke terraform init in: %s, due to: %s" % (tmp_dir, error)]}

    # Cleanup
    shutil.rmtree(tmp_dir)

    return {'status': 'COMPLETED',
            'output': {"init": init_output,
                       "apply": output,
                       "tmp_dir": tmp_dir,
                       "main_tf": main_content},
            'logs': []}


def get_env(env_vars):
    env = os.environ.copy()
    for key in env_vars:
        env[key] = env_vars[key]
    return env


def write_file(dirpath, file_name, content):
    main_concrete = open(dirpath + "/" + file_name, 'w')
    main_concrete.write(content)
    main_concrete.close()


def read_file(dirpath, file_name):
    main_concrete = open(dirpath + "/" + file_name, 'r')
    read = main_concrete.read()
    main_concrete.close()
    return read


def invoke(dirpath, cmd, env):
    process = subprocess.Popen(cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=dirpath, env=env)
    return process.communicate()


def execute_terraform_destroy(task):
    main_template = task['inputData']['main_template']
    tf_state = task['inputData']['tf_state']
    tf_state = tf_state if isinstance(tf_state, basestring) else json.dumps(tf_state)
    env_vars = task['inputData']['env_vars'] if task['inputData']['env_vars'] else {}
    env_vars = env_vars if isinstance(env_vars, dict) else eval(env_vars)

    env = get_env(env_vars)

    tmp_dir = tempfile.mkdtemp()

    write_file(tmp_dir, 'main.tf', main_template)
    write_file(tmp_dir, 'terraform.tfstate', tf_state)

    init_output, error = invoke(tmp_dir, "terraform init -no-color -input=false", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'error': error},
                'logs': ["Unable to invoke terraform init in: %s, due to: %s" % (tmp_dir, error)]}

    output, error = invoke(tmp_dir, "terraform destroy -no-color -input=false -auto-approve", env)
    if error is not None and error is not "":
        return {'status': 'FAILED',
                'output': {'destroy': output, 'init': init_output, 'error': error},
                'logs': ["Unable to invoke terraform destroy in: %s, due to: %s" % (tmp_dir, error)]}

    # Cleanup
    shutil.rmtree(tmp_dir)

    return {'status': 'COMPLETED',
            'output': {"destroy": output,
                       "tmp_dir": tmp_dir,
                       "main_tf": main_template},
            'logs': []}


def start(cc):
    print('Starting Terraform workers')

    cc.start('TERRAFORM_apply', execute_terraform_apply, False)
    cc.start('TERRAFORM_plan', execute_terraform_plan, False)
    cc.start('TERRAFORM_destroy', execute_terraform_destroy, False)
