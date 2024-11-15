# PEARC24 Kubernetes Tutorial

AI Examples\
Hands on session

## AI training using PyTorch example

You can use the yaml files from the repo as is but please change the username to something unique as we are all sharing the same namespace. Please download the yaml files using the download raw file button 
<img src="https://github.com/user-attachments/assets/4033a577-e8d3-4909-9773-30ab39cafef3" width="256" style="vertical-align:middle"/>
and edit 

We start by running the training example:

```
kubectl apply -f pytorch-training.yaml
```
Check on status:

```
kubectl get pods
```

When the job is in run state you can check the logs for output:

```
kubectl logs gp3-username
```

Once you are done exploring, please delete the pod:

```
kubectl delete -f pytorch-training.yaml
```

## Text generation inference example

Start up the inference pod:

```
kubectl apply -f tgi-inference.yaml
```

Once the pod is running, get interactive access to the pod:

```
kubectl exec -it tgi-username -- /bin/bash
```

Once in the pod, start a python3 interpreter and then run:

```
from huggingface_hub import InferenceClient
client = InferenceClient(model="http://0.0.0.0:80")
for token in client.text_generation("Who made cat videos?", max_new_tokens=24, stream=True): print (token)
```
## RAG example using Ollama

Start up the pod:
```
kubectl apply -f ollama-rag.yaml
```
Watch the logs and make sure you wait till the installs are done and the book is downloaded:

```
kubectl logs ollama-username
```
Once the book is downloaded (you will see wget output in the logs), we can get interactive access to the pod and start up the Ollama server and pull the module we want to use (Mistral):

```
kubectl exec -it ollama-username -- /bin/bash
cd /scratch
nohup ollama serve&
ollama pull mistral
```
We can now download our test script and run it:
```
wget https://raw.githubusercontent.com/mahidhar/pearc24_k8s_tutorial/main/test.py
python3 -i test.py
```
Now we can run the rag within the interactive python interpreter. Do the following one by one (i.e. wait for results before moving to the next one)
```
rag.invoke("What do you feed pigeons ?")
rag.invoke("Do tame pigeons have better plumage ?")
rag.invoke("What affects pigeon plumage ?")
```

## Helm based deployment of LLM as service (H2O) 

This is how it's supposed to work: <https://nrp-llama3.nrp-nautilus.io>

Use `guest`:`guest` or register a new user

Install helm. Details at: <https://github.com/helm/helm#install>. Quickest option mignt be to download and use static binaries from the release page referenced in link above.

We will be using the H20 project (<https://github.com/h2oai>). Clone the H2O repository:

```
git clone https://github.com/h2oai/h2ogpt.git
```

Copy the values file to the h2o directory:

```
cp h2o-values.yaml h2ogpt
cd h2ogpt
```
Install the helm chart. Make sure you use a unique name (change username below):

```
helm install h2ogpt-username helm/h2ogpt-chart -f h2o-values.yaml
```

Check the pods (kubectl get pods, maybe grep your username since there will be a lot of pods running) to make sure they are running. Once the pod is running, check the logs and see if h2o is running.

Now you can expose the llm by using an ingress (carefully edit all fields with username):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.class: haproxy
  name: llm-test-username
spec:
  rules:
  - host: llm-test-username.nrp-nautilus.io
    http:
      paths:
      - backend:
          service:
            name: h2ogpt-username-web
            port:
              number: 80
        path: /
        pathType: ImplementationSpecific
  tls:
  - hosts:
    - llm-test-username.nrp-nautilus.io
```

You can open llm-test-username.nrp-nautilus.io (with username replaced) in your browser once the forward works. This will give you the H2O interface for chat, ingesting docs etc. Once you are done you can release the resources by doing:

```
helm uninstall h2ogpt-username
```

## End

**Please make sure you did not leave any running pods. Jobs and associated completed pods are OK.**

