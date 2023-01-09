# if docker-compose.yml is used, building own nginx container is skipped
FROM nginx:1.23.1-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
