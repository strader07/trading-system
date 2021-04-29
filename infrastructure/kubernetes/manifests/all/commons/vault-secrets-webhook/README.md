# Vault Secrets webhook

## Using External Vault Instances

You will need to add the following annotations to the resources that you wish to mutate:

```
vault.security.banzaicloud.io/vault-addr: https://[URL FOR VAULT]
vault.security.banzaicloud.io/vault-path: [Auth path]
vault.security.banzaicloud.io/vault-role: [Auth role]
vault.security.banzaicloud.io/vault-skip-verify: "true" # Container is missing Trusted Mozilla roots too.
```

Be mindful about how you reference Vault secrets itself. For KV v2 secrets, you will need to add the /data/ to the path of the secret.

```
PS C:\> vault kv get kv/rax/test
====== Metadata ======
Key              Value
---              -----
created_time     2019-09-21T16:55:26.479739656Z
deletion_time    n/a
destroyed        false
version          1

=========== Data ===========
Key                    Value
---                    -----
MYSQL_PASSWORD         3xtr3ms3cr3t
MYSQL_ROOT_PASSWORD    s3cr3t
```

The secret shown above is referenced like this:

```
vault:[ENGINE]/data/[SECRET_NAME]#KEY
vault:kv/rax/data/test#MYSQL_PASSWORD
```

If you want to use a specific key version, you can append it after the key so it becomes like this:

`vault:kv/rax/data/test#MYSQL_PASSWORD#1`

Omitting the version will tell Vault to pull the latest version.

Also, you will need to create the following RBAC policy to handle the Vault Auth tokens.

```
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: vault-tokenreview-binding
  namespace: vswh # Change it if you don't use the defaults when you install it via Helm
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
- kind: ServiceAccount
  name: vswh-vault-secrets-webhook # Change it if you don't use the defaults when you install it via Helm
  namespace: vswh # Change it if you don't use the defaults when you install it via Helm
```

## Before you start

Before you install this chart you must create a namespace for it, this is due to the order in which the resources in the charts are applied.

```bash
kubectl create ns vault
```

## Installing the Chart

```bash
helm repo add banzaicloud-stable http://kubernetes-charts.banzaicloud.com/branch/master
helm repo update
```

```bash
helm upgrade --namespace vault -i vault-secrets-webhook banzaicloud-stable/vault-secrets-webhook --wait
```

When the command above finis you need to apply the `rbac.yaml`

```bash
kubectl apply -f rbac.yaml
```