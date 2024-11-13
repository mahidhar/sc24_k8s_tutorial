# AI and Scientific Research Computing with Kubernetes Tutorial

Basic Kubernetes\
Hands on session

## Setup

There are several basic step you must take to get access to the cluster.

1. Install the kubectl Kubernetes client.\
   Instructions at <https://kubernetes.io/docs/tasks/tools/install-kubectl/>\
   If you have homebrew installed on mac, use that. Otherwise try downloading the static binary (the curl way)
2. Download the configuration file (config) from this github repo and put it on your laptop in the location `~/.kube/config`. For windows please use the location`%USERPROFILE%\.kube\config`


The config file for this tutorial will have the right namespace pre-set. In general you need to be aware of which namespace you are working in, and either set it with `kubectl config set-context nautilus --namespace=the_namespace` or specify in each `kubectl` command by adding `-n namespace`.

## GUI tools

To easily see the current state of the namespace, you can use one of the GUI tools:

[Lens](https://k8slens.dev/) - Graphical user interface

[K9s](https://k9scli.io/) - console graphical user interface

## Launch a simple pod

Let’s create a simple generic pod, and login into it.

You can copy-and-paste the lines below, but please do replace “username” with your own id.\
All the participants in this hands-on session share the same namespace, so you will get name collisions if you don’t.

###### pod1.yaml:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-<username>
spec:
  containers:
  - name: mypod
    image: busybox:latest
    resources:
      limits:
        memory: 1Gi
        cpu: 1
      requests:
        memory: 100Mi
        cpu: 100m
    command: ["sh", "-c", "sleep 10000"]
```

Reminder, indentation is important in YAML, just like in Python.

*If you don't want to create the file and are using mac or linux, you can create yaml's dynamically like this:*

```bash
kubectl create -f - << EOF
<contents you want to deploy>
EOF
```

Now let’s start the pod:

```bash
kubectl create -f pod1.yaml
```

See if you can find it:

```bash
kubectl get pods
```

Note: You may see the pods from the other participants, too.

If it is not yet in Running state, you can check what is going on with

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Let’s log into it**

```bash
kubectl exec -it pod-<username> -- /bin/sh
```

You are now inside the (container in the) pod!

Does it feel any different than a regular, dedicated node?

Try to run some standard Linux commands. Hello world will do, but feel free to be creative.

**Try to create some directories and some files with content.**

Try different locations, both under /home and in system areas.

Put something memorable inside some of the files. Again, a simple Hello world will do, but feel free to be creative.

**Let's also check the networking.**

You can use ifconfig. Look for the inet address.

```bash
ifconfig -a
```

Get out of the Pod (with either Control-D or exit).

You should see the same IP displayed with kubectl

```bash
kubectl get pod -o wide pod-<username>
```

**We can now destroy the pod**

```bash
kubectl delete -f pod1.yaml
```

Check that it is actually gone:

```bash
kubectl get pods
```

Next, **let’s create it again:**

```bash
kubectl create -f pod1.yaml
```

Did it start on the same node?

```bash
kubectl get pod -o wide pod-<username>
```

Does it have the same IP?

Log back into the pod:

```bash
kubectl exec -it pod-<username> -- /bin/sh
```

What is the status of the files your created?


Feel free to experiment some more, then **delete explicitly the pod.**

```bash
kubectl delete pod pod-<username>
```

## Using the job object

Most science applications need to run in batch mode, without interactive access and with limited runtime.

We could submit Pods that do that, but we often want error handling at the system level, too.

The job object provides the option to restart your pod if it fails for any reason.

You can copy-and-paste the lines below, but please do replace “username” with your own id.

###### job1.yaml:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: job1-<username>
spec:
  completions: 1
  ttlSecondsAfterFinished: 1800
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: mysleeperpod
        image: rockylinux:9
        resources:
           limits:
             memory: 100Mi
             cpu: 0.1
           requests:
             memory: 100Mi
             cpu: 0.1
        command: ["sh", "-c", "date; echo Starting; sleep 30; env; date; echo Done"]
```


Now let’s create the job:

```bash
kubectl create -f job1.yaml
```

Check for the job and the associated pod:

```bash
kubectl get jobs
kubectl get pods 
```

Wait a minute and try again (a few times).

What happened?
(Hint: check the status and restart column)

The pod should have fist go into a Runnning state, followed by a Completed state...

Which means, that it terminated...

Now what?

You may have noticed that we are printing out to standard output. You can retrieve that with:

```bash
kubectl logs job1-<username>-<hash>
```

You could now delete the job. But you don't have to.
It will automatically remove itself after half an hour (1800 seconds).

Let's now create a bad job, one that will always fail:

###### badjob1.yaml:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: badjob1-<username>
spec:
  completions: 1
  ttlSecondsAfterFinished: 1800
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: mysleeperpod
        image: rockylinux:9
        resources:
           limits:
             memory: 100Mi
             cpu: 0.1
           requests:
             memory: 100Mi
             cpu: 0.1
        command: ["sh", "-c", "date; sleep 10; /santa/goes/skiing"]
```

Create the job:

```bash
kubectl create -f badjob1.yaml
```

Check for the job and the associated pod:

```bash
kubectl get jobs
kubectl get pods 
```

Wait a minute and try again (a few times).

What is happening?

Is the pod getting into a Completed staute?

How many time did it start?

When you are done looking at the pod, try to remove it:

```bash
kubectl delete pod badjob1-<username>-<hash>
```

Now check again:

```bash
kubectl get jobs
kubectl get pods 
```

What is happened?

Since our job will keep failing forever, make sure you delete the job when you are done:

```bash
kubectl delete -f badjob1.yaml
```


## Parameter sweep

Running a single application iteration is interesting, but science users often need many executions to get their science done.

So, let's do a simple parameter sweep. I.e. let's execute 10 pods with the same code but different inputs.

As usual, you can copy-and-paste the lines below, but please do replace “username” with your own id.

BTW: You probably noted that you need to provide a unique name for each job you submit.
This is indeed a requirement in Kubernetes.
(You can reuse the same name after you delete an old job, of course)

###### job2.yaml:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: job2-<username>
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
        image: rockylinux:9
        resources:
           limits:
             memory: 100Mi
             cpu: 0.1
           requests:
             memory: 100Mi
             cpu: 0.1
        command: ["sh", "-c", "let s=10+2*$JOB_COMPLETION_INDEX; date; sleep $s; date; echo Done $JOB_COMPLETION_INDEX"]
```

Now let’s create the job:

```bash
kubectl create -f job2.yaml
```

Check for the job and the associated pods:

```bash
kubectl get jobs
kubectl get pods
```

Did it start 10 pods?

Now wait for them to finish, and then look at the stdout with

```bash
kubectl logs job2-<username>-<index>-<hash>
``` 

## The end

**Please make sure you did not leave any running pods. Jobs and associated completed pods are OK.**
