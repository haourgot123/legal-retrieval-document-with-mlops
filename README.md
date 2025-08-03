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


# Chuẩn bị buildx (chỉ cần 1 lần)
docker buildx create --use
docker run --privileged --rm tonistiigi/binfmt --install all   # bật QEMU giả lập (nếu cần)

# Build & push multi-arch
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t haourgot123/legal_chatbot_retrieval:v5 \
  --push .
