## Add the Drone Helm Chart repo

In order to be able to use the charts in this repository, add the name and URL to your Helm client:

```console
helm repo add drone https://charts.drone.io
helm repo update
```

# Drone Server
----------------------

## Install

```console
helm upgrade drone drone/drone --install --namespace drone --values server-values.yaml
```

## Upgrading

```console
# This pulls the latest version of the drone chart from the repo.
help repo update
helm upgrade drone drone/drone --install --namespace drone --values server-values.yaml
```

## Uninstall

```console
helm delete drone --namespace drone
```

# Drone Runner Kubernetes
----------------------------


## Install

```
helm upgrade drone-runner-kube drone/drone-runner-kube --install --namespace drone --values runner-kube-values.yaml
```

## Upgrading

```console
# This pulls the latest version of the drone chart from the repo.
help repo update
helm upgrade drone-runner-kube drone/drone-runner-kube --install --namespace drone --values runner-kube-values.yaml
```

## Uninstall

```console
helm delete drone-runner-kube --namespace drone
```
