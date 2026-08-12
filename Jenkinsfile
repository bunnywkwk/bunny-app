pipeline {
    agent any

    environment {
        APP_NAME = 'bunny-app'
        DOCKER_REPO = 'bunnywkwk/bunny-app' 
        GITOPS_REPO_URL = 'github.com/bunnywkwk/bunny-gitops.git'
        GIT_SHORT_SHA = "${sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()}"
    }

    stages {
        stage('Determine Build Type') {
            steps {
                script {
                    if (env.TAG_NAME) {
                        // It is a Production Release (e.g., v1.0.0)
                        env.IS_PROD = 'true'
                        env.IMAGE_TAG = "${env.TAG_NAME}"
                        env.TARGET_GITOPS_FOLDER = "environments/production"
                        echo "Production Release Detected. Tag: ${env.IMAGE_TAG}"
                    } else if (env.BRANCH_NAME == 'staging') {
                        // It is a Staging Build
                        env.IS_STAGING = 'true'
                        env.IMAGE_TAG = "staging-${env.GIT_SHORT_SHA}"
                        env.TARGET_GITOPS_FOLDER = "environments/staging"
                        echo "Staging Build Detected. Tag: ${env.IMAGE_TAG}"
                    } else {
                        // It is a Feature Branch Build
                        env.IS_FEATURE = 'true'
                        echo "Feature Branch Detected. Running tests only."
                    }
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                sh '''
                    echo "Running Pytest..."
                    pip install -r requirements.txt httpx pytest
                    pytest
                '''
            }
        }

        stage('Build & Push Docker Image') {
            when {
                anyOf {
                    environment name: 'IS_STAGING', value: 'true'
                    environment name: 'IS_PROD', value: 'true'
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    script {
                        env.IMAGE = "${env.DOCKER_REPO}:${env.IMAGE_TAG}"
                    }
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        
                        echo "Building Docker image: ${env.IMAGE}"
                        docker build -t ${env.IMAGE} .
                        
                        echo "Pushing to Docker Hub..."
                        docker push ${env.IMAGE}
                    """
                }
            }
        }
        
        stage('Update GitOps Manifests') {
            when {
                anyOf {
                    environment name: 'IS_STAGING', value: 'true'
                    environment name: 'IS_PROD', value: 'true'
                }
            }
            steps {
                // Ensure you have a GitHub Personal Access Token saved in Jenkins as 'github-credentials'
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_TOKEN')]) {
                    sh """
                        # Clean up previous runs
                        rm -rf bunny-gitops

                        # 1. Clone the GitOps Repository
                        git clone https://${GITHUB_USER}:${GITHUB_TOKEN}@${env.GITOPS_REPO_URL}
                        cd bunny-gitops
                        
                        # 2. Checkout the correct branch based on environment
                        if [ "${env.IS_STAGING}" = "true" ]; then
                            git checkout main || git checkout -b main
                        elif [ "${env.IS_PROD}" = "true" ]; then
                            git checkout prod || git checkout -b prod
                        fi
                        
                        # 3. Update the image tag in the correct environment folder using sed
                        # This assumes you have a deployment.yaml file in the environments folder
                        sed -i "s|image: ${env.DOCKER_REPO}:.*|image: ${env.IMAGE}|g" ${env.TARGET_GITOPS_FOLDER}/deployment.yaml
                        
                        # 4. Commit and Push
                        git config user.email "jenkins@bunny-automation"
                        git config user.name "Jenkins GitOps"
                        git add .
                        git commit -m "Automated CI: Update ${env.APP_NAME} image to ${env.IMAGE_TAG} in ${env.TARGET_GITOPS_FOLDER}" || echo "No changes to commit"
                        
                        if [ "${env.IS_STAGING}" = "true" ]; then
                            git push origin main
                        elif [ "${env.IS_PROD}" = "true" ]; then
                            git push origin prod
                        fi
                    """
                }
            }
        }
    }
}
