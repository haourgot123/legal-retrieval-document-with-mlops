#!/bin/bash

set -e

NAMESPACE="elk"
RELEASE_NAME="elk-kibana"

echo "Uninstall Helm release: $RELEASE_NAME (if exists)..."
helm uninstall $RELEASE_NAME -n $NAMESPACE || true

echo "Deleting all labeled Kibana resources in namespace $NAMESPACE..."
kubectl delete all,cm,secret,sa,role,rolebinding,job,ingress -n $NAMESPACE -l "app.kubernetes.io/name=kibana" --ignore-not-found

echo "Deleting known Kibana resources by fixed names (in case they have no label)..."
kubectl delete secret elk-kibana-kibana-es-token -n $NAMESPACE --ignore-not-found
kubectl delete configmap elk-kibana-kibana-helm-scripts -n $NAMESPACE --ignore-not-found
kubectl delete job pre-install-elk-kibana-kibana -n $NAMESPACE --ignore-not-found
kubectl delete role pre-install-elk-kibana-kibana -n $NAMESPACE --ignore-not-found
kubectl delete rolebinding pre-install-elk-kibana-kibana -n $NAMESPACE --ignore-not-found
kubectl delete serviceaccount pre-install-elk-kibana-kibana -n $NAMESPACE --ignore-not-found

echo "Done cleaning up all Kibana-related resources in namespace $NAMESPACE."
