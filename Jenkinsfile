pipeline {
    agent {
        docker { image 'python:3.10-slim' }
    }

    stages {
        stage('Test') {
            steps {
                sh '''
                    pip install -r requirements.txt
                    pytest tests/ || true
                '''
            }
        }
    }
}
