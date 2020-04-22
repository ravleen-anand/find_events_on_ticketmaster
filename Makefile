.PHONY: image run

image:
	docker build -t city_events:latest -f Dockerfile .

run:
	docker run -it --rm \
		--name city_events \
		-p 127.0.0.1:8080:8080 \
		-v $(shell pwd)/app:/usr/src/app \
		city_events:latest