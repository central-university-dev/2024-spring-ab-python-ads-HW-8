# Makefile
create-cluster:
	kind create cluster --config=kind-cluster.yaml

deploy-redis:
	kubectl apply -f redis-deployment.yaml
	kubectl apply -f redis-service.yaml

deploy-rabbitmq:
	kubectl apply -f rabbitmq-deployment.yaml
	kubectl apply -f rabbitmq-service.yaml

build-container:
	docker build -t myapp:latest .

deploy-app:
	kubectl apply -f app-deployment.yaml
	kubectl apply -f app-service.yaml

all: create-cluster deploy-redis deploy-rabbitmq build-container deploy-app
