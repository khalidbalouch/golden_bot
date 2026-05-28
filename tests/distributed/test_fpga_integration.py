import pytest
from ml.hft.fpga_interface import FPGAInterface

def test_fpga_init():
    # Should not crash even if /dev/uio0 doesn't exist
    fpga = FPGAInterface(device_path="/tmp/fake_fpga")
    telemetry = fpga.read_telemetry()
    assert "latency_ns" in telemetry
