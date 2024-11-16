# AI and Scientific Research Computing using Kubernetes Tutorial

Storage\
Hands on session

## Using ephemeral storage

In the past exercises you have seen that you can write in pretty much any part of the filesystem inside a pod.
But the amount of space you have at your disposal is limited. And if you use a significant portion of it, your pod might be terminated if kubernetes needs to reclaim some node space.

If you need access to a larger (and often faster) local area, you should use the so-called ephemeral storage using emptyDir.

Note that you can request either a disk-based or a memory-based partition. We will do both below.

You can copy-and-paste the lines below, but please do replace “username” with your own id;\
As mentioned before, all the participants in this hands-on session share the same namespace, so you will get name collisions if you don’t.

###### s1.yaml:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: s1-<username>
spec:
  containers:
  - name: mypod
    image: rockylinux:8
    resources:
      limits:
        memory: 8Gi
        cpu: 100m
        ephemeral-storage: 10Gi
      requests:
        memory: 4Gi
        cpu: 100m
        ephemeral-storage: 1Gi
    command: ["sh", "-c", "sleep 1000"]
    volumeMounts:
    - name: scratch1
      mountPath: /mnt/myscratch
    - name: ramdisk1
      mountPath: /mytmp
  volumes:
  - name: scratch1
    emptyDir: {}
  - name: ramdisk1
    emptyDir:
      medium: Memory
```

Create the pod and once it has started, log into it using kubectl exec.

Look at the mounted filesystems:

```
df -H / /mnt/myscratch /tmp /mytmp /dev/shm
```

As you can see, / and /tmp are on the same filesystem, but /mnt/myscratch is a completely different filesystem.

You should also notice that /dev/shm is tiny; the real ramdisk is /mytmp.

*Note:* You can mount the ramdisk as /dev/shm (or /tmp). that way your applications will find it where they expect it to be.

Once you are done exploring, please delete the pod.

## Using persistent storage

Everything we have done so far has been temporary in nature.

The moment you delete the pod, everything that was computed is gone.

Most applications will however need access to long term data for either/both input and output.

In the Kubernetes cluster you are using we have a distributed filesystem, which allows using it for real data persistence.

To get storage, we need to create an object called PersistentVolumeClaim.

By doing that we "Claim" some storage space from a "Persistent Volume".

There will actually be PersistentVolume created, but it's a cluster-wide resource which you can not see.

Create the file (replace username as always):

###### pvc.yaml:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vol-<username>
spec:
  storageClassName: rook-cephfs
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
```

We're creating a 1GB volume.

Look at it's status with 

```
kubectl get pvc vol-<username>
```
(replace username). 

The `STATUS` field should be equals to `Bound` - this indicates successful allocation.

Note that it may take a few seconds for the system to get there, so be patient.
You can check the progress with

```
kubectl get events --sort-by=.metadata.creationTimestamp --field-selector involvedObject.name=vol-<username>
```

Now we can attach it to our pod. Create one with (replacing `username`):

###### s3.yaml:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: s3-<username>
spec:
  completionMode: Indexed
  completions: 10
  parallelism: 10
  ttlSecondsAfterFinished: 1800
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: mypod
        image: rockylinux:8
        resources:
           limits:
             memory: 100Mi
             cpu: 0.1
           requests:
             memory: 100Mi
             cpu: 0.1
        command: ["sh", "-c", "let s=2*$JOB_COMPLETION_INDEX; d=`date +%s`; date; sleep $s; (echo Job $JOB_COMPLETION_INDEX; ls -l /mnt/mylogs/)  > /mnt/mylogs/log.$d.$JOB_COMPLETION_INDEX; sleep 1000"]
        volumeMounts:
        - name: mydata
          mountPath: /mnt/mylogs
      volumes:
      - name: mydata
        persistentVolumeClaim:
          claimName: vol-<username>
```

Create the job and once any of the pods has started, log into it using kubectl exec.

Check the content of /mnt/mylogs
```
ls -l /mnt/mylogs
```

Try to create a file in there, with any content you like.

Now, delete the job, and create another one (with the same name).

Once one of the new pods start, log into it using kubectl exec.

What do you see in /mnt/mylogs ?

Once you are done exploring, please delete the pod.

If you have time, try to do the same exercise but using emptyDir. And verify that the logs indeed do not get preserved between pod restarts.

## Using S3 Storage
Some times the high I/O workloads can cause problems with CephFS based PVCs and end up being the bottlenecks on computational workloads. The S3 interface is scalable and universally accessible, so storage with S3 interfaces can be a great place to store large datasets which can be simultaneously accessed either from inside the cluster or externally. 

For this tutorial we have created a publicly accessible S3 storage bucket with the CIFAR-10 dataset already loaded. The first example will download the dataset from S3 to node local ephemeral storage and use it for a AI training case. 

Change the username in the pod-awscli.yaml file, and launch the pod by running:
```
kubectl apply -f pod-awscli.yaml
```

Check the logs to verify all the package installs are done (we install boto3 and torch packages for the test and echo a statement when they are done):
```
kubectl logs pod-username
```

Interactively access the running pod
```
kubectl exec -it pod-username -- /bin/bash
```

Change to the scratch directory and run the python script that lists the data in the S3 bucket and then downloads the CIFAR-10 dataset. Extract the dataset into the data directory

```
cd /scratch
wget https://raw.githubusercontent.com/mahidhar/sc24_k8s_tutorial/refs/heads/main/list-download-s3.py
python3 list-download-s3.py
```

Extract the dataset and run the benchmark
``` 
mkdir data
cd data
tar -xf ../cifar-10-python.tar.gz
cd ../
wget https://raw.githubusercontent.com/mahidhar/sc24_k8s_tutorial/refs/heads/main/run-training.py
python3 run-training.py
```

### S3 Connector From Amazon 
Amazon Labs has an S3 connector for PyTorch which allows from directly streaming data from S3 buckets. Using the S3 Connector for PyTorch automatically optimizes performance when downloading training data from and writing checkpoints to Amazon S3, eliminating the need to write your own code to list S3 buckets and manage concurrent requests. Details on the github site:

https://github.com/awslabs/s3-connector-for-pytorch

with examples at:

https://github.com/awslabs/s3-connector-for-pytorch/blob/main/examples/Getting%20started%20with%20the%20Amazon%20S3%20Connector%20for%20PyTorch.ipynb

## Explicitly moving files in

Most science users have large input data.
If someone has not already pre-loaded them on a PVC, you will have to fetch them yourself.

You can use any tool you are used to, f.e. curl, scp or rclone. You can either pre-load it to a PVC or fetch the data just-in-time, whatever you feel is more appropriate.

We do not have an explicit hands-on tutorial, but feel free to try out your favorite tool using what you have learned so far.

## Handling output data

Unlinke most batch systems, there is no shared filesystem between the submit host (aka your laptop) and the execution nodes.

You are responsible for explicit movement of the output files to a location that is useful for you.

The easiest option is to keep the output files on a persistent PVC and do the follow-up analysis inside the kuberenetes cluster.

But when you want any data to be exported outside of the kubernetes cluster, you will have to do it explicitly.
You can use any (authenticated) file transfer tool from ssh to globus. Just remember to inject the necessary creatials into to pod, ideally using a secret.

For *small files*, you can also use the `kubectl cp` command.
It is similar to `scp`, but routes all traffic through a central kubernetes server, making it very slow.
Good enough for testing and debugging, but not much else. 

Again, we do not have an explict hands-on tutorial, and we discourage the uploading of any sensitive credentials to this shared kubernetes setup.


## End

**Please make sure you did not leave any running pods. Jobs and associated completed pods are OK.**

