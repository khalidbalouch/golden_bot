from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, field_validator, ConfigDict


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class SecretSource(Enum):
    ENV = "env"
    VAULT = "vault"
    FILE = "file"


class AuditAction(Enum):
    SECRET_ACCESS = auto()
    KEY_ROTATION = auto()
    CONFIG_CHANGE = auto()
    LOGIN_ATTEMPT = auto()
    TRADE_EXECUTION = auto()
    SYSTEM_ERROR = auto()


@dataclass
class RotationConfig:
    key_id: str
    current_secret_path: str
    new_secret_path: str
    rotation_interval: timedelta
    grace_period: timedelta = timedelta(hours=1)
    notification_channels: List[str] = field(default_factory=list)
    rollback_on_failure: bool = True


@dataclass
class AuditEntry:
    timestamp: float
    action: AuditAction
    secret_name: Optional[str]
    user: str
    ip_address: str
    status: Literal["success", "failure", "warning"]
    message: str
    previous_hash: str
    entry_hash: str = field(init=False)

    def __post_init__(self):
        payload = f"{self.timestamp}|{self.action.name}|{self.secret_name}|{self.user}|{self.ip_address}|{self.status}|{self.message}|{self.previous_hash}"
        self.entry_hash = hmac.new(
            os.environ.get("GOLDEN_BOT_AUDIT_KEY", "default").encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


# =============================================================================
# SECRET LOADER
# =============================================================================

class SecretLoader:
    API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,64}$")
    API_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9+/=]{44,88}$")

    def __init__(self, audit_logger: "AuditLogger", cache_ttl_seconds: int = 300, validate_format: bool = True):
        self._audit = audit_logger
        self._cache: Dict[str, Tuple[str, float]] = {}
        self._cache_ttl = cache_ttl_seconds
        self._validate = validate_format
        self._fernet = Fernet(os.environ.get("GOLDEN_BOT_ENCRYPTION_KEY", Fernet.generate_key()))

    def load_secret(self, name: str, source: SecretSource = SecretSource.ENV,
                    required_permissions: Optional[List[str]] = None,
                    user: str = "system", ip_address: str = "127.0.0.1") -> str:
        # Check cache first
        cached = self._cache.get(name)
        if cached and time.time() - cached[1] < self._cache_ttl:
            self._audit.log(AuditAction.SECRET_ACCESS, name, user, ip_address, "success", "Cache hit")
            return cached[0]

        # Load from source
        if source == SecretSource.ENV:
            val = os.environ.get(name)
        elif source == SecretSource.VAULT:
            val = self._load_vault(name)
        elif source == SecretSource.FILE:
            val = self._load_file(name)
        else:
            val = None

        if not val:
            self._audit.log(AuditAction.SECRET_ACCESS, name, user, ip_address, "failure", "Not found")
            raise ValueError(f"Secret '{name}' not found")

        # Validate format if enabled
        if self._validate:
            self._validate_fmt(name, val)

        # Cache and return
        self._cache[name] = (val, time.time())
        self._audit.log(AuditAction.SECRET_ACCESS, name, user, ip_address, "success", f"Loaded from {source.value}")
        return val

    def _load_vault(self, n: str) -> Optional[str]:
        vt = os.environ.get("GOLDEN_BOT_VAULT_TYPE", "env")
        if vt == "aws":
            try:
                import boto3
                c = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
                return json.loads(c.get_secret_value(SecretId=f"golden-bot/{n}")["SecretString"]).get("value")
            except Exception:
                return None
        if vt == "hashicorp":
            try:
                import hvac
                cl = hvac.Client(url=os.environ.get("VAULT_ADDR", "http://localhost:8200"),
                                 token=os.environ.get("VAULT_TOKEN"))
                if cl.is_authenticated():
                    return cl.secrets.kv.v2.read_secret_version(
                        path=f"golden-bot/{n}",
                        mount_point=os.environ.get("VAULT_MOUNT", "secret")
                    )["data"]["data"].get("value")
                return None
            except Exception:
                return None
        return os.environ.get(f"VAULT_{n}")

    def _load_file(self, n: str) -> Optional[str]:
        p = Path("secrets") / f"{n}.enc"
        if not p.exists():
            return None
        try:
            return self._fernet.decrypt(p.read_bytes()).decode()
        except Exception:
            return None

    def _validate_fmt(self, n: str, v: str) -> None:
        if "API_KEY" in n.upper() and not self.API_KEY_PATTERN.match(v):
            raise ValueError(f"Invalid API_KEY format for {n}")
        if "API_SECRET" in n.upper() and not self.API_SECRET_PATTERN.match(v):
            raise ValueError(f"Invalid API_SECRET format for {n}")

    def clear_cache(self, name: Optional[str] = None) -> None:
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()


