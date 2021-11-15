# Frinx Machine 1.8 RELEASE NOTE:
-----------------

## Updated Services
### Uniconfig 4.2.9:

*   RPC install-multiple-nodes
    
*   Fix issues and improve stability
    
*   transactions, load balancing (without multizone support)
    

### Conductor:

*   External Storage with Postgres DB
    
*   Exposed in workflows proxy and also in KrakenD
    

### Micros:

*   Add transactions and load-balancing to CLI, NETCONF, UNICONFIG workers
    
*   Add worker for installing multiple devices in parallel
    
*   Add base workflows to pypi package
    

### Frinx Frontend:

*   Editor for workflow JSON's in UI
    
*   Used new KrakenD conductor endpoints
    

### Sample Topology:

*   Simulation of new device types (Junos,  iosxr 653, iosxr 663)
    
*   new simulated CLI cisco and Junos
    

### Demo Workflows:

*   new workflows
    
*   device identification (name, version, …) based on IP address
    
*   LLDP one device
    

### KrakenD:

*   removed obsolete endpoints
    
*   updated queries for searching
    
*   fixed query parsing for Uniconfig RPC’s
    

### Workflow Proxy:

*   updated endpoint for searching
    
*   add policy headers
    
*   swagger ui
    

### Monitoring services:

*   Monitoring services in global mode
    
*   Dashboards prepared for multi-node deployment
    
*   Replaced host id by hostname
    

### Device Inventory:

###   

Rest-api changes:
=================

### Removed krakend endpoints:

*   **POST** - /api/uniflow/executions
    
*   **GET** - /api/uniflow/schedule/{name}/{b}
    
*   **POST** - /api/uniconfig/rests/operations
    
*   **PUT, GET, PATCH, DELETE, POST** - /api/uniconfig/rests/data
    

### Changed KrakenD endpoints:

<table data-layout="full-width" data-local-id="b5b465ff-93a0-439f-9c10-c17c09c1dcc2" class="confluenceTable"><colgroup><col style="width: 231.0px;"><col style="width: 734.0px;"><col style="width: 111.0px;"><col style="width: 724.0px;"></colgroup><tbody><tr><th class="confluenceTh"><p><strong>METHOD</strong></p></th><th class="confluenceTh"><p><strong>OLD ENDPOINT</strong></p></th><th class="confluenceTh"><p><strong>METHOD</strong></p></th><th class="confluenceTh"><p><strong>NEW ENDPOINT</strong></p></th></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/metadata</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/metadata/workflow</p></td></tr><tr><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/api/uniflow/metadata/workflow/:name/:version</p></td><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/api/uniflow/metadata/workflow/{name}?version=</p></td></tr><tr><td class="confluenceTd"><p>DELETE</p></td><td class="confluenceTd"><p>/api/uniflow/bulk/terminate</p></td><td class="confluenceTd"><p>DELETE</p></td><td class="confluenceTd"><p>/api/uniflow/workflow/bulk/terminate</p></td></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/bulk/pause</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/workflow/bulk/pause</p></td></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/bulk/resume</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/api/uniflow/workflow/bulk/resume</p></td></tr><tr><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/api/uniflow/bulk/retry</p></td><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/api/uniflow/workflow/bulk/retry</p></td></tr><tr><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/api/uniflow/bulk/restart</p></td><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/api/uniflow/workflow/bulk/restart</p></td></tr></tbody></table>

### Changed KrakenD query inputs

