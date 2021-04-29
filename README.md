## How to connect local python app to redis on dev
1. brew cask install google-cloud-sdk (apt install google-cloud-sdk)
2. brew install kubernetes-cli (apt install kubernetes-cli)
3. gcloud container clusters get-credentials muzna-bo-aio-01 --zone europe-west2-c --project strange-metrics-258802
4. kubectl config rename-context gke_strange-metrics-258802_europe-west2-c_muzna-bo-aio-01 muzna-aio
5. kubectl --context muzna-aio --namespace development port-forward svc/redis 6379:6379
6. make run service <service-name> (i.e: `make run service python-service`)

### Some prerequisites are needed for number 6  to work
1. The Microservice must be located under services  directory
2. main.py is the located at the root of the microservice directory and has the main function
3. requirements.txt is the located at the root of the microservice directory
4. Dockerfile is the located at the root of the microservice directory
5. k8s is the located at the root of the microservice directory

## To connect to redis dev on localhost:6379:
```
kubectl --context muzna-aio --namespace development port-forward svc/redis 6379:6379
kubectl --context muzna-aio --namespace development port-forward svc/redis-exposed 6380:6379
```

## URLs:
- http://dashboard.dev.muwazana.com/
- http://dashboard.dev.muwazana.com/ws

## Redis
Local: redis:6789 and redis-exposed:6789
External: redis-exposed.ftx.dev.muwazana.com

## Secrets
1.Generate secrets - this is base64 encoded but not encrypted
```bash
kubectl --context muzna-aio --namespace development create secret generic ftx-dropcopy --from-literal=FTXKEY=CYZ -o yaml --dry-run > k8s/base/k8s-sec.yaml
```

2 Apply
```bash
kubectl --context muzna-aio --namespace development apply -f services/ftx-dropcopy/k8s/base/k8s-cm.yaml
kubectl --context muzna-aio --namespace development apply -f k8s/base/k8s-sec.yaml
```

## Sealed secrets
```bash
kubectl -n development create secret generic ftx-dropcopy --dry-run --from-literal=foo=bar -o yaml | kubeseal --context muzna-aio --controller-namespace commons --controller-name sealed-secrets -o yaml > services/ftx-dropcopy/k8s/base/k8s-ssec.yaml
```

Make sure k8s-ssec.yaml is in kustomization.yml.

## Deploy
```
make manual-deploy service ftx-dropcopy development/development
make manual-deploy service ftx-dashboard development/development
make manual-deploy service redis-exposed development/development
make manual-deploy job mktdata-archiver development/development
```

UI:
```
make manual-deploy app ftx-dashboard development/development
```

To generate/view a manifest file (never needed, auto done in manual deploy)
```bash
make gen service ftx-dropcopy development/development
```

## Control scaling
```bash
kubectl --context muzna-aio --namespace development scale --replicas 0 deployment ftx-dropcopy
```

## k9s
Ctrl-A abbreviations
dp deployment (delete here to remove pods)
s shell
l stdout/stderr
p go up
y/enter view secrets
:ctx context
:ns development
:sec secrets

## Rebuild base docker image
```bash
make build docker python
```

Replace python with service or [all] as well.

## Jobs
Build app
```bash
make build image mktdata-archiver
```

To update the app, manually update the `argo-workflow.yaml` file and apply it in k8s.

Run mktdata-archiver cronjob as a job:
```bash
kubectl create job --from=cronjob/mktdata-archiver <job-name>
```

## Tardis Machine
Port forwarding:
```bash
kubectl --context muzna-aio --namespace development port-forward svc/tardis-machine 8000:8000
```

Internal URL: http://tardis-machine:8000


## JupyterLab
See `helm/jupyterlab` and `infrastructure/docker/jupyterlab`

### Update image
1. Update `infrastructure/docker/jupyterlab/Dockerfile`
2. Build image: `docker build -f Dockerfile .`
3. Run: `infrastructure/docker/jupyterlab/update_registry.sh <source image> <version>`
4. Update version in `helm/jupyterlab/config.yaml`
5. Run `helm/jupyterlab/upgrade.sh`

## Helm Client Setup
1. Download helmv2 from https://github.com/helm/helm/releases and copy it as `helm2` into your $PATH.
2. `helm2 init`
3. `helm2 repo update`
4. `helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/`
5. `helm2 repo update`

### Install gcloud CLI in Jupyterhub
```bash
curl -sSL https://sdk.cloud.google.com > /tmp/gcl && bash /tmp/gcl --install-dir=~/gcloud --disable-prompts
./gcloud/google-application-sdk/gcloud auth application-default login
```

## Poetry MWZ Pypi Repo Setup
```bash
poetry config repositories.mwz https://nexus.tools.muwazana.com/repository/muwazana-hosted-pypi/
poetry config http-basic.mwz muwazana-user <PASSWORD>
```

For apps that need to use the repo, set the repo to pyproject.toml repo url:
```toml
[[tool.poetry.source]]
name = "mwz"
url = "https://nexus.tools.muwazana.com/repository/muwazana-pypi/simple"
```
