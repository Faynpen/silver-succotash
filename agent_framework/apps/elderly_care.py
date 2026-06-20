"""
Elderly Care Robot – Demo Application
---
Demonstrates the multi-agent framework in 4 healthcare scenarios:

1. Health Monitoring: Check vitals, detect abnormalities, generate reports
2. Medication Management: Schedule, dispense, compliance tracking
3. Fall Detection & Emergency Response: Detect, assess, respond
4. Rehabilitation: Guide exercises, track progress, report to therapist

Each scenario runs through the Plan → Execute → Review pipeline,
showcasing the framework's safety-first design for medical applications.
"""

import json
from datetime import datetime

from orchestrator import Orchestrator
from core.llm import LLMClient
from core.tools import ToolRegistry

# Import tool modules and register all functions
from tools.health_monitor import (
    get_vital_signs,
    get_heart_rate_history,
    check_sleep_status,
)
from tools.medication import (
    get_medication_schedule,
    log_medication_dose,
    check_medication_compliance,
)
from tools.fall_detection import (
    detect_fall,
    call_ambulance,
    notify_emergency_contacts,
    get_patient_location,
)
from tools.basic import calculator, web_search, control_environment


def register_all_tools(tools: ToolRegistry):
    """Register all IoT simulation tools."""
    # Health monitoring
    tools.register(get_vital_signs)
    tools.register(get_heart_rate_history)
    tools.register(check_sleep_status)

    # Medication
    tools.register(get_medication_schedule)
    tools.register(log_medication_dose)
    tools.register(check_medication_compliance)

    # Fall detection & emergency
    tools.register(detect_fall)
    tools.register(call_ambulance)
    tools.register(notify_emergency_contacts)
    tools.register(get_patient_location)

    # Basic utilities
    tools.register(calculator)
    tools.register(web_search)
    tools.register(control_environment)


SCENARIOS = {
    "1": {
        "name": "Health Monitoring",
        "description": "Check patient vitals, detect abnormalities",
        "prompt": (
            "Patient P001 (78-year-old male, history of hypertension and type 2 diabetes) "
            "is reporting dizziness. Please:\n"
            "1. Check his current vital signs\n"
            "2. Compare with recent history (last 6 hours)\n"
            "3. Assess if this requires immediate medical attention\n"
            "4. Generate a summary for the attending nurse"
        ),
    },
    "2": {
        "name": "Medication Management",
        "description": "Schedule, dispense, track compliance",
        "prompt": (
            "Patient P001 missed his morning medications (Aspirin and Metformin). "
            "It's now 11:00 AM. Please:\n"
            "1. Check his medication schedule\n"
            "2. Determine if it's safe to take the missed doses now\n"
            "3. Log the late doses if safe\n"
            "4. Check his overall compliance rate for the past week\n"
            "5. Alert the caregiver if compliance is below 85%"
        ),
    },
    "3": {
        "name": "Fall Detection & Emergency",
        "description": "Detect fall, assess severity, respond",
        "prompt": (
            "Patient P002 (82-year-old female) has triggered the fall detection sensor "
            "in her bathroom. She is not responding to the voice intercom. Please:\n"
            "1. Analyze the fall detection data\n"
            "2. Get her current location\n"
            "3. Assess the severity and determine if ambulance is needed\n"
            "4. If emergency: dispatch ambulance and notify all contacts\n"
            "5. Provide post-incident instructions for the family"
        ),
    },
    "4": {
        "name": "Rehabilitation Guidance",
        "description": "Guide exercises, track form, report progress",
        "prompt": (
            "Patient P001 is scheduled for post-hip-surgery rehabilitation exercises. "
            "His prescription: 3 sets of leg raises (15 reps each), "
            "2 sets of ankle pumps (20 reps each). Please:\n"
            "1. Retrieve his current vitals to ensure he's stable for exercise\n"
            "2. Guide through the rehabilitation routine step by step\n"
            "3. Generate a progress report for the physiotherapist\n"
            "4. Note any concerns about pain or difficulty"
        ),
    },
}


def run_elderly_care_demo(llm_client: LLMClient):
    """Run the elderly care robot multi-agent demo."""
    print("\n" + "=" * 60)
    print("  ELDERLY CARE ROBOT – Multi-Agent Decision System")
    print("=" * 60)
    print(f"  Model: {llm_client.model}")
    print(f"  Agent Mode: Plan → Execute → Review")
    print(f"  Scenarios: Health | Medication | Fall Emergency | Rehab")
    print("=" * 60)

    # Register tools
    tools = ToolRegistry()
    register_all_tools(tools)
    print(f"\n[System] {len(tools.list_tools())} tools registered:")
    for name in tools.list_tools():
        print(f"  - {name}")

    # Create orchestrator
    orchestrator = Orchestrator(
        llm=llm_client,
        tools=tools,
        storage_dir=".agent_memory",
        max_revise_rounds=3,
    )

    # Run each scenario
    for scenario_id, scenario in SCENARIOS.items():
        print(f"\n{'─' * 60}")
        print(f"  SCENARIO {scenario_id}: {scenario['name']}")
        print(f"  {scenario['description']}")
        print(f"{'─' * 60}")

        print(f"\n[User Input]\n{scenario['prompt']}\n")

        result = orchestrator.run(scenario['prompt'])

        # Show plan
        print(f"[Planner → {len(result['subtasks'])} subtasks]")
        for i, st in enumerate(result['subtasks'], 1):
            print(f"  {i}. {st}")

        # Show results
        print(f"\n{result['final_output']}")

        # Show review status
        print(f"\n[Review: {result['review_rounds']} round(s)]")

        # Show stats
        total_tool_calls = sum(
            r.get("tool_calls", 0) for r in result.get("results", [])
        )
        total_tokens = llm_client.total_tokens
        print(f"[Stats] Tool calls: {total_tool_calls} | "
              f"Tokens used: {total_tokens}")

    print(f"\n{'=' * 60}")
    print("  DEMO COMPLETE")
    print(f"  Total tokens consumed: {llm_client.total_tokens}")
    print(f"  Memory persisted to: .agent_memory/")
    print("=" * 60)
