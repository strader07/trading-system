FROM jupyter/scipy-notebook:6d42503c684f

USER root
RUN DEBIAN_FRONTEND=noninteractive && apt update && apt install -y openssh-client curl less iputils-ping htop

USER $NB_UID

ARG GCLOUD_PROJECT=strange-metrics-258802
ENV GCLOUD_PROJECT=$GCLOUD_PROJECT

ENV MLFLOW_TRACKING_URI=https://mlflow-api.muwazana.com
ENV MLFLOW_TRACKING_USERNAME=mlflow-api
ENV MLFLOW_TRACKING_PASSWORD=Klr9Is92HpvQ

RUN pip install ipython google-cloud-bigquery google-cloud-storage hmmlearn hyperopt dtale jupyter_contrib_nbextensions mlflow \
    && pip install --extra-index-url https://muwazana-user:fe8PXTWEEg4H3DcZ7sVHfq@nexus.tools.muwazana.com/repository/muwazana-pypi/simple mwzpyutil==1.5.5 paf==1.4.8 mktdata==1.0.0
