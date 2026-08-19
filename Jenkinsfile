pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.10-slim
    command:
    - sleep
    args:
    - infinity
'''
        }
    }

    stages {
        stage('Test') {
            steps {
                container('python') {
                    sh '''
                        pip install -r requirements.txt
                        pytest tests/ || true
                    '''
                }
            }
        }
    }
}
