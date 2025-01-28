DOCKER_COMPOSE = docker-compose
SERVICE = flask-app
FLASK = flask

# Команди для міграцій
migrate:
	$(DOCKER_COMPOSE) run $(SERVICE) $(FLASK) db upgrade

makemigrations:
	$(DOCKER_COMPOSE) run $(SERVICE) $(FLASK) db migrate -m "Migrations"

# Команда для створення суперкористувача
createsuperuser:
	$(DOCKER_COMPOSE) run flask-app flask createsuperuser --username $(username) --email $(email) --password $(password)

# Команди для роботи з Docker
docker-run:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) up
