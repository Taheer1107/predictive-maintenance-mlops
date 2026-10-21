pipeline {
    agent any
    triggers { pollSCM('H/5 * * * *') }
    options { disableConcurrentBuilds() }

    environment {
        PY  = 'C:\\Users\\Mohamed Taheer\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        ACR = 'mldockerimages123.azurecr.io'   // replace with your real login server
    }

    stages {
        stage('Clean') {
            steps {
                bat '''
                if exist mlruns rmdir /s /q mlruns
                if exist model rmdir /s /q model
                '''
            }
        }
        stage('Setup') {
            steps { bat '"%PY%" --version && "%PY%" -m venv venv && venv\\Scripts\\python -m pip install -r requirements.txt' }
        }
        stage('Train') {
            steps { bat 'venv\\Scripts\\python src\\train.py' }
        }
        stage('Quality gate') {
            steps { bat 'venv\\Scripts\\python src\\gate.py' }
        }
        stage('Export model') {
            steps { bat 'venv\\Scripts\\python src\\export_best.py' }
        }
        stage('Build images') {
            steps {
                bat '''
                docker build -t pm-api:%BUILD_NUMBER% .
                if errorlevel 1 exit /b 1
                docker build -f Dockerfile.ui -t pm-ui:%BUILD_NUMBER% .
                if errorlevel 1 exit /b 1
                '''
            }
        }
        stage('Push to ACR') {
            steps {
                retry(3) {
                    withCredentials([usernamePassword(credentialsId: 'acr-credentials', usernameVariable: 'ACR_USER', passwordVariable: 'ACR_PASS')]) {
                        bat '''
                        echo %ACR_PASS%| docker login %ACR% -u %ACR_USER% --password-stdin
                        if errorlevel 1 exit /b 1

                        docker tag pm-api:%BUILD_NUMBER% %ACR%/pm-api:%BUILD_NUMBER%
                        docker tag pm-api:%BUILD_NUMBER% %ACR%/pm-api:latest
                        docker tag pm-ui:%BUILD_NUMBER% %ACR%/pm-ui:%BUILD_NUMBER%
                        docker tag pm-ui:%BUILD_NUMBER% %ACR%/pm-ui:latest

                        docker push %ACR%/pm-api:%BUILD_NUMBER%
                        if errorlevel 1 exit /b 1
                        docker push %ACR%/pm-api:latest
                        if errorlevel 1 exit /b 1
                        docker push %ACR%/pm-ui:%BUILD_NUMBER%
                        if errorlevel 1 exit /b 1
                        docker push %ACR%/pm-ui:latest
                        if errorlevel 1 exit /b 1

                        docker logout %ACR%
                        '''
                    }
                }
            }
        }
    }
}