# AI and Scientific Research Computing using Kubernetes Tutorial

> GPU and MPI
Hands on session

## GPU's ON Kubernetes

Lets start by running a simple GPU job on Kubernetes. We will use the `nvidia-smi` command to check the GPU's available on the node.

```yaml
apiVersion: v1
kind: Pod
metadata:
  namespace: sc24
  name: pod1
  labels:
    app: pod
spec:
  containers:
  - name: ctr
    image: ubuntu:22.04
    command: ["bash", "-c"]
    args: ["nvidia-smi -L; trap 'exit 0' TERM; sleep 100 & wait"]
    resources:
      limits:
        nvidia.com/gpu: 1
```

Copy the above yaml to a file called `gpu-pod.yaml` and run the following command to create the pod.

```bash
kubectl apply -f gpu-pod.yaml
```

## MPI On Kubernetes

First lets run a basic CPU MPI job on Kubernetes. We will use the MPI operator to run the job.
We will calculate the value of Pi using the Monte Carlo method. The code is written in C and is available in the `mpi-pi` directory.

```yaml
apiVersion: kubeflow.org/v2beta1
kind: MPIJob
metadata:
  name: pi
spec:
  slotsPerWorker: 1
  runPolicy:
    cleanPodPolicy: Running
    ttlSecondsAfterFinished: 60
  sshAuthMountPath: /home/mpiuser/.ssh
  mpiReplicaSpecs:
    Launcher:
      replicas: 1
      template:
        spec:
          containers:
          - image: mpioperator/mpi-pi:openmpi
            name: mpi-launcher
            securityContext:
              runAsUser: 1000
            command:
            - mpirun
            args:
            - -n
            - "2"
            - /home/mpiuser/pi
            resources:
              limits:
                memory: 16Gi
                cpu: 2
              requests:
                memory: 16Gi
                cpu: 2

    Worker:
      replicas: 2
      template:
        spec:
          containers:
          - image: mpioperator/mpi-pi:openmpi
            name: mpi-worker
            securityContext:
              runAsUser: 1000
            command:
            - /usr/sbin/sshd
            args:
            - -De
            - -f
            - /home/mpiuser/.sshd_config
            resources:
              limits:
                cpu: 1
                memory: 1Gi
```

Copy the above yaml to a file called `mpi-pi.yaml` and run the following command to create the job.

```bash
kubectl apply -f mpi-pi.yaml
```

Now let's run a multi-node GPU MPI job on Kubernetes. We will use the MPI operator to run the job.

```yaml
apiVersion: kubeflow.org/v2beta1
kind: MPIJob
metadata:
  name: tensorflow-benchmarks
spec:
  slotsPerWorker: 1
  runPolicy:
    cleanPodPolicy: Running
  mpiReplicaSpecs:
    Launcher:
      replicas: 1
      template:
         spec:
           containers:
           - image: mpioperator/tensorflow-benchmarks:latest
             name: tensorflow-benchmarks
             command:
             - mpirun
             - --allow-run-as-root
             - -np
             - "2"
             - -bind-to
             - none
             - -map-by
             - slot
             - -x
             - NCCL_DEBUG=INFO
             - -x
             - LD_LIBRARY_PATH
             - -x
             - PATH
             - -mca
             - pml
             - ob1
             - -mca
             - btl
             - ^openib
             - python
             - scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py
             - --model=resnet101
             - --batch_size=64
             - --variable_update=horovod
             resources:
               limits:
                 memory: 16Gi
                 cpu: 4
               requests:
                 memory: 16Gi
                 cpu: 4
    Worker:
      replicas: 2
      template:
        spec:
          containers:
          - image: mpioperator/tensorflow-benchmarks:latest
            name: tensorflow-benchmarks
            resources:
              limits:
                nvidia.com/gpu: 1
```

Copy the above yaml to a file called `mpi-tensorflow.yaml` and run the following command to create the job.

```bash
kubectl apply -f mpi-tensorflow.yaml
```

## End

**Please make sure you did not leave any running pods. Jobs and associated completed pods are OK.**

