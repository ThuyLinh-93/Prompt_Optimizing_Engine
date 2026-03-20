pipeline {
    agent any

    tools {
        jdk 'openjdk 17'
    }

    environment {
        HARBOR_HOST = "10.202.227.93"
        HARBOR_PROJECT = "ai-agent"
        IMAGE_NAME = "ai-optimize-agent"
        IMAGE_TAG = "1.2.2"
        FULL_IMAGE_NAME = "${HARBOR_HOST}/${HARBOR_PROJECT}/${IMAGE_NAME}:${IMAGE_TAG}"
        DOCKER_FILE_DIR = "."
    }

    stages {
        stage('Build Jar') {
            steps {
                sh './gradlew clean build'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} \
                        --build-arg JAR_FILE=build/libs/ai-optimize-agent-0.0.1-SNAPSHOT.jar .
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'xocaffesy-docker-cred', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}
                        docker push ${FULL_IMAGE_NAME}
                    '''
                }
            }
        }
    }
}