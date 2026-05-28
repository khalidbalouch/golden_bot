#!/usr/bin/env python3
"""CLI: Scale worker pool replicas via K8s API"""
import argparse
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("scale_workers")

def scale_deployment(deployment_name: str, replicas: int, namespace: str = "default"):
    try:
        config.load_kube_config()
        apps_v1 = client.AppsV1Api()
        body = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=body)
        logger.info(f"✅ Scaled {deployment_name} to {replicas} replicas")
    except ApiException as e:
        logger.error(f"❌ Failed to scale: {e}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="golden-bot-pro")
    p.add_argument("--replicas", type=int, required=True)
    p.add_argument("--namespace", default="default")
    args = p.parse_args()
    scale_deployment(args.name, args.replicas, args.namespace)