<table data-layout="full-width" data-local-id="5c679ae8-0c97-4b4c-a589-fd8917db2b87" class="confluenceTable"><colgroup><col style="width: 605.0px;"><col style="width: 577.0px;"><col style="width: 618.0px;"></colgroup><tbody><tr><th class="confluenceTh"><p><strong>ENDPOINT</strong></p></th><th class="confluenceTh"><p><strong>OLD QUERY</strong></p></th><th class="confluenceTh"><p><strong>NEW QUERY</strong></p></th></tr><tr><td class="confluenceTd"><p>/api/uniflow/hierarchical</p></td><td class="confluenceTd"><p>?freeText=(workflowId:)AND(status:)&amp;start=&amp;size=</p></td><td class="confluenceTd"><p>?workflowId=&amp;status=&amp;start=&amp;size=&amp;order=</p><p>order inputs : DESC (default), ASC</p></td></tr><tr><td class="confluenceTd"><p>/api/uniflow/executions</p></td><td class="confluenceTd"><p>?q=&amp;h=&amp;freeText=(workflowId:)AND(status:)&amp;start=&amp;size=</p></td><td class="confluenceTd"><p>?q=&amp;h=&amp;workflowId=&amp;status=&amp;start=&amp;size=&amp;order=</p><p>order inputs : DESC (default), ASC</p></td></tr><tr><td class="confluenceTd"><p>/workflow/{a}</p></td><td class="confluenceTd"><p>?*</p></td><td class="confluenceTd"><p>?includeTask=</p></td></tr><tr><td class="confluenceTd"><p>/metadata/taskdefs/{name}</p></td><td class="confluenceTd"><p>?*</p></td><td class="confluenceTd"><p>?archiveWorfklow=</p></td></tr><tr><td class="confluenceTd"><p>/metadata/workflow/{name}</p></td><td class="confluenceTd"><p>?*</p></td><td class="confluenceTd"><p>?version=</p></td></tr></tbody></table>

### Removed workflow-proxy endpoints

*   **GET** - /schedule/metadata/workflow
    

### Changed workflow-proxy endpoints

<table data-layout="full-width" data-local-id="d7a2dfd7-0839-48c9-8d57-aa31f3e595fe" class="confluenceTable"><colgroup><col style="width: 231.0px;"><col style="width: 734.0px;"><col style="width: 111.0px;"><col style="width: 724.0px;"></colgroup><tbody><tr><th class="confluenceTh"><p><strong>METHOD</strong></p></th><th class="confluenceTh"><p><strong>OLD ENDPOINT</strong></p></th><th class="confluenceTh"><p><strong>METHOD</strong></p></th><th class="confluenceTh"><p><strong>NEW ENDPOINT</strong></p></th></tr><tr><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/shedule/?</p></td><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/schedule</p></td></tr><tr><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/metadata/workflow/:name/:version</p></td><td class="confluenceTd"><p>GET</p></td><td class="confluenceTd"><p>/metadata/workflow/{name}?version=</p></td></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/metadata</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/metadata/workflow</p></td></tr><tr><td class="confluenceTd"><p>DELETE</p></td><td class="confluenceTd"><p>/bulk/terminate</p></td><td class="confluenceTd"><p>DELETE</p></td><td class="confluenceTd"><p>/workflow/bulk/terminate</p></td></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/bulk/pause</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/workflow/bulk/pause</p></td></tr><tr><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/bulk/resume</p></td><td class="confluenceTd"><p>PUT</p></td><td class="confluenceTd"><p>/workflow/bulk/resume</p></td></tr><tr><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/bulk/retry</p></td><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/workflow/bulk/retry</p></td></tr><tr><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/bulk/restart</p></td><td class="confluenceTd"><p>POST</p></td><td class="confluenceTd"><p>/workflow/bulk/restart</p></td></tr></tbody></table>

### Changed workflow-proxy query inputs

<table data-layout="full-width" data-local-id="1ef74ee3-665e-4f01-8ce4-2a4b45a3f0c4" class="confluenceTable"><colgroup><col style="width: 605.0px;"><col style="width: 577.0px;"><col style="width: 618.0px;"></colgroup><tbody><tr><th class="confluenceTh"><p><strong>ENDPOINT</strong></p></th><th class="confluenceTh"><p><strong>OLD QUERY</strong></p></th><th class="confluenceTh"><p><strong>NEW QUERY</strong></p></th></tr><tr><td class="confluenceTd"><p>/hierarchical</p></td><td class="confluenceTd"><p>?freeText=(workflowId:)AND(status:)&amp;start=&amp;size=</p></td><td class="confluenceTd"><p>?workflowId=&amp;status=&amp;start=&amp;size=</p></td></tr><tr><td class="confluenceTd"><p>/executions</p></td><td class="confluenceTd"><p>?q=&amp;h=&amp;freeText=(workflowId:)AND(status:)&amp;start=&amp;size=</p></td><td class="confluenceTd"><p>?q=&amp;h=&amp;workflowId=&amp;status=&amp;start=&amp;size=</p></td></tr></tbody></table>