#!/bin/bash

set -e
set -u


function create_pgcron() {
	echo "  Creating cron extension"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE EXTENSION IF NOT EXISTS pg_cron;
		DELETE FROM cron.job;

		CREATE OR REPLACE FUNCTION remove_inactive_slots()
			RETURNS void AS
		\$\$
		DECLARE
			slot text;
		BEGIN
			FOR slot IN
				SELECT slot_name FROM pg_replication_slots WHERE active_pid IS NULL AND active = 'f'
			LOOP
				-- Drop the replication slot using the retrieved slot name
				EXECUTE 'SELECT pg_drop_replication_slot(' || quote_literal(slot) || ')';
			END LOOP;
		END;
		\$\$ LANGUAGE plpgsql;

		CREATE OR REPLACE FUNCTION clean_executed_cron_jobs()
			RETURNS void AS
		\$\$
		BEGIN
			DELETE FROM cron.job_run_details;
		END;
		\$\$ LANGUAGE plpgsql;
	
		SELECT cron.schedule('@hourly', \$\$SELECT remove_inactive_slots()\$\$);
		SELECT cron.schedule('@daily', \$\$SELECT clean_executed_cron_jobs()\$\$);
	EOSQL
}

create_pgcron
