DOCKER_COMPOSE = docker-compose
SERVICE = flask-app
FLASK = flask
python = python

# Команди для міграцій
migrate:
	$(DOCKER_COMPOSE) run $(SERVICE) $(python) $(FLASK) db upgrade

makemigrations:
	$(DOCKER_COMPOSE) run $(SERVICE) $(python) $(FLASK) db migrate -m "Migrations"

# Команда для створення суперкористувача
createsuperuser:
	$(DOCKER_COMPOSE) run $(SERVICE) $(python) $(FLASK) createsuperuser

# Команди для роботи з Docker
docker-run:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up
