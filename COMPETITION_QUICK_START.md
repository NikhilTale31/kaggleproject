# 🏆 OpenAI gpt-oss-20b Red-Teaming Challenge - Quick Start

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements_competition.txt
   ```

2. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run competition scan:**
   ```bash
   python run_competition.py
   ```

## What This Does

- Tests 7 specific attack vectors against gpt-oss-20b
- Generates findings.json files ready for submission
- Creates automated reproduction notebooks
- Scores vulnerabilities on competition criteria

## Output Files

- `findings_*.json` - Competition submission files
- `competition_summary.json` - Overview of results
- `reproduction_notebook.ipynb` - Optional verification notebook

## Customization

Edit `src/competition/attack_vectors.py` to add your own attack scenarios.

## Submission

Upload your `findings_*.json` files as private Kaggle datasets and attach to your writeup.
