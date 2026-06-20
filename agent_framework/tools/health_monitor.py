"""
Health Monitoring Tools
---
Mock sensors for vital signs monitoring.
In production, these would connect to real wearable/IoT devices.

Simulated data follows realistic ranges for elderly patients:
- Heart rate: 50-120 bpm (normal 60-100)
- Blood pressure: 90-180 systolic
- SpO2: 88-100%
- Temperature: 35.5-39.0°C
- Blood glucose: 3.9-15.0 mmol/L
"""

import random
import time
from datetime import datetime


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_vital_signs(patient_id: str) -> str:
    """Read current vital signs from wearable sensors for a patient. Returns heart rate, blood pressure, SpO2, temperature, glucose."""
    heart_rate = random.randint(55, 115)
    systolic = random.randint(100, 175)
    diastolic = random.randint(60, 100)
    spo2 = random.randint(88, 100)
    temp = round(random.uniform(35.5, 38.8), 1)
    glucose = round(random.uniform(4.0, 14.0), 1)

    # Flag abnormal values
    flags = []
    if heart_rate > 100:
        flags.append(f"⚠ HIGH heart rate: {heart_rate} bpm (normal: 60-100)")
    elif heart_rate < 60:
        flags.append(f"⚠ LOW heart rate: {heart_rate} bpm (normal: 60-100)")

    if systolic > 140:
        flags.append(f"⚠ HIGH blood pressure: {systolic}/{diastolic}")
    elif systolic < 90:
        flags.append(f"⚠ LOW blood pressure: {systolic}/{diastolic}")

    if spo2 < 92:
        flags.append(f"🔴 CRITICAL SpO2: {spo2}%")

    if temp > 37.5:
        flags.append(f"⚠ FEVER: {temp}°C")
    elif temp < 36.0:
        flags.append(f"⚠ LOW temperature: {temp}°C")

    if glucose > 11.0:
        flags.append(f"⚠ HIGH glucose: {glucose} mmol/L")
    elif glucose < 4.0:
        flags.append(f"⚠ LOW glucose: {glucose} mmol/L")

    result = (
        f"Vital Signs for Patient[{patient_id}] at {_now()}:\n"
        f"  Heart Rate: {heart_rate} bpm\n"
        f"  Blood Pressure: {systolic}/{diastolic} mmHg\n"
        f"  SpO2: {spo2}%\n"
        f"  Temperature: {temp}°C\n"
        f"  Blood Glucose: {glucose} mmol/L\n"
    )
    if flags:
        result += "\nAlerts:\n" + "\n".join(f"  {f}" for f in flags)
    else:
        result += "\nAll vital signs within normal range."

    return result


def get_heart_rate_history(patient_id: str, hours: int = 24) -> str:
    """Get heart rate history for the past N hours. Returns hourly averages."""
    data = []
    now_ts = int(time.time())
    for h in range(hours):
        ts = now_ts - (hours - h) * 3600
        hr = random.randint(58, 108)
        dt = datetime.fromtimestamp(ts).strftime("%H:%M")
        data.append(f"  {dt}: {hr} bpm")

    return (
        f"Heart Rate History for Patient[{patient_id}] (last {hours}h):\n"
        + "\n".join(data)
    )


def check_sleep_status(patient_id: str) -> str:
    """Check if the patient is currently sleeping based on motion sensors and time."""
    hour = datetime.now().hour
    motion = random.choice([True, False])

    is_sleep_time = hour < 6 or hour > 22

    if is_sleep_time and not motion:
        status = "Likely sleeping (nighttime, no motion detected)"
    elif motion:
        status = "Awake and active (motion detected)"
    else:
        status = "Possibly resting (daytime, no motion)"

    return (
        f"Sleep Status for Patient[{patient_id}] at {_now()}:\n"
        f"  Time: {hour}:00\n"
        f"  Motion detected: {motion}\n"
        f"  Assessment: {status}"
    )
