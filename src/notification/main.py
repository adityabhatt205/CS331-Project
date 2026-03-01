"""
Notification Service 
================================================================
Responsibilities:
  - Receive fault alerts from the Automation Service
  - Route to correct email recipients based on severity (via recipients.json)
  - Dispatch HTML emails via aiosmtplib (Gmail / any SMTP)
  - Log all notifications to SQLite
  - Provide console output for every alert
"""

import json
from dotenv import load_dotenv
load_dotenv()
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosmtplib
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

DATABASE_URL     = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./notification.db")
RECIPIENTS_FILE  = os.getenv("RECIPIENTS_FILE", "recipients.json")
SMTP_HOST        = "smtp.gmail.com"
SMTP_PORT        = 587
SMTP_USERNAME    = "digital.twin.cs31@gmail.com"
SMTP_PASSWORD    = "abze nfve jkaf orcz"
SMTP_FROM        = "digital.twin.cs31@gmail.com"
SMTP_TLS         = True
EMAIL_ENABLED    = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("notification")

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS notification_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id         INTEGER,
    event_type       TEXT NOT NULL,
    severity         TEXT NOT NULL,
    station_id       TEXT NOT NULL,
    description      TEXT NOT NULL,
    email_recipients TEXT,
    email_sent       INTEGER DEFAULT 0,
    console_logged   INTEGER DEFAULT 1,
    created_at       TEXT NOT NULL
)
"""

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_TABLE))

async def log_notification(session: AsyncSession, event_id: Optional[int], event_type: str,
                            severity: str, station_id: str, description: str,
                            recipients: List[str], email_sent: bool) -> int:
    result = await session.execute(
        text("""
            INSERT INTO notification_logs
              (event_id, event_type, severity, station_id, description,
               email_recipients, email_sent, created_at)
            VALUES (:eid, :et, :sev, :sid, :desc, :recip, :sent, :ts)
        """),
        {
            "eid": event_id, "et": event_type, "sev": severity, "sid": station_id,
            "desc": description,
            "recip": ", ".join(recipients) if recipients else None,
            "sent": int(email_sent),
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
    await session.commit()
    return result.lastrowid

async def update_email_sent(session: AsyncSession, log_id: int, sent: bool):
    await session.execute(
        text("UPDATE notification_logs SET email_sent=:s WHERE id=:id"),
        {"s": int(sent), "id": log_id},
    )
    await session.commit()

async def fetch_logs(session: AsyncSession, severity: Optional[str], limit: int) -> List[dict]:
    if severity:
        r = await session.execute(
            text("SELECT * FROM notification_logs WHERE severity=:s ORDER BY created_at DESC LIMIT :l"),
            {"s": severity, "l": limit},
        )
    else:
        r = await session.execute(
            text("SELECT * FROM notification_logs ORDER BY created_at DESC LIMIT :l"),
            {"l": limit},
        )
    cols = r.keys()
    return [dict(zip(cols, row)) for row in r.fetchall()]

_TIER_ORDER = ["emergency", "critical", "warning", "info"]

@lru_cache(maxsize=1)
def _load_routing() -> Dict[str, List[str]]:
    path = Path(RECIPIENTS_FILE)
    if not path.exists():
        log.warning(
            "recipients.json not found at '%s'. No emails will be sent until it is created.",
            path.resolve(),
        )
        return {t: [] for t in _TIER_ORDER}
    try:
        data = json.loads(path.read_text())
        routing = {k.lower(): v for k, v in data.items()}
        log.info("Loaded recipient routing: %s", {k: len(v) for k, v in routing.items()})
        return routing
    except Exception as e:
        log.error("Failed to parse recipients.json: %s", e)
        return {t: [] for t in _TIER_ORDER}

def reload_routing():
    _load_routing.cache_clear()

def resolve_recipients(severity: str) -> List[str]:
    """
    Return deduplicated recipients for the given severity.
    Higher tiers are always included (emergency ⊇ critical ⊇ warning ⊇ info).
    """
    routing = _load_routing()
    sev = severity.lower()
    try:
        tier_idx = _TIER_ORDER.index(sev)
    except ValueError:
        tier_idx = len(_TIER_ORDER) - 1

    # collect from this tier UP (towards emergency)
    all_recipients: List[str] = []
    for tier in _TIER_ORDER[: tier_idx + 1]:
        all_recipients.extend(routing.get(tier, []))

    # deduplicate preserving order
    seen: set = set()
    result = []
    for addr in all_recipients:
        if addr not in seen:
            seen.add(addr)
            result.append(addr)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL CHANNEL
# ─────────────────────────────────────────────────────────────────────────────

_SEVERITY_COLOR = {
    "emergency": "#7B0000",
    "critical":  "#C0392B",
    "warning":   "#E67E22",
    "info":      "#2980B9",
}

_SEVERITY_ICON = {
    "emergency": "🚨",
    "critical":  "🔴",
    "warning":   "🟠",
    "info":      "🔵",
}

def _build_email_html(severity: str, event_type: str, station_id: str,
                      description: str, snapshot: Optional[dict]) -> str:
    color = _SEVERITY_COLOR.get(severity.lower(), "#555")
    icon  = _SEVERITY_ICON.get(severity.lower(), "⚪")
    ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    snapshot_rows = ""
    if snapshot:
        snapshot_rows = "".join(
            f"<tr><td style='padding:4px 8px;color:#666;font-size:12px'>{k}</td>"
            f"<td style='padding:4px 8px;font-size:12px'><b>{v}</b></td></tr>"
            for k, v in snapshot.items()
            if v is not None and k != "timestamp"
        )
        snapshot_section = f"""
        <h3 style='color:#555;font-size:13px;margin-top:20px'>Sensor Snapshot</h3>
        <table style='border-collapse:collapse;width:100%;background:#f9f9f9;
                      border-radius:4px;overflow:hidden'>
            {snapshot_rows}
        </table>"""
    else:
        snapshot_section = ""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,sans-serif">
  <div style="max-width:620px;margin:30px auto;background:#fff;border-radius:10px;
              overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">

    <!-- Header bar -->
    <div style="background:{color};padding:20px 28px">
      <p style="margin:0;color:rgba(255,255,255,0.8);font-size:11px;
                letter-spacing:1px;text-transform:uppercase">
        Digital Twin — Industrial Alert
      </p>
      <h1 style="margin:6px 0 0;color:#fff;font-size:22px">
        {icon} {severity.upper()} — {event_type.replace("_"," ").title()}
      </h1>
    </div>

    <!-- Body -->
    <div style="padding:24px 28px">
      <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
        <tr>
          <td style="padding:4px 0;color:#999;font-size:12px;width:110px">Station</td>
          <td style="padding:4px 0;font-weight:bold">{station_id}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#999;font-size:12px">Event Type</td>
          <td style="padding:4px 0">{event_type}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#999;font-size:12px">Time</td>
          <td style="padding:4px 0">{ts}</td>
        </tr>
      </table>

      <div style="background:#fff8f0;border-left:4px solid {color};
                  padding:12px 16px;border-radius:0 4px 4px 0;margin-bottom:16px">
        <p style="margin:0;color:#333;font-size:14px;line-height:1.6">{description}</p>
      </div>

      {snapshot_section}

      <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
      <p style="margin:0;font-size:11px;color:#aaa;text-align:center">
        Automated alert from the Digital Twin Production Monitoring System.<br>
        Do not reply to this email.
      </p>
    </div>
  </div>
</body>
</html>
"""

