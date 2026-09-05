from enum import Enum


class CargoType(str, Enum):
    GENERAL = "GENERAL"
    PERISHABLE = "PERISHABLE"
    HAZARDOUS = "HAZARDOUS"
    FRAGILE = "FRAGILE"


class ShipmentPriority(str, Enum):
    STANDARD = "STANDARD"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TransportMode(str, Enum):
    SEA = "SEA"
    AIR = "AIR"
    RAIL = "RAIL"
    ROAD = "ROAD"


class FeasibilityStatus(str, Enum):
    PENDING = "PENDING"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"


class RiskCategory(str, Enum):
    CONGESTION = "CONGESTION"
    GEOPOLITICAL = "GEOPOLITICAL"
    WEATHER = "WEATHER"
    OPERATIONAL = "OPERATIONAL"
