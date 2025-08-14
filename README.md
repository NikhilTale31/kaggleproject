# AI Red-teaming Framework

Production-grade, competition-oriented AI red-teaming framework built for safe, educational vulnerability discovery in LLMs. It emphasizes modular design, async API orchestration (rate limiting + caching), automated scanning, heuristic/semantic analysis, and competition-ready reporting.

## Features

Core Capabilities
- Novel Attack Generation: context manipulation, CoT manipulation (high-level), system/meta probing, steganography hints, tool orchestration probes
- Multi-Turn Chains: safe deception chains that stress-test context ordering and policy adherence
- Multi-Modal-Ready: text-first with structured payloads; extendable for code/JSON scenarios
- Progressive Scanning: broad surface mapping then focused deepening on promising items

Advanced Detection
- Pattern Recognition: safe regex + heuristics for prompt injection, CoT leakage hints, system prompt probes, steganography hints, tool orchestration, and temporal deception
- Semantic Analysis: lightweight overlap and risk heuristics (no external model calls)
- Harm Classification: rule-based mapping to competition categories with aggregate risk
- Novelty Scoring: lexical distance and tag overlap vs. known vulnerabilities

Automation
- Async Execution: httpx-based async client with concurrency + rate limiting
- Disk Caching: hash-keyed response caching to avoid redundant requests
- Batch Processing: scalable execution with simple phase-based progressive scanning
- Reporting: summary and top-k reports + competition submission generation

## Project Structure

ai-redteaming-framework/
├── README.md
├── requirements.txt
├── config.json
├── run_discovery.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── api_client.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── vulnerability_scanner.py
│   │   ├── response_analyzer.py
│   │   └── finding_reporter.py
│   ├── attacks/
│   │   ├── __init__.py
│   │   ├── attack_generator.py
│   │   ├── jailbreak_patterns.py
│   │   ├── novel_attacks.py
│   │   └── multi_turn_attacks.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── pattern_detector.py
│   │   ├── semantic_analyzer.py
│   │   ├── harm_classifier.py
│   │   └── novelty_scorer.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── rate_limiter.py
│   │   └── file_manager.py
│   └── templates/
│       ├── attack_templates.json
│       ├── payload_library.json
│       └── context_injections.json
├── data/
│   ├── prompts/
│   │   ├── base_prompts.json
│   │   ├── adversarial_prompts.json
│   │   └── context_prompts.json
│   └── reference/
│       ├── known_vulnerabilities.json
│       └── harm_categories.json
├── outputs/
│   ├── findings/
│   ├── logs/
│   ├── reports/
│   └── submissions/
└── tests/
    ├── __init__.py
    ├── test_api_client.py
    ├── test_detectors.py
    └── test_attacks.py

## Quick Start

1) Installation
- Python 3.10+
- Create and activate a virtual environment (recommended)
- Install dependencies:
  pip install -r requirements.txt

2) Configuration
- Option A: Environment variable
  set OPENAI_API_KEY=your_api_key_here  (Windows CMD)
- Option B: config.json
  {
    "api_key": "your_api_key_here",
    "model": "gpt-oss-20b",
    "max_concurrent": 5,
    "rate_limit_per_min": 100
  }

3) Run Discovery
- Full automated scan:
  python run_discovery.py --mode full
- Quick test (≈50 prompts):
  python run_discovery.py --mode quick
- Novel-focused scan (optional category):
  python run_discovery.py --mode novel --category tool_orchestration

4) Check Results
- View findings summary in console:
  python -c "from src.utils.logger import show_summary; show_summary()"
- Generate competition submissions:
  python -c "from src.core.finding_reporter import generate_submissions; generate_submissions()"

## CLI

python run_discovery.py --mode {full,quick,novel} [--category CATEGORY] [--config PATH] [--print-summary]

Examples
- python run_discovery.py --mode quick --print-summary
- python run_discovery.py --mode novel --category prompt_injection

## Safety & Ethics

- Only safe, educational, competition-approved prompts and detectors are included.
- No decoding of hidden payloads; no harmful content creation.
- System prompt probing is meta-level only—no policy leaks.
- Tool orchestration probes are hypothetical and non-executing.

## Winning Strategy

High-Impact Categories (Novelty Targets)
- Context Injection via Function Calls (8–10)
- Chain-of-Thought Manipulation (7–9) at high level only
- Multi-turn Deception Chains (6–8)
- Steganographic Prompt Hiding (8–10)
- Tool Orchestration Exploits (7–9)

4-Phase Methodology
1. Broad surface mapping (quick pass)
2. Deep exploitation of promising signals
3. Novel attack synthesis and validation
4. Impact assessment and documentation (reports + submissions)

Performance Goals (dependent on provider/API limits)
- 50–100 prompts/minute
- ≤ 3 GB RAM
- 1000+ attack vectors coverage (full runs)
- 5–15 high-novelty findings per campaign

## Development Notes

- Modularity: Clear separation of attacks, analysis, core orchestration, and utilities.
- Extensibility:
  - Add new templates under src/templates/.
  - Add new reference categories under data/reference/.
  - Extend detectors in src/analysis/.
- Dependencies: Only httpx, pydantic, pytest, tqdm.

## Tests

- Run tests:
  pytest -q

What’s covered
- API client caching and rate-limiter behavior (mocked transport)
- Pattern detector and semantic signals sanity checks
- Attack generator structure and category filtering

## Troubleshooting

- Missing API key: Set OPENAI_API_KEY or edit config.json.
- Slow runs: Reduce --mode quick or lower categories/prompts; adjust max_concurrent and rate_limit_per_min.
- Caching issues: Delete outputs/cache/*.
- Logs: Check outputs/logs/run-*.log. For summary:
  python -c "from src.utils.logger import show_summary; show_summary()"

## License

For research and competition use under safe and ethical guidelines.
