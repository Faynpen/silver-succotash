"""
Fall Detection & Emergency Response Tools
---
Mock fall detection using simulated accelerometer data and camera analysis.
Emergency response: alerts, ambulance dispatch, contact notification.
"""

import random
from datetime import datetime


def detect_fall(patient_id: str) -> str:
    """Analyze accelerometer data to detect if a fall has occurred. Returns fall probability, impact force, and camera confirmation status."""
    fall_prob = random.random()
    impact_force = round(random.uniform(1.0, 15.0), 1)
    camera_confirm = random.choice([True, False])
    patient_response = random.choice(["responding", "no_response", "groaning"])

    severity = "LOW"
    if fall_prob > 0.8:
        severity = "HIGH"
    elif fall_prob > 0.5:
        severity = "MEDIUM"

    return (
        f"Fall Detection Analysis for Patient[{patient_id}] at "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n"
        f"  Fall probability: {fall_prob:.0%}\n"
        f"  Impact force: {impact_force}g (threshold: 3.0g)\n"
        f"  Camera confirmation: {'Fall visible' if camera_confirm else 'Inconclusive'}\n"
        f"  Patient response: {patient_response}\n"
        f"  Severity assessment: {severity}\n"
        f"  Recommended action: "
        + ("IMMEDIATE EMERGENCY RESPONSE" if severity == "HIGH"
           else "Send caregiver to check" if severity == "MEDIUM"
           else "Monitor and log incident")
    )


def call_ambulance(patient_id: str, patient_address: str = "") -> str:
    """Call emergency medical services for a patient. Returns dispatch confirmation and estimated arrival time."""
    eta = random.randint(5, 25)
    dispatch_id = f"EMS-{random.randint(10000, 99999)}"

    return (
        f"🚑 EMERGENCY DISPATCH CONFIRMED\n"
        f"  Dispatch ID: {dispatch_id}\n"
        f"  Patient: {patient_id}\n"
        f"  Location: {patient_address or 'Address on file'}\n"
        f"  Estimated arrival: {eta} minutes\n"
        f"  Status: Ambulance en route\n"
        f"\n⚠ IMPORTANT: Keep phone line open. Do not move patient unless in immediate danger."
    )


def notify_emergency_contacts(patient_id: str, message: str) -> str:
    """Send emergency notification to all registered emergency contacts via SMS and phone call."""
    contacts = [
        {"name": "Li Wei (son)", "relation": "Primary contact", "notified": True},
        {"name": "Li Fang (daughter)", "relation": "Secondary contact", "notified": True},
        {"name": "Dr. Zhang (physician)", "relation": "Healthcare provider", "notified": True},
    ]

    lines = [f"📱 Emergency notification sent for Patient[{patient_id}]:", f"  Message: {message}", ""]
    for c in contacts:
        method = random.choice(["SMS", "Phone call", "SMS + Phone call"])
        lines.append(f"  {c['name']} ({c['relation']}): {method} – Delivered")

    return "\n".join(lines)


def get_patient_location(patient_id: str) -> str:
    """Get the current GPS location of the patient. Returns address and coordinates."""
    locations = {
        "P001": "Room 302, Building A, Sunshine Senior Care, 88 Heping Rd, Beijing",
        "P002": "Room 108, Building B, Sunshine Senior Care, 88 Heping Rd, Beijing",
    }
    loc = locations.get(patient_id, f"Patient[{patient_id}] – Location data unavailable. Last known: Main building.")
    return (
        f"Patient[{patient_id}] Location:\n"
        f"  Address: {loc}\n"
        f"  Coordinates: {39.9 + random.random() * 0.01:.4f}, {116.3 + random.random() * 0.01:.4f}\n"
        f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"  Indoor zone: Living area" if "Room" in loc else f"  Indoor zone: Common area"
    )
