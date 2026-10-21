
pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    options {
        disableConcurrentBuilds()
    }

    environment {
        PY = 'C:\\Users\\Mohamed Taheer\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        ACR = 'mldokeimages123=.azurecr.io'
    }

    stages {
        stage('Setup') {
            steps {
                bat '"%PY%" --version && "%PY%" -m venv venv && venv\\Scripts\\python -m pip install -r requirements.txt'
            }
        }

        stage('Train') {
            steps {
                bat 'venv\\Scripts\\python src\\train.py'
            }
        }

        stage('Quality gate') {
            steps {
                bat 'venv\\Scripts\\python src\\gate.py'
            }
        }

        stage('Export model') {
            steps {
                bat 'venv\\Scripts\\python src\\export_best.py'
            }
        }

        stage('Build image') {
            steps {
                bat 'docker build -t pm-api:%BUILD_NUMBER% .'
            }
        }

        stage('Push to ACR') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'acr-credentials',
                        usernameVariable: 'ACR_USER',
                        passwordVariable: 'ACR_PASS'
                    )
                ]) {
                    bat '''
                        echo %ACR_PASS%| docker login %ACR% -u %ACR_USER% --password-stdin
                        if errorlevel 1 exit /b 1

                        docker tag pm-api:%BUILD_NUMBER% %ACR%/pm-api:%BUILD_NUMBER%
                        if errorlevel 1 exit /b 1

                        docker tag pm-api:%BUILD_NUMBER% %ACR%/pm-api:latest
                        if errorlevel 1 exit /b 1

                        docker push %ACR%/pm-api:%BUILD_NUMBER%
                        if errorlevel 1 exit /b 1

                        docker push %ACR%/pm-api:latest
                        if errorlevel 1 exit /b 1

                        docker logout %ACR%
                    '''
                }
            }
        }


      stage('Build and push UI') {
         steps {
          withCredentials([
          usernamePassword(
        credentialsId: 'acr-credentials',
        usernameVariable: 'ACR_USER',
        passwordVariable: 'ACR_PASS'
      )
    ]) {
      bat '''
        echo %ACR_PASS%| docker login %ACR% -u %ACR_USER% --password-stdin
        if errorlevel 1 exit /b 1

        docker build -f Dockerfile.ui -t %ACR%/pm-ui:latest .
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
