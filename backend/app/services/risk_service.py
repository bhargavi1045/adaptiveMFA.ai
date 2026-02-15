from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone as tz, timedelta
from sqlalchemy.orm import Session
import hashlib
import json
import os
import random

from app.config import settings
from app.models.user import User
from app.models.login_event import LoginEvent
from app.utils.logger import logger
import numpy as np


class DeviceFingerprintService:
    """Device fingerprinting with SHA256"""

    @staticmethod
    def calculate_fingerprint(user_agent: str, ip_address: str, device_id: str) -> str:
        
        try:
            raw = f"{user_agent or ''}|{ip_address or ''}|{device_id or ''}"
            return hashlib.sha256(raw.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Fingerprint calculation failed: {e}")
            return hashlib.sha256(b"unknown").hexdigest()

    @staticmethod
    def is_device_known(
        user_id: str,
        fingerprint: str,
        db: Session
    ) -> Tuple[bool, Optional[datetime]]:
        
        try:
            login = db.query(LoginEvent).filter(
                LoginEvent.user_id == user_id,
                LoginEvent.device_fingerprint == fingerprint,
                LoginEvent.user_action == "approved"
            ).order_by(LoginEvent.timestamp.desc()).first()

            if login:
                return True, login.timestamp
            return False, None
        except Exception as e:
            logger.error(f"Device history check failed: {e}")
            return False, None


class BehavioralAnalysisService:
    """Analyze login behavior for anomalies"""

    @staticmethod
    def calculate_behavior_deviation(
        user: User,
        typing_speed: float,
        key_interval: float,
        key_hold: float
    ) -> float:
        """
        Calculate maximum deviation from user's baseline behavior
        """
        try:
            if not user.behavior_profile:
                return 0.3  
            
            profile = json.loads(user.behavior_profile)
            
            def dev(current: float, baseline: float) -> float:
                if baseline == 0:
                    return 0.0 if current == 0 else 1.0
                return abs(current - baseline) / baseline
            
            return max(
                dev(typing_speed, profile.get("typing_speed", 0.0)),
                dev(key_interval, profile.get("key_interval", 0.0)),
                dev(key_hold, profile.get("key_hold", 0.0)),
            )
        except Exception as e:
            logger.error(f"Behavior deviation calculation failed: {e}")
            return 0.5


class RiskAssessmentService:

    def __init__(self):
        """Initialize risk assessment service"""
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.device_service = DeviceFingerprintService()
        self.behavior_service = BehavioralAnalysisService()
        
        try:
            from app.services.anomaly_service import AnomalyService
            self.anomaly_service = AnomalyService()
            logger.info("AnomalyService initialized")
        except Exception as e:
            logger.warning(f"AnomalyService not available: {e}")
            self.anomaly_service = None
        
        if settings.LLM_EXPLANATION_ENABLED and self.groq_api_key:
            try:
                from groq import Groq
                self.llm = Groq(api_key=self.groq_api_key)
                logger.info("Groq LLM initialized")
            except Exception as e:
                logger.warning(f"Groq LLM not available: {e}")
                self.llm = None
        else:
            self.llm = None
            if not settings.LLM_EXPLANATION_ENABLED:
                logger.info("LLM explanations disabled in settings")

    def assess_login(
        self,
        login_event: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Complete risk assessment for login
        """
        try:
            #Device Fingerprinting
            device_fingerprint = login_event.get("device_fingerprint")
        
            if not device_fingerprint:
                logger.warning("No device_fingerprint in login_event")
                device_fingerprint = "unknown"
        
            logger.info(f"Device fingerprint received: {device_fingerprint}")
        
            # Check if device is known
            device_known, last_seen = DeviceFingerprintService.is_device_known(
                str(user.id),
                device_fingerprint,
                db
            )
        
            logger.info(f"Device known: {device_known}, last seen: {last_seen}")

           
            #Behavioral Analysis
            
            typing_speed = login_event.get("typing_speed", 0.0)
            key_interval = login_event.get("key_interval", 0.0)
            key_hold = login_event.get("key_hold", 0.0)

            deviation = BehavioralAnalysisService.calculate_behavior_deviation(
                user,
                typing_speed,
                key_interval,
                key_hold
            )
            behavior_risk = self._map_deviation_to_risk(deviation)
            logger.debug(f"Behavior deviation: {deviation:.3f} ({behavior_risk})")

           
            #ML-based Anomaly Detection
            ml_score, ml_explanation = self._ml_risk_score(user, login_event)
            logger.debug(f"ML anomaly score: {ml_score:.3f}")

            #Location Metric (Impossible Travel Detection)
            location_metric = 0.0
        
            last_login = db.query(LoginEvent).filter(
                LoginEvent.user_id == user.id,
                LoginEvent.device_fingerprint == device_fingerprint,
                LoginEvent.timestamp > (datetime.now(tz.utc) - timedelta(days=30))
            ).order_by(LoginEvent.timestamp.desc()).offset(1).first()

            current_lat = login_event.get("location_latitude")
            current_lon = login_event.get("location_longitude")
        
            if (last_login and 
                last_login.location_latitude and last_login.location_longitude and
                current_lat and current_lon):
                try:
                    from geopy.distance import geodesic
                
                    last_coords = (last_login.location_latitude, last_login.location_longitude)
                    current_coords = (current_lat, current_lon)
                    distance_km = geodesic(last_coords, current_coords).km
                    time_diff_hours = (datetime.now(tz.utc) - last_login.timestamp).total_seconds() / 3600
                
                    if time_diff_hours > 0:
                        location_metric = distance_km / time_diff_hours
                        logger.info(f"Location: {distance_km:.2f}km in {time_diff_hours:.2f}h = {location_metric:.2f} km/h")
                        if location_metric > 900:
                            logger.warning(f"IMPOSSIBLE TRAVEL: {location_metric:.2f} km/h")
                    else:
                        location_metric = 0.0
                except Exception as e:
                    logger.warning(f"Location metric failed: {e}")
                    location_metric = 0.0
            else:
                location_metric = 0.0

            
            #Combine All Signals into Risk Score
            risk_score = self._combine_signals(
                device_known,
                deviation,
                ml_score,
                location_metric
            )
            risk_level = self._map_score_to_level(risk_score)

            logger.info(
                f"Risk Assessment: score={risk_score:.2f}, level={risk_level}, "
                f"device_known={device_known}, behavior={behavior_risk}, ml={ml_score:.2f}"
            )

            
            #Generate Explanation
            explanation = self._generate_explanation(
                user,
                login_event,
                risk_score,
                behavior_risk,
                ml_explanation,
                device_known=device_known,
                location_metric=location_metric
            )

            
            #Build Response
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "explanation": explanation,
                "device_fingerprint": device_fingerprint,
                "device_known": device_known,
                "last_seen": last_seen,
                "behavior_risk": behavior_risk,
                "anomaly_score": ml_score,
                "location_metric": location_metric,
                "mfa_required": risk_score > settings.RISK_THRESHOLD_LOW,
            }

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}", exc_info=True)
            return self._error_response()

    #Signal Combination 

    def _ml_risk_score(self, user: User, login_event: Dict[str, Any]) -> Tuple[float, str]:
        """
        Compute ML anomaly score using AnomalyService
        
        """
        try:
            if self.anomaly_service is None:
                logger.warning("AnomalyService not available")
                return 0.5, "ML detector unavailable, neutral score used"
            
            if not self.anomaly_service.is_trained:
                logger.debug("AnomalyService not trained yet")
                return 0.5, "ML model not trained yet"

            score = self.anomaly_service.detect_anomaly(login_event)
            
            if score < 0.3:
                explanation = "Low anomaly detected"
            elif score < 0.7:
                explanation = "Medium anomaly level"
            else:
                explanation = "High anomaly detected"
            
            logger.debug(f"ML scoring: score={score:.3f}, explanation={explanation}")
            return float(score), explanation

        except Exception as e:
            logger.error(f"ML risk scoring failed: {e}")
            return 0.5, "ML scoring failed, default score used"

    @staticmethod
    def _combine_signals(
        device_known: bool,
        deviation: float,
        ml_score: float,
        location_metric: float = 0.0
    ) -> float:
        
        device_factor = 0.0 if device_known else 0.35
        behavior_factor = min(deviation, 1.0) * 0.28
        ml_factor = min(ml_score, 1.0) * 0.27
        
        # Location factor for impossible travel
        location_factor = 0.0
        if location_metric > 900:
            location_factor = 0.10  # 10% risk for impossible travel
            logger.warning(f"Impossible travel detected: {location_metric:.2f} km/h")
        elif location_metric > 200:
            location_factor = 0.02  # 2% for flight speed
        
        risk_score = min(1.0, device_factor + behavior_factor + ml_factor + location_factor)
        
        logger.debug(
            f"Risk signals combined: "
            f"device={device_factor:.2f} + behavior={behavior_factor:.2f} + "
            f"ml={ml_factor:.2f} + location={location_factor:.2f} = {risk_score:.2f}"
        )
        
        return risk_score

    #Mapping and Classfication
    @staticmethod
    def _map_deviation_to_risk(deviation: float) -> str:
        """Map behavioral deviation to low/medium/high risk"""
        if deviation < 0.2:
            return "low"
        elif deviation < 0.5:
            return "medium"
        else:
            return "high"

    @staticmethod
    def _map_score_to_level(score: float) -> str:
        """Convert numeric score to risk level"""
        if score < settings.RISK_THRESHOLD_LOW:
            return "low"
        elif score < settings.RISK_THRESHOLD_HIGH:
            return "medium"
        else:
            return "high"

    @staticmethod
    def _generate_explanation(
        user: User,
        login_event: Dict[str, Any],
        risk_score: float,
        behavior_risk: str,
        ml_explanation: str,
        device_known: bool = False,
        location_metric: float = 0.0
    ) -> str:
        """Generate human-readable explanation of risk assessment"""
        parts = []
        
        if risk_score > 0.7:
            parts.append("High risk login detected.")
        elif risk_score > 0.3:
            parts.append("Medium risk login detected.")
        else:
            parts.append("Low risk login.")

        # Device status
        if not device_known:
            parts.append("Device not recognized.")
        else:
            parts.append("Device is known and trusted.")

        # Behavioral anomalies
        if behavior_risk == "high":
            parts.append("Behavioral anomaly detected.")
        elif behavior_risk == "medium":
            parts.append("Some behavioral variation observed.")

        # ML anomaly
        if ml_explanation:
            parts.append(f"ML analysis: {ml_explanation}.")

        # Location
        location = login_event.get("location", "Unknown")
        ip = login_event.get("ip_address", "Unknown")
        parts.append(f"Login from {location} (IP: {ip}).")

        # Impossible travel warning
        if location_metric > 900:
            parts.append(f"Impossible travel detected ({location_metric:.0f} km/h).")

        return " ".join(parts)

    @staticmethod
    def _error_response() -> Dict[str, Any]:
        """Safe default response on error"""
        return {
            "risk_score": 0.5,
            "risk_level": "medium",
            "anomaly_score": 0.5,
            "behavior_risk": "medium",
            "explanation": "Unable to assess risk. Default MFA enabled for safety.",
            "device_fingerprint": None,
            "device_known": False,
            "last_seen": None,
            "location_metric": 0.0,
            "mfa_required": True,
        }

    #Utility

    @staticmethod
    def calculate_risk_score(anomaly_score: float, rag_score: Optional[float] = None) -> float:

        if rag_score is None:
            return max(0.0, min(1.0, anomaly_score))
        combined = (anomaly_score + rag_score) / 2
        return max(0.0, min(1.0, combined))

    @staticmethod
    def get_risk_level(risk_score: float) -> str:
        """Convert risk score to categorical level"""
        if risk_score < settings.RISK_THRESHOLD_LOW:
            return "LOW"
        elif risk_score < settings.RISK_THRESHOLD_HIGH:
            return "MEDIUM"
        else:
            return "HIGH"

    import functools
import time
from pathlib import Path
from typing import Optional


_geo_cache: dict[str, tuple[Optional[str], float]] = {}
_GEO_CACHE_TTL = 3600  

_LOCALHOST_ADDRESSES = frozenset({"127.0.0.1", "::1", "0.0.0.0"})


def _get_db_path() -> Path:
    raw = os.environ.get("GEOIP_DB_PATH", "/etc/geoip/GeoLite2-City.mmdb")
    path = Path(raw)
    if not path.exists():
        raise FileNotFoundError(
            f"GeoIP database not found at '{path}'. "
            "Set the GEOIP_DB_PATH environment variable to the correct path."
        )
    return path


@staticmethod
def resolve_ip_location(ip_address: str) -> Optional[str]:
    if not ip_address:
        return None

    if ip_address in _LOCALHOST_ADDRESSES:
        return "Localhost"

    cached = _geo_cache.get(ip_address)
    if cached is not None:
        location, expiry = cached
        if time.monotonic() < expiry:
            return location
        del _geo_cache[ip_address]

    location: Optional[str] = None
    try:
        import geoip2.database
        import geoip2.errors

        db_path = _get_db_path()

        with geoip2.database.Reader(str(db_path)) as reader:
            record = reader.city(ip_address)

            city    = record.city.name or ""
            region  = (record.subdivisions[0].iso_code
                       if record.subdivisions else "")
            country = record.country.iso_code or ""

            if city and region:
                location = f"{city}, {region}"
            elif city and country:
                location = f"{city}, {country}"
            elif country:
                location = country

    except FileNotFoundError as exc:
       
        logger.error(str(exc))

    except ImportError:
        logger.error(
            "geoip2 package is not installed. "
            "Run: pip install geoip2"
        )

    except Exception as exc:
        logger.warning(f"GeoIP lookup failed for {ip_address!r}: {exc}")

    _geo_cache[ip_address] = (location, time.monotonic() + _GEO_CACHE_TTL)

    return location