FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

COPY build/libs/*SNAPSHOT.jar app.jar
COPY src/main/resources/template_schema.json template_schema.json

RUN mkdir -p /app/outputs /app/config

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
