.PHONY: create-cluster build load-images deploy


API_IMAGE_NAME=myapi
WORKER_IMAGE_NAME=myworker
DOCKER_REGISTRY=mirckos
VERSION=latest
CLUSTER_NAME=kind-cluster
K8S_DIR=./k8s
DOC_DIR=./Dockerfiles


create-cluster:
	kind create cluster --name $(CLUSTER_NAME) --config $(K8S_DIR)/kind-config.yaml

delete-cluster:
	kind delete cluster --name $(CLUSTER_NAME)

build:
	docker build -t ${DOCKER_REGISTRY}/${API_IMAGE_NAME}:${VERSION} -f $(DOC_DIR)/Dockerfile.api .
	docker build -t ${DOCKER_REGISTRY}/${WORKER_IMAGE_NAME}:${VERSION} -f $(DOC_DIR)/Dockerfile.worker .

push:
	docker push $(DOCKER_REGISTRY)/$(API_IMAGE_NAME):$(VERSION)
	docker push $(DOCKER_REGISTRY)/$(WORKER_IMAGE_NAME):$(VERSION)

load-images:
	kind load docker-image ${DOCKER_REGISTRY}/${API_IMAGE_NAME}:${VERSION} --name ${CLUSTER_NAME}
	kind load docker-image ${DOCKER_REGISTRY}/${WORKER_IMAGE_NAME}:${VERSION} --name ${CLUSTER_NAME}

deploy:
	kubectl apply -f $(K8S_DIR)/redis.yaml
	kubectl apply -f $(K8S_DIR)/rabbitmq.yaml
	kubectl apply -f $(K8S_DIR)/api-deployment.yaml
	kubectl apply -f $(K8S_DIR)/api-service.yaml
	kubectl apply -f $(K8S_DIR)/worker-deployment.yaml

clean:
	kubectl delete -f $(K8S_DIR)/redis.yaml
	kubectl delete -f $(K8S_DIR)/rabbitmq.yaml
	kubectl delete -f $(K8S_DIR)/api-deployment.yaml
	kubectl delete -f $(K8S_DIR)/api-service.yaml
	kubectl delete -f $(K8S_DIR)/worker-deployment.yaml

full-clean: clean delete-cluster
	docker rmi ${DOCKER_REGISTRY}/${API_IMAGE_NAME}:${VERSION}
	docker rmi ${DOCKER_REGISTRY}/${WORKER_IMAGE_NAME}:${VERSION}





