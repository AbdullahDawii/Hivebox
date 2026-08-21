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
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  - name: hadolint
    image: hadolint/hadolint:latest-debian
    command: ["sleep"]
    args: ["infinity"]
  volumes:
  - name: docker-config
    secret:
      secretName: ghcr-secret
      items:
      - key: .dockerconfigjson
        path: config.json
'''
        }
    }
    stages {
        stage('Lint') {
            steps {
                container('python') {
                    sh '''
                        pip install -r requirements.txt
                        pylint main.py || true
                    '''
                }
            }
        }
        stage('Dockerfile Lint') {
            steps {
                container('hadolint') {
                    sh 'hadolint Dockerfile || true'
                }
            }
        }
        stage('Test') {
            steps {
                container('python') {
                    sh '''
                        pip install -r requirements.txt
                        pytest tests/ -v --ignore=tests/e2e
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
                        --destination ghcr.io/abdullahdawii/hivebox-app:latest
                    '''
                }
            }
        }
    }
}
