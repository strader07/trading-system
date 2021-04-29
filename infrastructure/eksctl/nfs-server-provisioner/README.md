# NFS Server Provisioner

[NFS Server Provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs)
is an out-of-tree dynamic provisioner for Kubernetes. You can use it to quickly
& easily deploy shared storage that works almost anywhere.

## Introduction

This chart bootstraps a [nfs-server-provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs)
deployment on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh)
package manager.

## Installing the Chart

To install the chart with the release name `trader-nfs`:

```console
$ helm upgrade -i -f values.yaml trader-nfs stable/nfs-server-provisioner
```

The command deploys nfs-server-provisioner on the Kubernetes cluster in the default
configuration. The [configuration](#configuration) section lists the parameters
that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `trader-nfs` deployment:

```console
$ helm delete trader-nfs
```

The command removes all the Kubernetes components associated with the chart and
deletes the release.

## Persistence

The nfs-server-provisioner image stores it's configuration data, and importantly, **the dynamic volumes it
manages** `/export` path of the container.

The chart mounts a [Persistent Volume](http://kubernetes.io/docs/user-guide/persistent-volumes/)
volume at this location. The volume can be created using dynamic volume
provisioning. However, **it is highly recommended** to explicitly specify
a storageclass to use rather than accept the clusters default, or pre-create
a volume for each replica.

If this chart is deployed with more than 1 replica, `storageClass.defaultClass=true`
and `persistence.storageClass`, then the 2nd+ replica will end up using the 1st
replica to provision storage - which is likely never a desired outcome.
