# Frinx Machine architecture

Uniconfig part of Frinx Machine is horizontally and vertically scalable and provide variety deployment options based on customer requirements.

Terminology:
 - Single-node deployment: All FM services including Uniconfig are running on swarm master node
 - Multi-node deployment: Uniconfig services are distributed on swarm worker nodes
 - Single-zone deployment: Only one Uniconfig zone is deployed. Default zone name is uniconfig
 - Multi-zone deployment: Multiple Uniconfig zones with are deployed. Each zone must have unique name

## Default deployment architecture 
Single-node and single-zone, only one unicnfig-controller replica is running.

![Frinx Machine architecture](assets/fm_architecture.svg "Frinx Machine architecture" )

</br>

## Enhanced deployment architecture 
Contain two uniconfig zones (uniconfig1, uniconfig2). Each zone contain 4 replicas (1,2,3,4) of uniconfig controller, which are deployed on 2 worker nodes. Uniconfig-postgres is deployed only on one node in zone. Each zone has deployed also Telegraf monitoring service. 

![Frinx Machine multinode architecture](assets/fm_architecture_multinode.svg "Frinx Machine multinode architecture" )
