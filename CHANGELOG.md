# Frinx Machine 1.7 RELEASE NOTE

## Uniconfig

* Using Uniconfig 4.2.8 - stateless model
* Multi-zone with multi-instance uniconfig deployment
* Use Traefik as a load balancer in front of Uniconfig instances in each zone 

## Conductor

* Update conductor server to 3.0.5
* Disabled ack check in client
* Changed health-check API
* Optimise Frinx Conductor Client - PyPi version 1.0.3

## Conductor workers

* Install/Uninstall RPCs
* Frinx Conductor Workers -  PyPi version 1.0.2

## Device inventory

* Replace old inventory with new Device Inventory

## KrakenD

* Update KrakenD image to v1.4.0
* Add default certificates to docker image
* No local building required
* Add log filtering plugin

## FM-Workflows

* Clean obsolete workflows
* Add device inventory worker
* Optimise tasts definitions for conductor client v 1.3.0
* Mock IOS02 as a separate device

## Docker secrets

* Store certificates in docker secrets

## Monitoring services

* Collecting swarm statistics 
* Collecting node statistics 
* Collecting logs of FM services
* Grafana visualisation
