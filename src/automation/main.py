"""
Automation Service — Digital Twin Industrial Automation System
=============================================================
Single-file FastAPI microservice.

Responsibilities:
  - Ingest sensor data from production stations
  - Run a multi-rule fault detection engine
  - Persist fault events to SQLite
  - Forward alerts to the Notification Service (with retries)

Run:
    uvicorn main:app --reload --port 8001
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

NOTIFICATION_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8002")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./automation.db")
HTTP_RETRIES = int(os.getenv("HTTP_RETRY_ATTEMPTS", "3"))

# Thresholds
TEMP_WARN = float(os.getenv("TEMP_WARN_C", "70"))
TEMP_CRIT = float(os.getenv("TEMP_CRIT_C", "90"))
TEMP_EXTREME = float(os.getenv("TEMP_EXTREME_C", "110"))          # Meltdown territory
PRESSURE_WARN = float(os.getenv("PRESSURE_WARN_BAR", "4.5"))
PRESSURE_CRIT = float(os.getenv("PRESSURE_CRIT_BAR", "6.0"))
FILL_UNDERFILL_ML = float(os.getenv("FILL_UNDERFILL_ML", "330"))  # Below this = underfill
FILL_OVERFILL_ML = float(os.getenv("FILL_OVERFILL_ML", "370"))    # Above this = overfill
SPEED_MAX = float(os.getenv("CONVEYOR_MAX_SPEED", "100"))          # units/min
VIBRATION_WARN = float(os.getenv("VIBRATION_WARN_G", "3.0"))
VIBRATION_CRIT = float(os.getenv("VIBRATION_CRIT_G", "6.0"))
BOTTLE_REJECT_RATE_WARN = float(os.getenv("REJECT_RATE_WARN", "0.05"))   # 5%
BOTTLE_REJECT_RATE_CRIT = float(os.getenv("REJECT_RATE_CRIT", "0.15"))   # 15%

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("automation")

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS fault_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id  TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    severity    TEXT    NOT NULL,
    description TEXT    NOT NULL,
    raw_payload TEXT,
    notified    INTEGER DEFAULT 0,
    created_at  TEXT    NOT NULL
)
"""

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_TABLE))

