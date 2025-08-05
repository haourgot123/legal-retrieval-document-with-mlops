pipeline {
    agent any

    environment{
        registry = 'haourgot123/legal_chatbot_retrieval'
        registryCredential = 'dockerhub'
    }

    stages {
        stage ("Run Test") {
            steps {
                script {
                    echo 'Running tests...'
                    // Uncomment and adjust as needed
                    // sh './run-tests.sh'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo 'Building Docker image...'
                    dir("src/lawbot") {
                        sh "docker build -t ${registry}:v4 ."
                    }
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo 'Pushing Docker image...'
                    docker.withRegistry("", registryCredential) {
                        docker.image("${registry}:v4").push()
                        docker.image("${registry}:v4").push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm' // Name of the container to be used for helm upgrade
                        image 'haourgot123/jenkins:lts-jdk17' // The image containing helm
                        alwaysPullImage true // Always pull image in case of using the same tag
                    }
                }
            }
            steps {
                script {
                    container('helm') {
                        sh("helm upgrade --install legal-chatbot ./helm_charts/legal_chatbot --namespace model-serving")
                    }
                }
            }
        }
    }
}
