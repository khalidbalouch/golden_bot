#!/usr/bin/env python3
"""CLI: Manual key rotation utility for Golden Bot"""
import asyncio, argparse, os, sys
sys.path.insert(0, ".")
from core.security import KeyRotationManager, RotationConfig, SecretLoader, AuditLogger, AuditAction
from datetime import timedelta

async def main(key_id: str, action: str):
    audit = AuditLogger(); loader = SecretLoader(audit)
    mgr = KeyRotationManager(loader, audit)
    cfg = RotationConfig(key_id=key_id, current_secret_path=f"secrets/{key_id}_current", new_secret_path=f"secrets/{key_id}_new", rotation_interval=timedelta(days=30))
    if action=="generate":
        print(f"✅ New key pair generated for {key_id} (dry-run)")
    elif action=="swap":
        nid, ns = await mgr.rotate_key(key_id, cfg, user="cli")
        print(f"✅ Swapped {key_id} -> {nid}")
    else: print("Usage: --action [generate|swap]")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--key", required=True); parser.add_argument("--action", choices=["generate","swap"], default="generate")
    args=parser.parse_args(); asyncio.run(main(args.key, args.action))
