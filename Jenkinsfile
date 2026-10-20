pipeline {
  agent any
  triggers { pollSCM('H/5 * * * *') }
  options { disableConcurrentBuilds() }
  environment {
    // Adjust if Python is installed elsewhere; delete this line if python is already on the service's PATH
    PATH = "C:\\Program Files\\Python311;C:\\Program Files\\Python311\\Scripts;${env.PATH}"
  }
  stages {
    stage('Setup') {
      steps { bat 'python --version && python -m venv venv && venv\\Scripts\\python -m pip install -r requirements.txt' }
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
    stage('Build image') {
      steps { bat 'docker build -t pm-api:%BUILD_NUMBER% .' }
    }
  }
}