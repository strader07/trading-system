# How to install Argo

## 1. Download the Argo CLI

Download the latest Argo CLI from our [releases page](https://github.com/argoproj/argo/releases).

## 2. Install the Controller

```sh
kubectl create namespace argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo/stable/manifests/install.yaml
```

Examples below will assume you've installed argo in the `argo` namespace. If you have not, adjust
the commands accordingly.

NOTE: On GKE, you may need to grant your account the ability to create new `clusterrole`s

```sh
kubectl create clusterrolebinding YOURNAME-cluster-admin-binding --clusterrole=cluster-admin --user=YOUREMAIL@gmail.com
```

## 3. Configure the service account to run Workflows

### Roles, RoleBindings, and ServiceAccounts

In order for Argo to support features such as artifacts, outputs, access to secrets, etc. it needs to communicate with Kubernetes resources
using the Kubernetes API. To communicate with the Kubernetes API, Argo uses a `ServiceAccount` to authenticate itself to the Kubernetes API.
You can specify which `Role` (i.e. which permissions) the `ServiceAccount` that Argo uses by binding a `Role` to a `ServiceAccount` using a `RoleBinding`

Then, when submitting Workflows you can specify which `ServiceAccount` Argo uses using:

```sh
argo submit --serviceaccount argo
```

When no `ServiceAccount` is provided, Argo will use the `default` `ServiceAccount` from the namespace from which it is run, which will almost always have insufficient privileges by default.

For more information about granting Argo the necessary permissions for your use case see [Workflow RBAC](workflow-rbac.md).

### Granting admin privileges

We will grant the `default` `ServiceAccount` in argo namespace admin privileges (i.e., we will bind the `admin` `Role` to the `default` `ServiceAccount` of the argo namespace):

```sh
kubectl create rolebinding default-admin --namespace=argo --clusterrole=admin --serviceaccount=argo:default
```

**Note that this will grant admin privileges to the `default` `ServiceAccount` in the development namespace that the command is run from, so you will only be able to
run Workflows in the namespace where the `RoleBinding` was made.**

## 4. Run Sample Workflows
```sh
argo submit --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/hello-world.yaml
argo submit --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/coinflip.yaml
argo submit --watch https://raw.githubusercontent.com/argoproj/argo/master/examples/loops-maps.yaml
argo list
argo get xxx-workflow-name-xxx
argo logs xxx-pod-name-xxx #from get command above
```

Additional examples and more information about the CLI are available on the [Argo Workflows by Example](../examples/README.md) page.

You can also create Workflows directly with `kubectl`. However, the Argo CLI offers extra features
that `kubectl` does not, such as YAML validation, workflow visualization, parameter passing, retries
and resubmits, suspend and resume, and more.
```sh
kubectl create -f https://raw.githubusercontent.com/argoproj/argo/master/examples/hello-world.yaml
kubectl get wf
kubectl get wf hello-world-xxx
kubectl get po --selector=workflows.argoproj.io/workflow=hello-world-xxx --show-all
kubectl logs hello-world-yyy -c main
```


## 5. Install an Artifact Repository

Verify you have a bucket in Google Cloud Storage, we will use it in the next section.

## 6. Reconfigure the workflow controller to use the Minio artifact repository

Edit the `workflow-controller` `ConfigMap`:
```sh
kubectl edit cm -n argo workflow-controller-configmap
```
Add the following:
```yaml
data:
  config: |
    artifactRepository: |
      archiveLogs: true
      gcs:
        bucket: muzna-argo
        key: /
        # serviceAccountKeySecret is a secret selector.
        # It references the k8s secret named 'argo-secrets'.
        # This secret is expected to have have the key 'serviceAccountKey',
        # containing the base64 encoded credentials
        # to the bucket.
        serviceAccountKeySecret:
          name: argo-secrets
          key: serviceAccountKey
```

## 7. Run a workflow which uses artifacts
```sh
argo submit https://raw.githubusercontent.com/argoproj/argo/master/examples/artifact-passing.yaml
```

## 8. Access the Argo UI

Install the ingress in this folder:

```
kubectl apply -f ingress.yaml
```

UI should be accessible at [https://argo.muwazana.com](https://argo.muwazana.com)