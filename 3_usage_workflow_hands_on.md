# AI and Scientific Research Computing with Kubernetes Tutorial

Typical usage workflow\
Hands on session

## Use an existing application container to run jobs

Lets use an existing LAMMPS (a molecular dynamics code) container from dockerhub. 

###### lammps.yaml:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: lammps-<username>
spec:
  template:
    spec:
      volumes:
          - name: scratch
            emptyDir: {}
      containers:
      - name: test
        image: lammps/lammps:patch_7Jan2022_rockylinux8_openmpi_py3
        command: ["/bin/bash", "-c"]
        args:
        - >-
            cd /scratch;
            curl -O https://www.lammps.org/bench/inputs/in.lj.txt ;
            export OMP_NUM_THREADS=1;
            lmp_serial < in.lj.txt ;
            mpirun --oversubscribe -np 4 lmp_mpi < in.lj.txt;
        volumeMounts:
            - name: scratch
              mountPath: /scratch
        resources:
          limits:
            memory: 16Gi
            cpu: "4"
            ephemeral-storage: 10Gi
          requests:
            memory: 16Gi
            cpu: "4"
            ephemeral-storage: 10Gi
      restartPolicy: Never
```
Lets run this simple application test:

```
kubectl apply -f lammps.yaml
```
Now lets check the output:
```
kubectl logs lammps-mahidhar-cj25r
```

Delete the job once we have checked output:
```
kubectl delete -f lammps.yaml
```

## Simple config files

Let's start with creating a simple test file and import it into a pod.

Create a local file named `hello.txt` with any content you like.

Let's now import this file into a configmap (replace username, as before):
```
kubectl create configmap config1-<username> --from-file=hello.txt
```

Can you see it?
```
kubectl get configmap
```

You can also look at its content with
```
kubectl get configmap -o yaml config1-<username>
```

Import that file into a pod:

###### c1.yaml:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: c1-<username>
spec:
  containers:
  - name: mypod
    image: rockylinux:8
    resources:
      limits:
        memory: 100Mi
        cpu: 100m
      requests:
        memory: 100Mi
        cpu: 100m
    command: ["sh", "-c", "sleep 1000"]
    volumeMounts:
    - name: hello
      mountPath: /tmp/hello.txt
      subPath: hello.txt
  volumes:
  - name: hello
    configMap:
      name: config1-<username>
      items:
      - key: hello.txt
        path: hello.txt
```

Create the pod and once it has started, login using kubectl exec and check if the file is indeed in the /tmp directory.

Inside the pod, try making some changes to 
```
/tmp/hello.txt
```

Cound you open the file for writing?

Once you are done exploring, delete the pod and the configmap:
```
kubectl delete pod c1-<username>
kubectl delete configmap config1-<username> 
```

## Importing a whole directory

Create an additional local file named `world.txt` with any content you like.

Let's now import this file into a configmap (replace username, as before):
```
kubectl create configmap config2-<username> --from-file=hello.txt --from-file=world.txt
```

Check its content, as before.

Let's now import the whole configmap into a pod:

###### c2.yaml:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: c2-<username>
spec:
  containers:
  - name: mypod
    image: rockylinux:8
    resources:
      limits:
        memory: 100Mi
        cpu: 100m
      requests:
        memory: 100Mi
        cpu: 100m
    command: ["sh", "-c", "sleep 1000"]
    volumeMounts:
    - name: cfg
      mountPath: /tmp/myconfig
  volumes:
  - name: cfg
    configMap:
      name: config2-<username>
```

Create the pod and once it has started, login using kubectl exec and check if the file is indeed in the /tmp/myconfig directory.

Once again, try to modify their content.

Log out, and update the content of either hello.txt or world.txt.

Let's now update the configmap:

```
kubectl create configmap config2-<username> --from-file=hello.txt --from-file=world.txt --dry-run=client -o yaml |kubectl replace -f -
```

Log back into the node, and check the content of the files in /tmp/myconfig.

Wait a minute (or so), and check again. The changes should propagate into the running pod. 

Once you are done exploring, delete the pod and the configmap:
```
kubectl delete pod c2-<username>
kubectl delete configmap config2-<username> 
```

## Download input data; Download, build, and run scientific code

Let's now work through a scientific application workflow. In this example we will: (a) Download the input data from an external source and put it in the ephemeral storage; (b) Download and build the scientific code; and (c) Run the benchmark.

The container we have chosen is a standard gcc container from dockerhub. The application we will use is the Metagenome Annotation workflow component benchmark
from the NERSC-10 Benchmark Suite (https://gitlab.com/NERSC/N10-benchmarks/hmmsearch-benchmark). This benchmark is based on the computation workflow of the Joint Genome Institute's (JGI)'s Integrated Microbial Genomes project (IMG). IMG's scientific objective is to analyze, annotate and distribute microbial genomes and microbiome datasets.

The application hmmsearch is one program within the HMMER biosequence analysis package that uses a profile Hidden Markov Models (HMM) algorithm to perform a search for matches between input sequences and a reference database of sequence profiles. 

Lets start by spinning up a pod with the gcc environment with a sleep of 3600s. 
We will walk through the benchmark steps manually after the pod starts.

###### scienceapp.yaml:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: scienceapp-<username>
spec:
      volumes:
          - name: scratch
            emptyDir: {}
      containers:
      - name: gcc
        image: gcc:latest
        command: ["/bin/bash", "-c"]
        args:
        - >-
            sleep 3600s;
        volumeMounts:
            - name: scratch
              mountPath: /scratch
        resources:
          limits:
            memory: 32Gi
            cpu: "16"
            ephemeral-storage: 10Gi
          requests:
            memory: 32Gi
            cpu: "16"
            ephemeral-storage: 10Gi
      restartPolicy: Never
```

Start the pod after you put in your username in the yaml file:

```
kubectl apply -f scienceapp.yaml
```

Once the pod is running you can interactively access it:

```
kubectl exec -it scienceapp-<username> -- /bin/bash
```

### Start by cloning the repository and download the data 

We change to the local scratch directory and download data. This might take some time as we have ~1.3GB to download.

```
cd /scratch
git clone https://gitlab.com/NERSC/N10-benchmarks/hmmsearch-benchmark.git
cd hmmsearch-benchmark
bash ./scripts/wget_data.sh
```

### Build the application code

Next we can run the build script that will download the source code and build it

```
cd /scratch/hmmsearch-benchmark
bash ./scripts/build.sh
```

### Run the application

Follow the steps below to run the code:

```
export HMM_BENCH=/scratch/hmmsearch-benchmark
export HMM_DATA=$HMM_BENCH/data
export HMM_SEARCH=$HMM_BENCH/hmmer-3.3.2/src/hpc_hmmsearch
export NCPU=16

nohup $HMM_SEARCH --cpu ${NCPU} -o out.txt --noali data/Pfam-A.hmm data/uniprot_sprot.fasta &
```

The code will take some time to run. You can use the "top" command to see how its doing and also look at the out.txt file for output.

You can delete the pod once you have seen the output:
```
kubectl delete -f scienceapp.yaml
```

## Comment on storage

In the examples so far we have used the ephemeral storage on the nodes for storing input data, code, and output from simulations. This gets purged when the pod is deleted. In the afternoon session we will look into persistent storage options using CephFS, S3 etc.