async def send_email(
    recipients: List[str],
    severity: str,
    event_type: str,
    station_id: str,
    description: str,
    snapshot: Optional[dict] = None,
) -> bool:
    """
    Dispatch a styled HTML alert email.
    Returns True on success, False on any SMTP failure.
    Validates config before attempting to send.
    """
    if not recipients:
        log.info("No recipients configured for severity=%s — skipping email.", severity)
        return False

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        log.warning(
            "SMTP credentials missing (SMTP_USERNAME / SMTP_PASSWORD). "
            "Set them in your .env to enable email dispatch."
        )
        return False

    subject = (
        f"[{severity.upper()}] {event_type.replace('_',' ').title()} — {station_id}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_FROM or SMTP_USERNAME
    msg["To"]      = ", ".join(recipients)

    # Plain text fallback
    plain = (
        f"ALERT: {severity.upper()} | {event_type} | {station_id}\n\n"
        f"{description}\n\n"
        f"Time: {datetime.now(timezone.utc).isoformat()}"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(
        _build_email_html(severity, event_type, station_id, description, snapshot),
        "html",
    ))

    try:
        log.info(
            "Sending email to %d recipient(s): %s | Subject: %s",
            len(recipients), recipients, subject,
        )
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            start_tls=SMTP_TLS,
        )
        log.info("✅ Email delivered to: %s", recipients)
        return True

    except aiosmtplib.SMTPAuthenticationError:
        log.error(
            "❌ SMTP authentication failed for user '%s'. "
            "Check SMTP_USERNAME / SMTP_PASSWORD. "
            "For Gmail, use an App Password (not your account password).",
            SMTP_USERNAME,
        )
        return False

    except aiosmtplib.SMTPConnectError as e:
        log.error("❌ Cannot connect to SMTP server %s:%d — %s", SMTP_HOST, SMTP_PORT, e)
        return False

    except aiosmtplib.SMTPException as e:
        log.error("❌ SMTP error: %s", e)
        return False

    except Exception as e:
        log.error("❌ Unexpected error in email channel: %s", e)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# CONSOLE CHANNEL