# =============================================================================
# KEY ROTATION MANAGER
# =============================================================================

class KeyRotationManager:
    def __init__(self, loader: SecretLoader, audit: AuditLogger,
                 max_retries: int = 3, base_delay: float = 1.0):
        self._l = loader
        self._a = audit
        self._mr = max_retries
        self._bd = base_delay
        self._active: Dict[str, bool] = {}

    async def rotate_key(self, kid: str, cfg: RotationConfig,
                         user: str = "system", ip: str = "127.0.0.1") -> Tuple[str, str]:
        if self._active.get(kid):
            raise RuntimeError(f"Rotation active for {kid}")
        self._active[kid] = True
        try:
            for i in range(self._mr):
                try:
                    nid = f"{kid}_{int(time.time())}"
                    ns = secrets.token_urlsafe(64)
                    await self._store(cfg.new_secret_path, ns)
                    await self._val(nid, ns)
                    await self._swap(cfg.current_secret_path, cfg.new_secret_path)
                    self._l.clear_cache(cfg.current_secret_path.split("/")[-1])
                    self._a.log(AuditAction.KEY_ROTATION, kid, user, ip, "success", f"Rotated {kid}->{nid}")
                    await self._dep(cfg.current_secret_path, cfg.grace_period)
                    return nid, ns
                except Exception as e:
                    if i == self._mr - 1:
                        if cfg.rollback_on_failure:
                            await self._rb(cfg)
                        self._a.log(AuditAction.KEY_ROTATION, kid, user, ip, "failure", str(e))
                        raise RuntimeError(f"Rotation failed: {e}")
                    await asyncio.sleep(self._bd * (2 ** i))
        finally:
            self._active.pop(kid, None)

    async def _store(self, p: str, v: str) -> None:
        if os.environ.get("GOLDEN_BOT_VAULT_TYPE", "env") == "file":
            fp = Path("secrets") / f"{Path(p).name}.enc"
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(self._l._fernet.encrypt(v.encode()))
            fp.chmod(0o600)

    async def _val(self, *a, **k):
        await asyncio.sleep(0.1)

    async def _swap(self, *a, **k):
        pass

    async def _dep(self, *a, **k):
        pass

    async def _rb(self, *a, **k):
        pass


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AuditLogger:
    def __init__(self, log_path: Union[str, Path] = "logs/audit.log",
                 hmac_key: Optional[str] = None, flush_interval: int = 10):
        self._lp = Path(log_path)
        self._lp.parent.mkdir(parents=True, exist_ok=True)
        self._hk = (hmac_key or os.environ.get("GOLDEN_BOT_AUDIT_KEY") or "default").encode()
        self._buf: List[AuditEntry] = []
        self._fi = flush_interval
        self._lf = time.time()
        self._ch = self._read_head()

    def log(self, act: AuditAction, sn: Optional[str], u: str, ip: str,
            st: str, msg: str) -> None:
        e = AuditEntry(time.time(), act, sn, u, ip, st, msg, self._ch or "GENESIS")
        self._buf.append(e)
        self._ch = e.entry_hash
        if len(self._buf) >= 100 or time.time() - self._lf > self._fi:
            self.flush()

    def flush(self) -> None:
        if not self._buf:
            return
        with open(self._lp, "a") as f:
            for e in self._buf:
                f.write(json.dumps(e.__dict__) + "\n")
        self._buf.clear()
        self._lf = time.time()

    def verify_chain(self, start: Optional[int] = None) -> Tuple[bool, Optional[int]]:
        entries = self._read_all()
        if not entries:
            return True, None
        exp = "GENESIS" if (start or 0) == 0 else entries[start - 1].entry_hash
        for i, e in enumerate(entries[start or 0:], start=start or 0):
            p = f"{e.timestamp}|{e.action.name}|{e.secret_name}|{e.user}|{e.ip_address}|{e.status}|{e.message}|{e.previous_hash}"
            if hmac.new(self._hk, p.encode(), hashlib.sha256).hexdigest() != e.entry_hash:
                return False, i
            if e.previous_hash != exp:
                return False, i
            exp = e.entry_hash
        return True, None

    def export_compliance(self, st: Optional[float] = None, et: Optional[float] = None,
                          fmt: Literal["json", "csv"] = "json") -> bytes:
        entries = [e for e in self._read_all() if (not st or e.timestamp >= st) and (not et or e.timestamp <= et)]
        if fmt == "json":
            return json.dumps({
                "bot": "Golden Bot",
                "ts": time.time(),
                "head": self._ch,
                "entries": [e.__dict__ for e in entries],
                "proof": self._proof(entries)
            }, indent=2).encode()
        else:
            import csv, io
            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["ts", "act", "secret", "user", "ip", "status", "msg", "hash"])
            for e in entries:
                w.writerow([
                    datetime.fromtimestamp(e.timestamp).isoformat(),
                    e.action.name,
                    e.secret_name or "",
                    e.user,
                    e.ip_address,
                    e.status,
                    e.message,
                    e.entry_hash
                ])
            return out.getvalue().encode()

    def _read_head(self) -> Optional[str]:
        if not self._lp.exists():
            return None
        with open(self._lp, "rb") as f:
            f.seek(0, 2)
            sz = f.tell()
            buf = 8192
            while sz > 0:
                rd = min(buf, sz)
                f.seek(sz - rd)
                lines = f.read(rd).decode().split("\n")
                if len(lines) > 1 and lines[-2].strip():
                    try:
                        return json.loads(lines[-2])["entry_hash"]
                    except Exception:
                        pass
                sz -= rd
        return None

    def _read_all(self) -> List[AuditEntry]:
        res = []
        if not self._lp.exists():
            return res
        with open(self._lp) as f:
            for l in f:
                if l.strip():
                    try:
                        d = json.loads(l)
                        res.append(AuditEntry(
                            d["timestamp"], AuditAction[d["action"]], d.get("secret_name"),
                            d["user"], d["ip_address"], d["status"], d["message"],
                            d["previous_hash"], d["entry_hash"]
                        ))
                    except Exception:
                        pass
        return res

    def _proof(self, entries: List[AuditEntry]) -> str:
        if not entries:
            return hmac.new(self._hk, b"EMPTY", hashlib.sha256).hexdigest()
        h = "EXPORT_GENESIS"
        for e in entries:
            h = hmac.new(self._hk, f"{h}|{e.entry_hash}".encode(), hashlib.sha256).hexdigest()
        return h


