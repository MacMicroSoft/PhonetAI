DOCKER_COMPOSE = docker-compose
SERVICE = flask-app
POETRY = poetry
FLASK = flask

# Команди для міграцій
migrate:
	$(DOCKER_COMPOSE) run $(SERVICE) $(python) $(FLASK) db upgrade

makemigrations:
	$(DOCKER_COMPOSE) run $(SERVICE) $(python) $(FLASK) db migrate -m "Migrations"

# Команди для роботи з Docker
docker-run:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up