async def save_event(session: AsyncSession, station_id: str, event_type: str,
                     severity: str, description: str, raw_payload: str) -> int:
    result = await session.execute(
        text("""
            INSERT INTO fault_events (station_id, event_type, severity, description, raw_payload, created_at)
            VALUES (:sid, :et, :sev, :desc, :raw, :ts)
        """),
        {
            "sid": station_id, "et": event_type, "sev": severity,
            "desc": description, "raw": raw_payload,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
    await session.commit()
    return result.lastrowid

async def mark_notified(session: AsyncSession, event_id: int):
    await session.execute(
        text("UPDATE fault_events SET notified=1 WHERE id=:id"), {"id": event_id}
    )
    await session.commit()

async def fetch_events(session: AsyncSession, station_id: Optional[str], limit: int) -> List[dict]:
    if station_id:
        r = await session.execute(
            text("SELECT * FROM fault_events WHERE station_id=:s ORDER BY created_at DESC LIMIT :l"),
            {"s": station_id, "l": limit},
        )
    else:
        r = await session.execute(
            text("SELECT * FROM fault_events ORDER BY created_at DESC LIMIT :l"), {"l": limit}
        )
    cols = r.keys()
    return [dict(zip(cols, row)) for row in r.fetchall()]

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    INFO      = "info"
    WARNING   = "warning"
    CRITICAL  = "critical"
    EMERGENCY = "emergency"

class SensorPayload(BaseModel):
    station_id:               str   = Field(..., description="Station identifier, e.g. FILL-01")
    conveyor_speed:           float = Field(..., ge=0,    description="Belt speed in units/min")
    item_count:               int   = Field(..., ge=0,    description="Items detected in last cycle")
    temperature_c:            float = Field(...,          description="Station temperature °C")
    fill_volume_ml:           Optional[float] = Field(None, description="Liquid fill level ml (filling stations)")
    pressure_bar:             Optional[float] = Field(None, description="Line pressure in bar")
    vibration_g:              Optional[float] = Field(None, description="Vibration intensity in G")
    motor_current_amps:       Optional[float] = Field(None, description="Motor draw in amps")
    motor_rated_amps:         Optional[float] = Field(None, description="Motor rated capacity in amps")
    bottles_inspected:        Optional[int]   = Field(None, description="Bottles checked by vision system")
    bottles_rejected:         Optional[int]   = Field(None, description="Bottles rejected by vision system")
    label_feed_ok:            bool  = Field(True,  description="Labeling roll present and feeding")
    cap_feed_ok:              bool  = Field(True,  description="Cap feed hopper not empty")
    co2_pressure_bar:         Optional[float] = Field(None, description="CO2 supply pressure bar")
    co2_min_bar:              float = Field(2.5,   description="Minimum acceptable CO2 pressure")
    emergency_stop_triggered: bool  = Field(False, description="Manual e-stop activated")
    timestamp:                Optional[datetime] = None

class AnalysisResult(BaseModel):
    station_id:        str
    fault_detected:    bool
    event_type:        str
    severity:          Severity
    description:       str
    notification_sent: bool = False
    event_id:          Optional[int] = None

# ─────────────────────────────────────────────────────────────────────────────
# RULES ENGINE
# ─────────────────────────────────────────────────────────────────────────────
# Each rule is a function: SensorPayload -> Optional[tuple(event_type, Severity, description)]
# Rules are evaluated in order; first match wins (priority-ordered list at bottom).
# To add a rule: write a function, append it to RULES.

RuleResult = tuple  # (event_type: str, severity: Severity, description: str)

def rule_emergency_stop(p: SensorPayload) -> Optional[RuleResult]:
    """Operator-triggered emergency stop — unconditional highest priority."""
    if p.emergency_stop_triggered:
        return (
            "emergency_stop", Severity.EMERGENCY,
            f"[{p.station_id}] 🚨 EMERGENCY STOP activated by operator. "
            f"All downstream stations should halt immediately."
        )

def rule_extreme_overheat(p: SensorPayload) -> Optional[RuleResult]:
    """
    Extreme overheat — imminent equipment damage or fire risk.
    Treated as EMERGENCY because it may require evacuation.
    """
    if p.temperature_c >= TEMP_EXTREME:
        return (
            "extreme_overheat", Severity.EMERGENCY,
            f"[{p.station_id}] 🔥 EXTREME TEMPERATURE: {p.temperature_c:.1f}°C "
            f"(limit {TEMP_EXTREME}°C). Fire / meltdown risk — evacuate area."
        )

def rule_overheat_critical(p: SensorPayload) -> Optional[RuleResult]:
    if p.temperature_c >= TEMP_CRIT:
        return (
            "overheat", Severity.CRITICAL,
            f"[{p.station_id}] Critical overheat: {p.temperature_c:.1f}°C "
            f"(threshold {TEMP_CRIT}°C). Shutdown imminent if unresolved."
        )

def rule_overheat_warning(p: SensorPayload) -> Optional[RuleResult]:
    if p.temperature_c >= TEMP_WARN:
        return (
            "overheat", Severity.WARNING,
            f"[{p.station_id}] Temperature rising: {p.temperature_c:.1f}°C "
            f"(warning at {TEMP_WARN}°C). Monitor cooling system."
        )

def rule_pressure_critical(p: SensorPayload) -> Optional[RuleResult]:
    """High line pressure — risk of burst or seal failure."""
    if p.pressure_bar is not None and p.pressure_bar >= PRESSURE_CRIT:
        return (
            "pressure_critical", Severity.CRITICAL,
            f"[{p.station_id}] Line pressure CRITICAL: {p.pressure_bar:.2f} bar "
            f"(max {PRESSURE_CRIT} bar). Risk of pipe/seal rupture."
        )

def rule_pressure_warning(p: SensorPayload) -> Optional[RuleResult]:
    if p.pressure_bar is not None and p.pressure_bar >= PRESSURE_WARN:
        return (
            "pressure_warning", Severity.WARNING,
            f"[{p.station_id}] Line pressure elevated: {p.pressure_bar:.2f} bar "
            f"(warning at {PRESSURE_WARN} bar)."
        )

def rule_jam(p: SensorPayload) -> Optional[RuleResult]:
    """
    Classic jam: conveyor is moving but zero items are passing through.
    Could be a physical blockage or a failed feeder.
    """
    if p.item_count == 0 and p.conveyor_speed > 0:
        return (
            "jam", Severity.CRITICAL,
            f"[{p.station_id}] JAM detected: conveyor at {p.conveyor_speed:.1f} units/min "
            f"but item count is 0. Line likely blocked."
        )

def rule_conveyor_overspeed(p: SensorPayload) -> Optional[RuleResult]:
    """Conveyor running above rated maximum — mechanical stress / spillage risk."""
    if p.conveyor_speed > SPEED_MAX:
        excess = p.conveyor_speed - SPEED_MAX
        return (
            "conveyor_overspeed", Severity.WARNING,
            f"[{p.station_id}] Conveyor overspeed: {p.conveyor_speed:.1f} units/min "
            f"({excess:.1f} above max {SPEED_MAX}). Risk of mechanical damage."
        )

def rule_motor_overload(p: SensorPayload) -> Optional[RuleResult]:
    """
    Motor current exceeds rated capacity — thermal overload, bearing failure, or jam.
    We use percentage of rated current for a universal metric.
    """
    if p.motor_current_amps is not None and p.motor_rated_amps:
        ratio = p.motor_current_amps / p.motor_rated_amps
        if ratio >= 1.3:
            return (
                "motor_overload", Severity.CRITICAL,
                f"[{p.station_id}] Motor overload: drawing {p.motor_current_amps:.1f}A "
                f"({ratio*100:.0f}% of rated {p.motor_rated_amps:.1f}A). "
                f"Overload protection may trip."
            )
        if ratio >= 1.1:
            return (
                "motor_high_current", Severity.WARNING,
                f"[{p.station_id}] Motor current elevated: {p.motor_current_amps:.1f}A "
                f"({ratio*100:.0f}% of rated). Check for mechanical resistance."
            )

def rule_vibration_critical(p: SensorPayload) -> Optional[RuleResult]:
    """High vibration — loose components, bearing failure, or imbalance."""
    if p.vibration_g is not None and p.vibration_g >= VIBRATION_CRIT:
        return (
            "vibration_critical", Severity.CRITICAL,
            f"[{p.station_id}] Critical vibration: {p.vibration_g:.2f}G "
            f"(limit {VIBRATION_CRIT}G). Risk of structural damage or component ejection."
        )

def rule_vibration_warning(p: SensorPayload) -> Optional[RuleResult]:
    if p.vibration_g is not None and p.vibration_g >= VIBRATION_WARN:
        return (
            "vibration_warning", Severity.WARNING,
            f"[{p.station_id}] Elevated vibration: {p.vibration_g:.2f}G "
            f"(warning {VIBRATION_WARN}G). Inspect bearings and fasteners."
        )

def rule_fill_overfill(p: SensorPayload) -> Optional[RuleResult]:
    """Filling station dispensing too much — product waste and possible overflow."""
    if p.fill_volume_ml is not None and p.fill_volume_ml > FILL_OVERFILL_ML:
        excess = p.fill_volume_ml - FILL_OVERFILL_ML
        return (
            "fill_overfill", Severity.WARNING,
            f"[{p.station_id}] Overfill detected: {p.fill_volume_ml:.1f}ml "
            f"(+{excess:.1f}ml over limit {FILL_OVERFILL_ML}ml). "
            f"Calibrate fill nozzle solenoid."
        )

def rule_fill_underfill(p: SensorPayload) -> Optional[RuleResult]:
    """Under-filled bottles are a product quality / regulatory non-compliance issue."""
    if p.fill_volume_ml is not None and p.fill_volume_ml < FILL_UNDERFILL_ML:
        deficit = FILL_UNDERFILL_ML - p.fill_volume_ml
        return (
            "fill_underfill", Severity.CRITICAL,
            f"[{p.station_id}] Underfill detected: {p.fill_volume_ml:.1f}ml "
            f"(-{deficit:.1f}ml below minimum {FILL_UNDERFILL_ML}ml). "
            f"Product non-compliant — quarantine batch."
        )

def rule_high_rejection_rate(p: SensorPayload) -> Optional[RuleResult]:
    """
    Vision system rejection rate too high — systematic quality problem.
    Could indicate foreign matter, deformed bottles, or mislabeling.
    """
    if p.bottles_inspected and p.bottles_inspected > 0 and p.bottles_rejected is not None:
        rate = p.bottles_rejected / p.bottles_inspected
        if rate >= BOTTLE_REJECT_RATE_CRIT:
            return (
                "high_rejection_rate", Severity.CRITICAL,
                f"[{p.station_id}] Vision system rejection CRITICAL: "
                f"{p.bottles_rejected}/{p.bottles_inspected} bottles rejected "
                f"({rate*100:.1f}%). Halt line and inspect for contamination."
            )
        if rate >= BOTTLE_REJECT_RATE_WARN:
            return (
                "elevated_rejection_rate", Severity.WARNING,
                f"[{p.station_id}] Elevated rejection rate: "
                f"{p.bottles_rejected}/{p.bottles_inspected} ({rate*100:.1f}%). "
                f"Inspect labeling / cap application."
            )

def rule_label_feed_fault(p: SensorPayload) -> Optional[RuleResult]:
    """Label roll empty or misfeeding — products will ship unlabeled."""
    if not p.label_feed_ok:
        return (
            "label_feed_fault", Severity.CRITICAL,
            f"[{p.station_id}] Label feed fault. Label roll may be empty or jammed. "
            f"Bottles will ship without labels — halt labeling station."
        )

def rule_cap_feed_fault(p: SensorPayload) -> Optional[RuleResult]:
    """Cap hopper empty — bottles will ship uncapped (product spoilage / safety)."""
    if not p.cap_feed_ok:
        return (
            "cap_feed_fault", Severity.CRITICAL,
            f"[{p.station_id}] Cap feed fault. Hopper may be empty. "
            f"Bottles will be uncapped — halt capping station immediately."
        )

def rule_co2_pressure_low(p: SensorPayload) -> Optional[RuleResult]:
    """
    CO2 supply pressure below minimum — carbonation will fail,
    producing flat product that fails quality checks.
    """
    if p.co2_pressure_bar is not None and p.co2_pressure_bar < p.co2_min_bar:
        return (
            "co2_low_pressure", Severity.WARNING,
            f"[{p.station_id}] CO2 pressure low: {p.co2_pressure_bar:.2f} bar "
            f"(min {p.co2_min_bar:.2f} bar). Carbonation quality at risk — "
            f"check CO2 supply cylinder."
        )

# ── Priority-ordered rule list ─────────────────────────────────────────────
# Rules at the top take precedence. First match wins.
RULES = [
    rule_emergency_stop,
    rule_extreme_overheat,
    rule_overheat_critical,
    rule_pressure_critical,
    rule_motor_overload,         # motor_overload returns WARNING or CRITICAL depending on ratio
    rule_vibration_critical,
    rule_jam,
    rule_label_feed_fault,
    rule_cap_feed_fault,
    rule_fill_underfill,
    rule_high_rejection_rate,    # high_rejection handles both CRIT and WARN internally
    rule_overheat_warning,
    rule_pressure_warning,
    rule_conveyor_overspeed,
    rule_vibration_warning,
    rule_fill_overfill,
    rule_co2_pressure_low,
]

def evaluate(payload: SensorPayload) -> Optional[RuleResult]:
    for rule in RULES:
        result = rule(payload)
        if result is not None:
            return result
    return None

# ─────────────────────────────────────────────────────────────────────────────
# HTTP CLIENT (with retries)
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(HTTP_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    reraise=True,
)
async def _post_with_retry(url: str, payload: dict) -> bool:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        try:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            log.error("Notification service HTTP %d: %s", e.response.status_code, e.response.text)
            return False

async def notify(event_id: int, event_type: str, severity: str,
                 station_id: str, description: str, snapshot: dict) -> bool:
    try:
        return await _post_with_retry(
            f"{NOTIFICATION_URL}/api/v1/alerts",
            {
                "event_id": event_id,
                "event_type": event_type,
                "severity": severity,
                "station_id": station_id,
                "description": description,
                "sensor_snapshot": snapshot,
            },
        )
    except Exception as e:
        log.error("Failed to reach notification service after %d retries: %s", HTTP_RETRIES, e)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    log.info("Automation Service ready on port 8001")
    yield

app = FastAPI(
    title="Automation Service",
    description="Rules-engine brain for the Digital Twin soft-drink production line.",
    version="2.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "automation"}

@app.post("/api/v1/sensor-data", response_model=AnalysisResult)
async def analyze(payload: SensorPayload):
    """
    Submit a sensor reading. The rules engine evaluates it and, if a fault
    is detected, persists it and notifies the Notification Service.
    """
    result = evaluate(payload)

    if result is None:
        return AnalysisResult(
            station_id=payload.station_id,
            fault_detected=False,
            event_type="normal",
            severity=Severity.INFO,
            description=f"[{payload.station_id}] All parameters nominal.",
        )

    event_type, severity, description = result
    log.warning("FAULT | %s | %s | %s", severity.upper(), event_type, description)

    async with SessionLocal() as session:
        event_id = await save_event(
            session, payload.station_id, event_type, severity.value,
            description, json.dumps(payload.model_dump(mode="json"), default=str)
        )
        notified = await notify(
            event_id, event_type, severity.value,
            payload.station_id, description,
            payload.model_dump(mode="json"),
        )
        if notified:
            await mark_notified(session, event_id)

    return AnalysisResult(
        station_id=payload.station_id,
        fault_detected=True,
        event_type=event_type,
        severity=severity,
        description=description,
        notification_sent=notified,
        event_id=event_id,
    )

@app.get("/api/v1/events")
async def list_events(
    station_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    async with SessionLocal() as session:
        return await fetch_events(session, station_id, limit)

# ─────────────────────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
