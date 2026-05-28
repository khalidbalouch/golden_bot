import pytest
from ml.mm.avellaneda_stoikov import AvellanedaStoikov
from ml.mm.inventory_manager import InventoryManager
from ml.mm.spread_optimizer import SpreadOptimizer

def test_avellaneda_stoikov():
    model = AvellanedaStoikov(risk_aversion=0.1, inventory_penalty=0.5)
    # Long inventory should lower reservation price
    r_long = model.calculate_reservation_price(100.0, 1.0, 0.02, 1.0)
    assert r_long < 100.0

    # Short inventory should raise reservation price
    r_short = model.calculate_reservation_price(100.0, -1.0, 0.02, 1.0)
    assert r_short > 100.0

def test_inventory_manager():
    inv = InventoryManager(max_inventory=10.0)
    inv.update_inventory("BTC", 5.0)
    assert inv.get_inventory("BTC") == 5.0
    assert inv.check_limit("BTC", 4.0) == True
    assert inv.check_limit("BTC", 6.0) == False # Exceeds 10

def test_spread_optimizer():
    opt = SpreadOptimizer(base_spread_bps=10.0)
    # High vol should increase spread
    s1 = opt.calculate_adaptive_spread(0.01, 0.0)
    s2 = opt.calculate_adaptive_spread(0.05, 0.0)
    assert s2 > s1

    # Rebate should decrease spread
    s_rebate = opt.calculate_adaptive_spread(0.01, 0.0002)
    assert s_rebate < s1