# =============================================================================
# IP WHITELIST MANAGER
# =============================================================================

class IPWhitelistManager:
    def __init__(self, wf: Union[str, Path] = "config/ip_whitelist.txt",
                 max_fail: int = 5, block_min: int = 30,
                 geo: Optional[List[str]] = None):
        self._wf = Path(wf)
        self._mf = max_fail
        self._bd = timedelta(minutes=block_min)
        self._geo = geo or []
        self._fails: Dict[str, List[float]] = {}
        self._bl: Dict[str, datetime] = {}
        self._load()

    def _load(self) -> None:
        self._al: List[ipaddress.IPv4Network] = []
        if self._wf.exists():
            for l in self._wf.read_text().splitlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    try:
                        self._al.append(ipaddress.IPv4Network(l, strict=False))
                    except Exception:
                        pass

    def check_access(self, ip: str, ep: str = "api") -> bool:
        if ip in self._bl and datetime.now() < self._bl[ip]:
            return False
        if ip in self._bl:
            del self._bl[ip]
        if self._geo:
            cc = self._geo_lookup(ip)
            if cc and cc not in self._geo:
                self.record_failure(ip)
                return False
        if self._al:
            try:
                if not any(ipaddress.IPv4Address(ip) in n for n in self._al):
                    self.record_failure(ip)
                    return False
            except Exception:
                return False
        return True

    def record_failure(self, ip: str) -> None:
        now = time.time()
        att = self._fails.setdefault(ip, [])
        cutoff = now - self._bd.total_seconds()
        att[:] = [t for t in att if t > cutoff]
        att.append(now)
        if len(att) >= self._mf:
            self._bl[ip] = datetime.now() + self._bd

    def _geo_lookup(self, ip: str) -> Optional[str]:
        return None

    def add(self, cidr: str) -> None:
        n = ipaddress.IPv4Network(cidr, strict=False)
        if n not in self._al:
            self._al.append(n)
            self._persist()

    def _persist(self) -> None:
        self._wf.parent.mkdir(parents=True, exist_ok=True)
        self._wf.write_text(
            f"# Golden Bot IP Whitelist\n# Updated: {datetime.now().isoformat()}\n" +
            "\n".join(str(n) for n in self._al) + "\n"
        )


