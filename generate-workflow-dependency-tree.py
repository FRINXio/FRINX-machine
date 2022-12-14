from collections import defaultdict
import requests
import json

def parse_response(response):
    decode = response.content.decode('utf8')
    try:
        response_json = json.loads(decode if decode else "{}")
    except ValueError as e:
        response_json = json.loads("{}")

    response_code = response.status_code
    return response_code, response_json


def parse_decision_task(tasks_by_workflow, workflow_name, decision_task):
    # recursively traverse nested decisions 
    if decision_task["type"] == "DECISION":
        parse_tasks(tasks_by_workflow, workflow_name, decision_task)
    if decision_task["type"] == "SUB_WORKFLOW":
        tasks_by_workflow[workflow_name].append(decision_task["subWorkflowParam"]["name"])
    else:
        tasks_by_workflow[workflow_name].append(decision_task["name"])


def parse_tasks(tasks_by_workflow, workflow_name, task):
    task_name = task["name"]
    task_type = task["type"]
    if task_type == "SUB_WORKFLOW":
        task_name = task["subWorkflowParam"]["name"]
    if task_type == "DECISION":
        for decision_case in task["decisionCases"].keys():
            for decision_task in task["decisionCases"][decision_case]:
                parse_decision_task(tasks_by_workflow, workflow_name, decision_task)
        for decision_task in task.get("defaultCase", []):
            parse_decision_task(tasks_by_workflow, workflow_name, decision_task)
        # keep also relation to system decision task
        task_name = "SYS-DECISION"
    # keep other system tasks as one task with prefix
    if task_type == "FORK_JOIN":
        task_name = "SYS-FORK_JOIN"
    if task_type == "JOIN":
        task_name = "SYS-JOIN"
    if task_type == "FORK_JOIN_DYNAMIC":
        task_name = "SYS-FORK_JOIN_DYNAMIC"
    if task_type == "LAMBDA":
        task_name = "SYS-LAMBDA"
    if task_type == "DYNAMIC":
        task_name = "SYS-DYNAMIC"
    if task_type == "HTTP":
        task_name = "SYS-HTTP"
    tasks_by_workflow[workflow_name].append(task_name)
    # add also dependency on task generated in worker for dynamic-task
    dfork_index = task_name.find("_as_dynamic_fork_tasks")
    if dfork_index is not -1:
        # tasks_by_workflow[workflow_name].append(task_name[0:dfork_index])
        tasks_by_workflow[workflow_name].append(task["inputParameters"]["task"])


def main():
    resp_worklows = requests.get("http://localhost:3000/api/conductor/metadata/workflow")
    resp_worklows_code, resp_worklows_json = parse_response(resp_worklows)
    tasks_by_workflow = defaultdict(list)
    for workflow in resp_worklows_json["result"]:
        workflow_name = workflow["name"]
        for task in workflow["tasks"]:
            parse_tasks(tasks_by_workflow, workflow_name, task)
    
    resp_tasks = requests.get("http://localhost:3000/api/conductor/metadata/taskdefs")
    resp_tasks_code, resp_tasks_json = parse_response(resp_tasks)
    tasks = []
    for task in resp_tasks_json["result"]:
        task_name = task["name"]
        tasks.append(task_name)

    print("Copy text below to http://www.webgraphviz.com/")
    print("digraph dependencies {")
    print("ratio = fill")
    print("node [style=filled]")
    for workflow in tasks_by_workflow:
        for task in tasks_by_workflow[workflow]:
            print('  "' + workflow + '"' + " -> " + '"' + task + '"')
    for workflow in tasks_by_workflow:
        print('  "' + workflow + '"' + '[color="0.650 0.200 7.000"]')
    for task in tasks:    
        print('  "' + task + '"' + '[color="0.348 0.839 0.839"]')

    print("}")


if __name__ == '__main__':
    main()
