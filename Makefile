build:
	docker-compose up -d --build

logs:
	docker logs livetracker -f