# =============================================================================
# BOT CONFIG (Pydantic v2 Compatible — ALL REQUIRED FIELDS)
# =============================================================================

class BotConfig(BaseModel):
    # Bot Identity
    bot_name: str = Field(default="Golden Bot", pattern=r"^[A-Za-z0-9\s_-]{3,50}$")
    bot_id: str = Field(default_factory=lambda: f"gb_{secrets.token_hex(8)}")
    env: Literal["testnet", "live"] = "testnet"
    market: Literal["futures", "spot"] = "futures"
    dry_run: bool = True

    # Exchange Connection
    exchange: str = "binance"
    api_key_secret: str = "BINANCE_API_KEY"
    api_secret_secret: str = "BINANCE_API_SECRET"
    rate_limit_per_second: float = Field(default=10.0, ge=0.1, le=100.0)

    # Risk Management
    max_loss_usd: float = Field(default=100.0, gt=0)
    max_loss_per_trade_usd: float = Field(default=10.0, gt=0)
    risk_per_trade_pct: float = Field(default=1.0, ge=0.1, le=10.0)
    max_parallel_trades: int = Field(default=3, ge=1, le=20)
    leverage: int = Field(default=5, ge=1, le=125)

    # Trading Parameters
    default_timeframe: str = "15m"
    watchlist: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    score_gate: float = Field(default=45.0, ge=0, le=100)  # ✅ ADDED: ML signal threshold
    use_ml: bool = False  # ✅ ADDED: Enable ML signals

    # Web Dashboard
    web_port: int = Field(default=8080, ge=1024, le=65535)
    web_token: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    dashboard_theme: str = "dark_blue"  # ✅ ADDED: Dashboard theme

    # Security & Audit
    audit_log_path: str = "logs/audit.log"
    secret_source: Literal["env", "vault", "file"] = "env"
    ip_whitelist_enabled: bool = False

    # Pydantic v2 config
    model_config = ConfigDict(validate_assignment=True, extra="allow")  # ✅ Allow extra fields from .env

    # Validators
    @field_validator("watchlist")
    @classmethod
    def validate_symbols(cls, v):
        for s in v:
            if not re.match(r"^[A-Z]+USDT$", s):
                raise ValueError(f"Invalid symbol: {s}")
        return v

    @field_validator("score_gate")
    @classmethod
    def validate_score_gate(cls, v):
        return max(0.0, min(100.0, v))