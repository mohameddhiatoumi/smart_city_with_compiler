"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Sensor models
class SensorBase(BaseModel):
    capteur_id: str
    zone_id: int
    type_capteur: str
    statut: str
    taux_erreur: Optional[float] = None  # ← ADD THIS
    nb_anomalies_totales: Optional[int] = None 

class SensorDetail(SensorBase):
    date_installation: Optional[datetime]
    derniere_maintenance: Optional[datetime]
    taux_erreur: float
    nb_anomalies_totales: int
    seuil_alerte: float

class MeasurementBase(BaseModel):
    mesure_id: int
    capteur_id: str
    timestamp: datetime
    type_mesure: str
    valeur: float
    unite: str
    est_anomalie: bool


# Zone models
class ZoneBase(BaseModel):
    zone_id: int
    nom: str
    description: Optional[str]

class ZonePollution(BaseModel):
    zone_id: int
    zone_nom: str
    avg_pm25: Optional[float]
    avg_pm10: Optional[float]
    avg_co2: Optional[float]
    avg_no2: Optional[float]
    measurement_count: int


# Citizen models
class CitizenBase(BaseModel):
    citoyen_id: int
    nom: str
    email: Optional[str]
    zone_id: int
    score_ecologique: int
    date_inscription: datetime


# Vehicle models
class VehicleBase(BaseModel):
    vehicule_id: str
    citoyen_id: Optional[int]
    type_vehicule: str
    statut: str
    zone_actuelle_id: Optional[int]


# Intervention models
class InterventionBase(BaseModel):
    intervention_id: int
    capteur_id: str
    statut: str
    date_demande: datetime
    date_terminaison: Optional[datetime]
    technicien1_id: Optional[int]
    technicien2_id: Optional[int]
    validation_ia: bool
    description: Optional[str]


# Dashboard models
class DashboardStats(BaseModel):
    total_sensors: int
    active_sensors: int
    faulty_sensors: int
    total_measurements_today: int
    total_anomalies_today: int
    avg_error_rate: float
    ongoing_interventions: int

class AnomalyAlert(BaseModel):
    capteur_id: str
    type_capteur: str
    zone_nom: str
    taux_erreur: float
    nb_anomalies: int
    last_anomaly: datetime


# Query models
class NLQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class NLQueryResponse(BaseModel):
    original_query: str
    sql_query: str
    results: List[dict]
    execution_time_ms: float
    row_count: int