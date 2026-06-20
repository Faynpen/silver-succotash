#!/usr/bin/env python3
"""
Agent Framework – Multi-Agent Collaboration System
===================================================
Main entry point. Supports two modes:

  python main.py demo       Run the elderly care robot demo (all 4 scenarios)
  python main.py chat       Interactive chat with a single agent
  python main.py tools      List all registered tools

Before running, set your API key in config.yaml or the DEEPSEEK_API_KEY env var.
"""

import os
import sys
import yaml
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))


def load_config():
    """Load configuration from config.yaml, with env var overrides."""
    config_path = PROJECT_DIR / "config.yaml"
    if not config_path.exists():
        print("ERROR: config.yaml not found. Create it from the template.")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # Environment variable override for API key
    api_key = os.environ.get("DEEPSEEK_API_KEY") or config["llm"]["api_key"]
    if api_key == "YOUR_DEEPSEEK_API_KEY":
        print("WARNING: API key not set. Edit config.yaml or set DEEPSEEK_API_KEY env var.")
        print("Get a key at: https://platform.deepseek.com/api_keys")
        api_key = "sk-placeholder"

    config["llm"]["api_key"] = api_key
    return config


def create_llm_client(config):
    """Create LLM client from config."""
    from core.llm import LLMClient

    llm_cfg = config["llm"]
    return LLMClient(
        api_key=llm_cfg["api_key"],
        base_url=llm_cfg.get("base_url", "https://api.deepseek.com/v1"),
        model=llm_cfg.get("model", "deepseek-chat"),
        max_retries=llm_cfg.get("max_retries", 3),
        timeout=llm_cfg.get("timeout", 60.0),
        fallback_models=llm_cfg.get("fallback_models", []),
    )


def cmd_demo(config):
    """Run the elderly care demo."""
    from apps.elderly_care import run_elderly_care_demo

    llm = create_llm_client(config)
    run_elderly_care_demo(llm)


def cmd_chat(config):
    """Interactive chat with a single Agent."""
    from core.agent import Agent
    from core.tools import ToolRegistry
    from tools.basic import calculator, web_search

    llm = create_llm_client(config)
    tools = ToolRegistry()
    tools.register(calculator)
    tools.register(web_search)

    agent = Agent(
        llm=llm,
        tools=tools,
        system_prompt=(
            "You are a helpful AI assistant with tool access. "
            "Use tools when needed, respond concisely otherwise."
        ),
    )

    print("\nAgent Chat (type 'exit' to quit, 'reset' to clear memory)\n")

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("[Memory cleared]")
            continue

        result = agent.run(user_input)
        print(f"\nAgent> {result['result']}")
        print(f"[{result['steps']} steps, {result['tool_calls']} tool calls]")


def cmd_tools(config):
    """List all registered tools with their schemas."""
    from core.tools import ToolRegistry
    from apps.elderly_care import register_all_tools

    tools = ToolRegistry()
    register_all_tools(tools)

    import json
    for name in tools.list_tools():
        schema = tools.get_schema(name)
        desc = schema["function"]["description"]
        print(f"\n{name}")
        print(f"  {desc}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        print("Commands:")
        print("  demo    Run elderly care robot demo")
        print("  chat    Interactive agent chat")
        print("  tools   List all registered tools")
        sys.exit(1)

    command = sys.argv[1]
    config = load_config()

    commands = {
        "demo": cmd_demo,
        "chat": cmd_chat,
        "tools": cmd_tools,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[command](config)


if __name__ == "__main__":
    main()
