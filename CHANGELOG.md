# Frinx Machine 1.9 RELEASE NOTE:
-----------------
## Frinx Machine
*    Credentials and certificates via docker secret

*    KrakenD custom certs via docker secrets

*    Multinode deployment, multiple placement methods can be used

*    Uniconfig and Traefik settings via docker config

*    Authorization and Authentification with Azure AD (AAA)

*    Added high-performance resource limits 

<br>

## Updated Services

### Uniconfig
*   Leaf-ref validation

*   Introduction of transaction idle-timeout

*   Removed AAA

*   Bug fixing


<br>

### Monitoring

*    InfluxDB instead of Prometheus

*    Telegraf instead of node-exported and cadvisor

### Conductor

*   Sanitize log4j  vulnerability

### Workflow-proxy

*    Fix RBAC issues

*    OpenAPI with AAA

*    Event sanitize

### Inventory

*    Transaction id to uniconfig API communication

*    Remove snapshots

*    Uniconfig zone tenant defined via env variable

### Frinx-Frontend

*   Bug fixing


### KrakenD

*    KrakenD Azure plugin with role claims to the header

*    KrakenD Azure plugin with optional group claims to the header

*    Validate certs during starting a container

### Resource manager

*    Add desired value for vlan strategy 

*    Rewrite and refactor ivp4 strategy

*    Update unique-id strategy

## REST API changes

### New workflow-proxy endpoints

*   **GET** - /oauth2-redirect.html   :  Swagger UI redirect url

*   **POST** - /api/uniflow/docs/token : CORS fixing token change url

### Removed workflow-proxy endpoints

*   **GET** - /api/uniflow/workflow/{a}
