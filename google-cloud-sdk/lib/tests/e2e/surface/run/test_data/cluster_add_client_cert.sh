#!/bin/bash

# Run this script after you create a new test cluster, so as to give it the
# right auth data to test out the client certificate auth method with gcloud.
# Before running, be sure to auth the cluster so the kubectl commands below
# can work:
#  gcloud container clusters get-credentials \
#    $CLUSTER_NAME \
#    --region=$CLUSTER_REGION \
#    --project=cloud-sdk-integration-testing
#
# Pass the cluster name as an argument:
#   cluster_add_client_cert.sh $CLUSTER_NAME

set -x
pushd "$(dirname "$0")"
# To generate the robot.csr we've checked in.
# openssl req -config ./csr.cnf -new -key ./test-robot.key -nodes -out robot.csr
kubectl apply -f csr.yaml
sleep 2
kubectl certificate approve robot
KUBECONFIG=robot-kubeconfig-pre.yaml gcloud container clusters get-credentials $1 --zone us-central1-a
# The following is a hack to cons up a kubeconfig manually, but it works.
head -n $(grep -n users: robot-kubeconfig-pre.yaml | cut -d ':' -f 1) robot-kubeconfig-pre.yaml > robot-kubeconfig.yaml
echo "- name: gke_cloud-sdk-integration-testing_us-central1-a_$1" >> robot-kubeconfig.yaml
echo "  user:" >> robot-kubeconfig.yaml
echo "    client-certificate-data: $(kubectl get csr robot -o jsonpath='{.status.certificate}')" >> robot-kubeconfig.yaml
echo "    client-key-data: $(cat ./test-robot.key | base64 -w0)" >> robot-kubeconfig.yaml
rm robot-kubeconfig-pre.yaml
kubectl apply -f auth.yaml
popd
