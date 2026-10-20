pipeline {
  agent any
  triggers { pollSCM('H/5 * * * *') }
  stages {
    stage('Setup') {
      steps { bat 'python -m venv venv && venv\\Scripts\\pip install -r requirements.txt' }
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