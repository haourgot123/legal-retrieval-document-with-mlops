# legal-retrieval-document-with-mlops



## System Architechture
![Alt text](imgs/MLOPS.drawio.png)



## Qdrant Helms Setup

- k create ns database
- kubens database
- helm repo add qdrant https://qdrant.github.io/qdrant-helm
- helm repo update
- helm install qdrant qdrant/qdrant
- helm upgrade -i qdrant qdrant/qdrant
