# PostgreSQL Database
----------------------

## Install Postgres

### Add Bitnami Helm repo

In order to be able to use the charts in this repository, add the name and URL to your Helm client:

```console
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### Install

```console
kubectl create namespace mlflow
helm upgrade -i --namespace mlflow --values postgres-values.yaml mlflow-postgres bitnami/postgresql
```

# MLflow
----------

### Add Bitnami Helm repo

In order to be able to use the charts in this repository, add the name and URL to your Helm client:

```console
helm repo add larribas https://larribas.me/helm-charts
helm repo update
```

### Install

```console
helm upgrade -i --namespace mlflow --values mlflow-values.yaml mlflow larribas/mlflow
```

### Apply the ingresses

```console
kubectl apply -f ingress.yaml
```
