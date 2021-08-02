-- /* Create tables */

-- CREATE TABLE protocol
-- (
--     id   serial NOT NULL PRIMARY KEY,
--     name text   NOT NULL
-- );

-- CREATE TABLE uniconfig_instance
-- (
--     id                   serial    NOT NULL PRIMARY KEY,
--     instance_name        text      NOT NULL,
--     backup_instance_name text      NULL,
--     host                 text      NOT NULL,
--     port                 integer   NOT NULL,
--     heartbeat_timestamp  timestamp NULL
-- );

-- CREATE TABLE node
-- (
--     id                     serial  NOT NULL PRIMARY KEY,
--     uniconfig_instance_id  integer NOT NULL,
--     management_protocol_id integer NOT NULL,
--     netconf_repository_id  integer NULL,
--     node_id                text    NOT NULL,
--     is_native              boolean NOT NULL,
--     mount_request          jsonb   NOT NULL,
--     config                 jsonb   NULL,
--     config_fingerprint     text    NULL
-- );

-- CREATE TABLE netconf_repository
-- (
--     id              serial NOT NULL PRIMARY KEY,
--     repository_name text   NOT NULL
-- );

-- CREATE TABLE yang_schema
-- (
--     id                    serial  NOT NULL PRIMARY KEY,
--     netconf_repository_id integer NOT NULL,
--     module_name           text    NOT NULL,
--     revision              date    NULL,
--     yang_data             bytea   NOT NULL
-- );

-- /* Create foreign key, check, and unique constraints (indexes are automatically created with unique constraints) */

-- ALTER TABLE protocol
--     ADD CONSTRAINT "UNIQUE_name"
--         UNIQUE (name);

-- ALTER TABLE uniconfig_instance
--     ADD CONSTRAINT "UNIQUE_instance_name"
--         UNIQUE (instance_name);

-- ALTER TABLE uniconfig_instance
--     ADD CONSTRAINT "UNIQUE_backup_instance_name"
--         UNIQUE (backup_instance_name);

-- ALTER TABLE uniconfig_instance
--     ADD CONSTRAINT "CHECK_port"
--         CHECK (port > 0 AND port < 65536);

-- ALTER TABLE node
--     ADD CONSTRAINT "UNIQUE_node_id"
--         UNIQUE (node_id);

-- ALTER TABLE node
--     ADD CONSTRAINT "FK_node_uniconfig_instance"
--         FOREIGN KEY (uniconfig_instance_id)
--             REFERENCES uniconfig_instance (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ALTER TABLE node
--     ADD CONSTRAINT "FK_node_protocol"
--         FOREIGN KEY (management_protocol_id)
--             REFERENCES protocol (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ALTER TABLE node
--     ADD CONSTRAINT "FK_node_netconf_repository"
--         FOREIGN KEY (netconf_repository_id)
--             REFERENCES netconf_repository (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ALTER TABLE yang_schema
--     ADD CONSTRAINT "FK_yang_schema_netconf_repository"
--         FOREIGN KEY (netconf_repository_id)
--             REFERENCES netconf_repository (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ALTER TABLE netconf_repository
--     ADD CONSTRAINT "UNIQUE_repository_name"
--         UNIQUE (repository_name);

-- /* Inserting of constant values */

-- INSERT INTO protocol (id, name)
-- VALUES (1, 'cli'),
--        (2, 'netconf');
-- SELECT SETVAL('protocol_id_seq', (SELECT MAX(id) from "protocol"));