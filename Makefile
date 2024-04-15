build:
	docker build -t modelapp .

run: build
	docker run -p 5000:5000 modelapp

deploy: 
	kubectl apply -f deployment.yaml

delete:
	kubectl delete -f deployment.yaml
