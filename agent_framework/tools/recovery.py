"""
Rehabilitation Training Tools
---
Tools for elderly rehabilitation scenario:
- Generate personalized rehab plans
- Check exercise safety based on vitals
- Log training sessions for progress tracking

In production, these would integrate with motion sensors,
pressure mats, and physical therapist review portals.
"""

import random
from datetime import datetime


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_rehab_plan(patient_id: str, condition: str = "general") -> str:
    """Generate a personalized rehabilitation training plan for a patient. Condition can be: general, post_surgery, fall_recovery, joint_pain, stroke_recovery."""
    plans = {
        "general": [
            ("肩颈活动", "坐姿耸肩 2×10 次，缓慢转动肩部"),
            ("下肢拉伸", "坐姿抬腿 2×8 次/腿，每动作保持 5 秒"),
            ("平衡训练", "扶椅背单腿站立 3×10 秒/腿"),
            ("呼吸练习", "腹式呼吸 5 分钟，深吸慢呼"),
        ],
        "post_surgery": [
            ("床上踝泵", "勾脚-绷脚交替 3×15 次，每小时 1 组"),
            ("渐进式坐起", "从 30°逐步过渡到 90°坐姿 2×5 分钟"),
            ("辅助行走", "助行器辅助慢走 3×3 分钟，间隔休息"),
            ("上肢活动", "握力球训练 2×10 次，弹力带轻度拉伸"),
        ],
        "fall_recovery": [
            ("核心激活", "仰卧屈膝 2×8 次，骨盆轻微抬升"),
            ("坐站转移", "扶椅子从坐到站 3×5 次，慢速完成"),
            ("步态训练", "视线正前方慢走 2×5 分钟，脚跟着地"),
            ("柔韧恢复", "坐姿前屈 2×6 次，缓慢幅度适可而止"),
        ],
        "joint_pain": [
            ("温和关节活动", "手指开合 3×10 次，手腕轻旋"),
            ("膝关节零负重", "坐姿伸膝 2×8 次/腿，5 秒停顿"),
            ("水中运动", "温水泳池缓慢行走 10 分钟（如有条件）"),
            ("热敷后拉伸", "热敷 15 分钟后进行轻度关节拉伸"),
        ],
        "stroke_recovery": [
            ("患侧激活", "镜子疗法 5 分钟，健侧带动患侧视觉反馈"),
            ("语言训练", "跟读常见词语 3 组，每词重复 5 次"),
            ("精细动作", "捡豆训练 2×10 次，拇食指对握"),
            ("坐姿平衡", "无靠背坐姿 3×2 分钟，重心转移练习"),
        ],
    }

    selected = plans.get(condition, plans["general"])
    plan_lines = [
        f"Rehab Plan for Patient[{patient_id}] | Condition: {condition}",
        f"Generated at {_now()}",
        "",
        "Daily Schedule:",
    ]
    for i, (name, instruction) in enumerate(selected, 1):
        plan_lines.append(
            f"  {i}. {name} — {instruction}"
        )

    # Add safety notes
    plan_lines.append("")
    plan_lines.append("Safety Notes:")
    plan_lines.append(
        "  • Stop immediately if pain, dizziness, or shortness of breath occurs"
    )
    plan_lines.append(
        "  • Keep hydration within reach during exercise"
    )
    plan_lines.append(
        "  • Use mobility aids as prescribed; do not skip them"
    )

    return "\n".join(plan_lines)


def check_exercise_safety(patient_id: str, heart_rate: int = 0,
                          blood_pressure_systolic: int = 0,
                          spo2: int = 0) -> str:
    """Check if it is safe for the patient to perform rehabilitation exercises. Requires current vital signs."""
    warnings = []

    if heart_rate == 0 and blood_pressure_systolic == 0:
        # Simulated check
        heart_rate = random.randint(60, 130)
        blood_pressure_systolic = random.randint(95, 180)
        spo2 = random.randint(88, 100)

    if heart_rate > 110:
        warnings.append("Heart rate too high for exercise (> 110 bpm)")
    elif heart_rate < 50:
        warnings.append("Heart rate too low for exercise (< 50 bpm)")

    if blood_pressure_systolic > 160:
        warnings.append(
            "Blood pressure critically high (> 160 systolic) — "
            "defer exercise, notify nurse"
        )
    elif blood_pressure_systolic > 145:
        warnings.append(
            "Blood pressure elevated (> 145 systolic) — "
            "light activity only, reduce intensity by 50%"
        )

    if spo2 < 92:
        warnings.append(
            "SpO2 below safe threshold (< 92%) — "
            "do NOT exercise, administer oxygen, notify doctor"
        )

    safe = len(warnings) == 0
    status = "SAFE to proceed with rehab exercises" if safe else \
             "EXERCISE ADJUSTMENT REQUIRED — see warnings below"

    result = (
        f"Exercise Safety Check for Patient[{patient_id}] at {_now()}:\n"
        f"  Heart Rate: {heart_rate} bpm\n"
        f"  Blood Pressure: {blood_pressure_systolic} mmHg (systolic)\n"
        f"  SpO2: {spo2}%\n"
        f"\nAssessment: {status}"
    )
    if warnings:
        result += f"\n\nWarnings ({len(warnings)}):\n"
        for w in warnings:
            result += f"  • {w}"
    else:
        result += "\nNo safety concerns detected."

    return result


def log_training_session(patient_id: str, exercise_name: str,
                         duration_min: int = 0, completed: bool = True,
                         pain_level: int = 0, notes: str = "") -> str:
    """Log a completed rehabilitation training session. Pain level: 0=none, 10=severe."""
    if duration_min == 0:
        duration_min = random.randint(3, 20)
    if pain_level == 0:
        pain_level = random.randint(0, 3)

    status = "COMPLETED" if completed else "PARTIAL (stopped early)"

    if pain_level >= 7:
        flag = "⚠ HIGH PAIN — escalate to physiotherapist"
    elif pain_level >= 4:
        flag = "Moderate discomfort — monitor next session"
    else:
        flag = "Comfortable — maintain current intensity"

    return (
        f"Training Session Log for Patient[{patient_id}] at {_now()}:\n"
        f"  Exercise: {exercise_name}\n"
        f"  Duration: {duration_min} minutes\n"
        f"  Status: {status}\n"
        f"  Pain Level: {pain_level}/10\n"
        f"  Flag: {flag}"
        + (f"\n  Notes: {notes}" if notes else "")
    )


def get_progress_summary(patient_id: str) -> str:
    """Get the rehabilitation progress summary for a patient over the past week."""
    sessions_completed = random.randint(8, 14)
    sessions_planned = 14
    avg_pain = round(random.uniform(1.0, 4.5), 1)
    improvement = random.choice([
        "Mild improvement — ROM increased by approximately 10°",
        "Steady progress — endurance up ~20%, pain decreasing",
        "Plateaued — no significant change this week; consider adjusting plan",
        "Good response — gait symmetry improving, less reliance on mobility aid",
    ])

    return (
        f"Rehab Progress Summary for Patient[{patient_id}]:\n"
        f"  Period: Last 7 days\n"
        f"  Sessions completed: {sessions_completed}/{sessions_planned}\n"
        f"  Average pain level: {avg_pain}/10\n"
        f"  Assessment: {improvement}"
    )
