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
    command: ["sleep"]
    args: ["infinity"]
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: ["sleep"]
    args: ["infinity"]
'''
        }
    }

    stages {
        stage('Test') {
            steps {
                container('python') {
                    sh '''
                        pip install -r requirements.txt
                        pytest tests/ -v
                    '''
                }
            }
        }

        stage('Build') {
            steps {
                container('kaniko') {
                    sh '''
                        /kaniko/executor \
                        --context `pwd` \
                        --dockerfile `pwd`/Dockerfile \
                        --no-push \
                        --destination hivebox-app:latest
                    '''
                }
            }
        }
    }
}
