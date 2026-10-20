FROM jenkins/jenkins:lts
USER root
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip docker.io curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*