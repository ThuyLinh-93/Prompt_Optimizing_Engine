pipeline {
    agent any
    environment {
        HARBOR_HOST = "10.202.227.93"
        HARBOR_PROJECT = "ai-agent"
        IMAGE_NAME = "ai-review-agent"
        IMAGE_TAG = sh(script: 'git describe --tags --always 2>/dev/null || git rev-parse --short HEAD', returnStdout: true).trim()
        FULL_IMAGE_NAME = "${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
        DOCKERFILE_DIR = "."
    }

    stages {
         stage('Checkout') {
             steps {
                 checkout scm
             }
         }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERFILE_DIR}
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'harbor-docker-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login "${HARBOR_HOST}" -u "$DOCKER_USER" --password-stdin
                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}
                        docker push ${FULL_IMAGE_NAME}
                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                        docker push ${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }
    }
}