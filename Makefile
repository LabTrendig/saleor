.PHONY: default
default:
	pip install -r requirements.txt
	pip install -r requirements_dev.txt

.PHONY: backend
backend:
	docker-compose run --rm --service-ports --use-aliases backend --shell

.PHONY: runserver
runserver:
	python manage.py runserver 0.0.0.0:8000

static:
	yarn run build-assets

.PHONY: build
build: static
	docker build \
		--build-arg STATIC_URL='/static/' \
		--tag registry.gitlab.com/trendig-it/ops/backend:production \
		.

push: build
	docker push \
		registry.gitlab.com/trendig-it/ops/backend:production