# ─────────────────────────────────────────────────────────────────────────────

def log_to_console(severity: str, event_type: str, station_id: str, description: str):
    icon = _SEVERITY_ICON.get(severity.lower(), "⚪")
    msg  = f"{icon} [{severity.upper()}] {event_type} | {station_id} | {description}"
    {
        "emergency": log.critical,
        "critical":  log.critical,
        "warning":   log.warning,
        "info":      log.info,
    }.get(severity.lower(), log.info)(msg)

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class AlertRequest(BaseModel):
    event_id:        Optional[int] = None
    event_type:      str
    severity:        str
    station_id:      str
    description:     str
    sensor_snapshot: Optional[Dict[str, Any]] = None

class AlertResponse(BaseModel):
    accepted:          bool
    log_id:            int
    channels_used:     List[str]
    email_sent:        bool
    email_recipients:  List[str]

# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND EMAIL TASK
# ─────────────────────────────────────────────────────────────────────────────

async def _email_task(log_id: int, recipients: List[str], severity: str,
                      event_type: str, station_id: str,
                      description: str, snapshot: Optional[dict]):
    """
    Runs outside the request lifecycle via FastAPI BackgroundTasks.
    Sends the email then updates the DB row with the result.
    """
    sent = await send_email(recipients, severity, event_type, station_id, description, snapshot)
    async with SessionLocal() as session:
        await update_email_sent(session, log_id, sent)
    if sent:
        log.info("Background email task complete — log_id=%d ✅", log_id)
    else:
        log.warning("Background email task failed  — log_id=%d ❌", log_id)

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    log.info("Notification Service ready on port 8002")
    log.info("Email enabled: %s | SMTP: %s:%d", EMAIL_ENABLED, SMTP_HOST, SMTP_PORT)
    if EMAIL_ENABLED and not SMTP_USERNAME:
        log.warning("EMAIL_ENABLED=true but SMTP_USERNAME is not set. Emails will not send.")
    yield

app = FastAPI(
    title="Notification Service",
    description="Multi-channel alert dispatcher for the Digital Twin soft-drink production line.",
    version="2.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "notification",
        "email_enabled": EMAIL_ENABLED,
        "smtp_configured": bool(SMTP_USERNAME and SMTP_PASSWORD),
    }

@app.post("/api/v1/alerts", response_model=AlertResponse)
async def receive_alert(alert: AlertRequest, background_tasks: BackgroundTasks):
    """
    Receives a fault alert from the Automation Service.
    - Console logging happens immediately (synchronous).
    - Email is dispatched in the background (non-blocking).
    """
    # 1 — Console (always, always synchronous)
    log_to_console(alert.severity, alert.event_type, alert.station_id, alert.description)

    # 2 — Resolve recipients
    recipients: List[str] = []
    if EMAIL_ENABLED:
        recipients = resolve_recipients(alert.severity)

    # 3 — Persist log entry (email_sent stays False until background task updates it)
    async with SessionLocal() as session:
        log_id = await log_notification(
            session,
            event_id=alert.event_id,
            event_type=alert.event_type,
            severity=alert.severity,
            station_id=alert.station_id,
            description=alert.description,
            recipients=recipients,
            email_sent=False,
        )

    channels = ["console"]

    # 4 — Schedule email as background task (response returns immediately)
    if recipients and EMAIL_ENABLED:
        channels.append("email")
        background_tasks.add_task(
            _email_task,
            log_id=log_id,
            recipients=recipients,
            severity=alert.severity,
            event_type=alert.event_type,
            station_id=alert.station_id,
            description=alert.description,
            snapshot=alert.sensor_snapshot,
        )

    return AlertResponse(
        accepted=True,
        log_id=log_id,
        channels_used=channels,
        email_sent=False,         # will be updated async; check /api/v1/logs to confirm
        email_recipients=recipients,
    )

@app.get("/api/v1/logs")
async def list_logs(
    severity: Optional[str] = Query(None, description="Filter: info|warning|critical|emergency"),
    limit: int = Query(50, ge=1, le=500),
):
    async with SessionLocal() as session:
        return await fetch_logs(session, severity, limit)

@app.post("/api/v1/recipients/reload")
async def reload_recipients():
    """Hot-reload recipients.json without restarting the service."""
    reload_routing()
    routing = _load_routing()
    return {"reloaded": True, "routing_summary": {k: len(v) for k, v in routing.items()}}

# ─────────────────────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
