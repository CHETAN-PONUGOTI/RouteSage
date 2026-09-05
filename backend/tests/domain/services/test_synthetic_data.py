from app.domain.services.synthetic_data import SyntheticDataGenerator


def test_reproducibility():
    gen1 = SyntheticDataGenerator(seed=123)
    shipments1, routes1 = gen1.generate_dataset()

    gen2 = SyntheticDataGenerator(seed=123)
    shipments2, routes2 = gen2.generate_dataset()

    assert len(shipments1) == len(shipments2)
    assert len(routes1) == len(routes2)

    # Check shipments are identical
    for s1, s2 in zip(shipments1, shipments2):
        assert s1.id == s2.id
        assert s1.origin == s2.origin
        assert s1.weight == s2.weight

    # Check routes are identical
    for r1, r2 in zip(routes1, routes2):
        assert r1.id == r2.id
        assert r1.total_cost == r2.total_cost
        assert r1.transit_time == r2.transit_time


def test_tradeoffs():
    gen = SyntheticDataGenerator(seed=42)
    shipments, routes = gen.generate_dataset()

    # Let's find alternatives for the first shipment
    s1_routes = [r for r in routes if r.shipment_id == shipments[0].id]

    assert len(s1_routes) == 4

    # Profiles are:
    # 0: Balanced
    # 1: Economy
    # 2: Express
    # 3: High-Risk Low-Cost

    r_balanced = s1_routes[0]
    r_economy = s1_routes[1]
    r_express = s1_routes[2]
    r_high_risk = s1_routes[3]

    # General expectations based on generation logic
    assert r_express.transit_time < r_economy.transit_time
    assert r_economy.total_cost < r_express.total_cost
    assert r_express.reliability > r_economy.reliability

    assert r_high_risk.aggregate_risk > r_balanced.aggregate_risk
    assert r_high_risk.delay_probability > r_express.delay_probability
