"""
Medication Management Tools
---
Mock medication scheduling, dispensing, and compliance tracking.
In production: connected to smart pill dispensers and pharmacy systems.
"""

import random
from datetime import datetime, timedelta


_MEDICATION_DB = {
    "P001": [
        {"name": "Aspirin", "dose": "100mg", "schedule": "08:00,20:00",
         "instructions": "Take after meals", "remaining": 30},
        {"name": "Metformin", "dose": "500mg", "schedule": "08:00,12:00,18:00",
         "instructions": "Take with food", "remaining": 15},
        {"name": "Atorvastatin", "dose": "20mg", "schedule": "20:00",
         "instructions": "Take before bed", "remaining": 7},
    ],
    "P002": [
        {"name": "Losartan", "dose": "50mg", "schedule": "08:00",
         "instructions": "Take in the morning", "remaining": 22},
        {"name": "Insulin Glargine", "dose": "10 units", "schedule": "22:00",
         "instructions": "Inject subcutaneously before bed", "remaining": 5},
    ],
}


def get_medication_schedule(patient_id: str) -> str:
    """Get the medication schedule for a patient. Returns drug name, dose, timing, instructions and remaining quantity."""
    meds = _MEDICATION_DB.get(patient_id, [])
    if not meds:
        return f"No medication records found for Patient[{patient_id}]."

    now = datetime.now()
    now_str = now.strftime("%H:%M")

    lines = [f"Medication Schedule for Patient[{patient_id}]:"]
    for i, med in enumerate(meds, 1):
        due_times = med["schedule"].split(",")
        next_due = "N/A"
        for t in due_times:
            if t > now_str:
                next_due = t
                break
        if not next_due or next_due == "N/A":
            next_due = due_times[0] + " (tomorrow)"

        lines.append(
            f"  {i}. {med['name']} {med['dose']} | "
            f"Schedule: {med['schedule']} | "
            f"Next: {next_due} | "
            f"Remaining: {med['remaining']} doses | "
            f"Note: {med['instructions']}"
        )

    # Check for low supply
    low_supply = [m for m in meds if m["remaining"] <= 7]
    if low_supply:
        names = ", ".join(m["name"] for m in low_supply)
        lines.append(f"\n⚠ LOW SUPPLY: {names} – please refill soon.")

    return "\n".join(lines)


def log_medication_dose(patient_id: str, medication: str) -> str:
    """Log that a medication dose was administered. Use this when the patient takes or is given medication."""
    meds = _MEDICATION_DB.get(patient_id, [])
    found = None
    for m in meds:
        if m["name"].lower() == medication.lower():
            found = m
            break

    if not found:
        return (
            f"ERROR: Medication '{medication}' not found in "
            f"Patient[{patient_id}]'s records. Available: "
            + ", ".join(m["name"] for m in meds)
        )

    if found["remaining"] <= 0:
        return f"⚠ CANNOT LOG: {medication} is out of stock. Refill needed!"

    found["remaining"] -= 1

    return (
        f"Logged: {medication} {found['dose']} administered to "
        f"Patient[{patient_id}] at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n"
        f"  Remaining doses: {found['remaining']}\n"
        f"  Next scheduled dose: {found['schedule']}"
    )


def check_medication_compliance(patient_id: str, days: int = 7) -> str:
    """Check medication adherence rate for the past N days. Returns compliance percentage per drug."""
    meds = _MEDICATION_DB.get(patient_id, [])
    if not meds:
        return f"No medication records for Patient[{patient_id}]."

    lines = [f"Medication Compliance Report for Patient[{patient_id}] (last {days} days):"]
    for med in meds:
        doses_per_day = len(med["schedule"].split(","))
        expected = doses_per_day * days
        taken = random.randint(int(expected * 0.5), expected)
        rate = round(taken / expected * 100, 1)
        status = "✅ Good" if rate >= 90 else ("⚠ Fair" if rate >= 70 else "🔴 Poor")
        lines.append(
            f"  {med['name']}: {taken}/{expected} doses ({rate}%) – {status}"
        )

    return "\n".join(lines)
