# Makefile target to start PostgreSQL Docker container
# Inputs:
#   - None
# Outputs:
#   - Docker container named 'pg' running PostgreSQL with database 'movies_database'
#   - Local volume mounted to '/docker-entrypoint-initdb.d/' containing SQL dump 'dump_db.sql'
# Error handling:
#   - If the 'docker run' command fails, exit with error code 1
# Usage: make docker_pg_db

docker_pg_db:
	@docker run --name pg -p 5432:5432 \
		-e POSTGRES_USER=app \
		-e POSTGRES_PASSWORD=123qwe \
		-e POSTGRES_DB=movies_database \
		-d \
		-v $(PWD)/schema_design/dump_db.sql:/docker-entrypoint-initdb.d/dump_db.sql \
		postgres:16 || { echo "Failed to start PostgreSQL Docker container. Exiting." >&2; exit 1; }

schema:
	docker-compose exec pg psql -U app -d movies_database -f docker-entrypoint-initdb.d/dump_db.sql

# Makefile target to start Redis Docker container
redis:
	docker run -d --name redis -p 6379:6379 -p 8001:8001 redis

es:
	docker run -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.6.2
