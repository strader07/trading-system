# eksctl.io

Creating a new cluster

1. duplicate the trader_cluster.yaml
2. Change the settings you want like region, version, etc...
3. Run the following command to create a new cluster

   Before running the command make sure you setup AWS_REGION and AWS_PROFILE or AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

```bash
eksctl create cluster -f trader_cluster.yaml
```

## Patch aws-node deamonset to release unused internal IP's

```bash
kubectl patch daemonset -n kube-system aws-node --patch "$(cat aws-node-patch.yaml)"
```

