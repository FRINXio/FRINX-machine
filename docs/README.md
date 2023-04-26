# FRINX machine

## Components resource utilization characteristics

Specifies (on a very high level) how resource intensive individual components of FRINX machine are in terms of low - medium - high.

| Component   | CPU         | RAM         | Disk        | Network    |
| ----------- | ----------- | ----------- | ----------- | ---------- |
| Uniconfig   | High        | High        | Medium      | Medium     |
| UC LB Traefik | Low       | Low         | Low         | High       |
| Postgres    | Medium      | Low         | High        | Medium     |
| Conductor   | High        | Medium      | Low         | Medium     |
| WF proxy    | Medium      | Low         | Low         | Medium     |
| Schellar    | Low         | Low         | Low         | Low        |
| Workers     | -           | -           | -           | -          |
| Inventory   | Low         | Low         | Low         | Low        |
| API gateway | Low         | Low         | Low         | High       |
| Resource mgr | Low        | Low         | Low         | Low        |
