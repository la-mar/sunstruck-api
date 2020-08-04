COMMIT_HASH ?= $$(git log -1 --pretty=%h)
DATE := $$(date +"%Y-%m-%d")
CTX := .
DOCKERFILE := Dockerfile
IMAGE_NAME := sunstruck
APP_VERSION := $$(grep -o '\([0-9]\+.[0-9]\+.[0-9]\+\)' pyproject.toml | head -n1)

run-tests:
	pytest src/sunstruck tests/

recreate-and-seed-db:
	poetry shell && sunstruck db recreate && seed_db

cov:
	export CI=false && pytest -x --cov src/sunstruck tests/ --cov-report html:./coverage/coverage.html --log-cli-level 30 --log-level 20 -vv

cicov:
	export CI=true && pytest -x --cov src/sunstruck tests/ --cov-report html:./coverage/coverage.html --log-cli-level 10 --log-level 10 -vv

ncov:
	# generate cov report to stdout
	pytest --cov src/sunstruck tests/

view-cov:
	open -a "Google Chrome" ./coverage/coverage.html/index.html

login:
	docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}

build: login
	@echo "Building docker image: ${IMAGE_NAME}"
	docker build  -f ${DOCKERFILE} ${CTX} -t ${IMAGE_NAME}
	docker tag ${IMAGE_NAME} ${IMAGE_NAME}:${COMMIT_HASH}

push:
	docker push ${IMAGE_NAME}:dev
	docker push ${IMAGE_NAME}:${COMMIT_HASH}

push-version:
	docker push ${IMAGE_NAME}:${APP_VERSION}

all: build login push

secret-key:
	python3 -c 'import secrets;print(secrets.token_urlsafe(256))'

show-db-connections:
	# list all active database connections
	psql -c "select datname, usename, pid, client_addr from pg_stat_activity;"

set-max-connections:
	# timescale docker image defaults to max_connections=25
	psql -c "ALTER SYSTEM SET max_connections TO '500';"
