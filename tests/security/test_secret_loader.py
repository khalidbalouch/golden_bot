import os, pytest, unittest.mock as mock
from core.security import SecretLoader, AuditLogger, SecretSource

@pytest.fixture
def mock_audit(): return mock.MagicMock(spec=AuditLogger)
@pytest.fixture
def loader(mock_audit): return SecretLoader(audit_logger=mock_audit, validate_format=False)

def test_load_env(loader, mock_audit):
    os.environ["TEST_SECRET"]="val123"; assert loader.load_secret("TEST_SECRET", user="t", ip="127.0.0.1")=="val123"
    assert mock_audit.log.call_args[1]["status"]=="success"

def test_missing_raises(loader, mock_audit):
    os.environ.pop("MISSING", None)
    with pytest.raises(ValueError, match="not found"): loader.load_secret("MISSING", user="t", ip="127.0.0.1")
    assert mock_audit.log.call_args[1]["status"]=="failure"
