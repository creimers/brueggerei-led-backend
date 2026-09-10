# Everything runs inside Docker Compose; nothing is run natively.
# See README.md.

COMPOSE := docker compose
RUN := $(COMPOSE) run --rm django
PROD := $(COMPOSE) -f production.yml

.PHONY: all build up down runserver migrate superuser shell test lock lock-check rollout

all: build

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

runserver:
	$(COMPOSE) up

migrate:
	$(RUN) uv run manage.py migrate

superuser:
	$(RUN) uv run manage.py createsuperuser

shell:
	$(RUN) uv run manage.py shell

test:
	$(RUN) uv run manage.py test

# Dependency management. The virtualenv is baked into the image, so rebuild
# (make build) after uv.lock changes.
lock:
	$(RUN) uv lock

lock-check:
	$(RUN) uv lock --check

# Zero-downtime deploy on the VM: build the new image, then let
# docker rollout start it next to the old container, wait for the
# healthcheck and drain the old one.
rollout:
	$(PROD) build django
	docker rollout -f production.yml django
