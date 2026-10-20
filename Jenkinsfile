pipeline {
  agent any
  triggers { pollSCM('H/5 * * * *') }
  stages {
    stage('Setup') {
      steps { sh 'python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt' }
    }
    stage('Train') {
      steps { sh '. venv/bin/activate && python src/train.py' }
    }
    stage('Quality gate') {
      steps { sh '. venv/bin/activate && python src/gate.py' }
    }
    stage('Export model') {
      steps { sh '. venv/bin/activate && python src/export_best.py' }
    }
    stage('Build image') {
      steps { sh 'docker build -t pm-api:${BUILD_NUMBER} .' }
    }
  }
}