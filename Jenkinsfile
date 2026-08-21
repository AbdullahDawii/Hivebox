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
                        pip install pylint
                        pylint main.py || true
                    '''
                }
                container('kaniko') {
                    sh '''
                        wget -q https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -O /tmp/hadolint
                        chmod +x /tmp/hadolint
                        /tmp/hadolint Dockerfile || true
                    '''
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
