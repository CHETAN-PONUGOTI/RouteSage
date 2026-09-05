from uuid import uuid4

from app.domain.models.enums import FeasibilityStatus, TransportMode
from app.domain.models.route import Route, RouteLeg
from app.domain.optimization.pareto import ParetoAnalyzer


def create_route(
    cost: float,
    time: float,
    rel: float,
    risk: float,
    status: FeasibilityStatus = FeasibilityStatus.FEASIBLE,
) -> Route:
    return Route(
        id=uuid4(),
        shipment_id=uuid4(),
        route_name="Route",
        total_cost=cost,
        transit_time=time,
        delay_probability=1.0 - rel,
        reliability=rel,
        aggregate_risk=risk,
        feasibility_status=status,
        legs=[
            RouteLeg(
                sequence=1,
                origin="A",
                destination="B",
                transport_mode=TransportMode.SEA,
                duration=time,
                cost=cost,
            )
        ],
    )


def test_single_route_pareto():
    analyzer = ParetoAnalyzer()
    r = create_route(1000, 5, 0.9, 0.2)

    efficient, dominated = analyzer.analyze([r])
    assert len(efficient) == 1
    assert len(dominated) == 0
    assert efficient[0] == r


def test_clear_dominance():
    # A dominates B
    a = create_route(1000, 5, 0.9, 0.2)
    b = create_route(1200, 6, 0.8, 0.3)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b])

    assert len(efficient) == 1
    assert len(dominated) == 1
    assert efficient[0] == a
    assert dominated[0] == b


def test_partial_tradeoff():
    # Mutually non-dominated
    a = create_route(1000, 5, 0.9, 0.2)  # Better cost and time
    b = create_route(1200, 6, 0.95, 0.1)  # Better reliability and risk

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b])

    assert len(efficient) == 2
    assert len(dominated) == 0


def test_identical_routes():
    # Identical values -> neither strictly dominates the other, so both are efficient
    a = create_route(1000, 5, 0.9, 0.2)
    b = create_route(1000, 5, 0.9, 0.2)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b])

    assert len(efficient) == 2
    assert len(dominated) == 0


def test_equal_on_some_dimensions():
    # A dominates B because it's strictly better on cost, identical on others
    a = create_route(1000, 5, 0.9, 0.2)
    b = create_route(1200, 5, 0.9, 0.2)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b])

    assert len(efficient) == 1
    assert efficient[0] == a
    assert dominated[0] == b


def test_one_route_dominates_all():
    a = create_route(1000, 5, 0.9, 0.2)
    b = create_route(1200, 5, 0.9, 0.2)
    c = create_route(1000, 6, 0.9, 0.2)
    d = create_route(1000, 5, 0.8, 0.2)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b, c, d])

    assert len(efficient) == 1
    assert efficient[0] == a
    assert len(dominated) == 3
    assert b in dominated
    assert c in dominated
    assert d in dominated


def test_infeasible_excluded():
    a = create_route(1000, 5, 0.9, 0.2)
    b = create_route(500, 2, 0.99, 0.05, status=FeasibilityStatus.INFEASIBLE)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([a, b])

    # b is infeasible, so it doesn't participate. a is the only feasible route.
    assert len(efficient) == 1
    assert efficient[0] == a
    assert len(dominated) == 0


def test_hand_constructed_scenario():
    # A = (1000, 5, 0.90, 0.20)
    # B = (1200, 4, 0.95, 0.15)
    # C = (1500, 7, 0.80, 0.40)

    A = create_route(1000, 5, 0.90, 0.20)
    B = create_route(1200, 4, 0.95, 0.15)
    C = create_route(1500, 7, 0.80, 0.40)

    # A and B are mutually non-dominated (A is cheaper, B is faster/more reliable/less risky)
    # A dominates C (A is cheaper, faster, more reliable, less risky)
    # B dominates C (B is cheaper, faster, more reliable, less risky)

    analyzer = ParetoAnalyzer()
    efficient, dominated = analyzer.analyze([A, B, C])

    assert len(efficient) == 2
    assert A in efficient
    assert B in efficient
    assert len(dominated) == 1
    assert dominated[0] == C
