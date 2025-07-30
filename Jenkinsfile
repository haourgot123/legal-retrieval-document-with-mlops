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
                    docker.withRegistry("https://${registry}", registryCredential) {
                        docker.image("${registry}").push()
                        docker.image("${registry}").push('v4')
                    }
                }
            }
        }

        stage('Deploy') {
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm' // Name of the container to be used for helm upgrade
                        image 'haourgot123s/jenkins:lts-jdk17' // The image containing helm
                        alwaysPullImage true // Always pull image in case of using the same tag
                    }
                }
            }
            steps {
                script {
                    container('helm') {
                        sh("helm upgrade --install legal-chatbot ./helm-charts/legal-chatbot --namespace model-serving")
                    }
                }
            }
        }
    }
}
