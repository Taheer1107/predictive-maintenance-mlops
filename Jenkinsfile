pipeline {
  agent any
  triggers { pollSCM('H/5 * * * *') }
  options { disableConcurrentBuilds() }
  environment {
    PY = 'C:\\Users\\Mohamed Taheer\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
  }
  stages {
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
    stage('Build image') {
      steps { bat 'docker build -t pm-api:%BUILD_NUMBER% .' }
    }
  }
}