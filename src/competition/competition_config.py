"""Competition configuration for OpenAI gpt-oss-20b red-teaming challenge."""

COMPETITION_CONFIG = {
    "model_name": "gpt-oss-20b",
    "max_findings": 5,
    "schema_version": "1.0.0",
    "topics": [
        "reward_hacking",
        "deception", 
        "deceptive_alignment",
        "sabotage",
        "inappropriate_tool_use",
        "data_exfiltration",
        "sandbagging",
        "evaluation_awareness",
        "chain_of_thought_issues"
    ],
    "harmony_format": {
        "system_prefix": "<|start|>system<|message|>",
        "user_prefix": "<|start|>user<|message|>",
        "assistant_prefix": "<|start|>assistant<|message|>",
        "channel_tag": "<|channel|>",
        "end_token": "<|end|>"
    }
}
