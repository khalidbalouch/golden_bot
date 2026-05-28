import json, time, pytest
from core.security import AuditLogger, AuditAction

def test_chain_integrity(tmp_path):
    lp=tmp_path/"audit.log"; log=AuditLogger(str(lp), hmac_key="test32chars!!")
    for i in range(5): log.log(AuditAction.SECRET_ACCESS, f"s{i}", "t", "127.0.0.1", "success", f"Test {i}")
    log.flush()
    v, bad=log.verify_chain(); assert v
    # Tamper
    lines=lp.read_text().strip().split("\n"); d=json.loads(lines[2]); d["message"]="TAMPERED"; lines[2]=json.dumps(d)
    lp.write_text("\n".join(lines)+"\n")
    log2=AuditLogger(str(lp), hmac_key="test32chars!!")
    v, bad=log2.verify_chain(); assert not v and bad==2
