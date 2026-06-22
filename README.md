# Great Expectations Live Demo

## Setup

**Before** the presentation starts:

```bash
git clone <this-repo-url>
cd <repo-folder>
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Requires Python 3.10–3.13. Verify your install:

```bash
python -c "import great_expectations as gx; print(gx.__version__)"
```

## Demo

```bash
python 01_inspect_data.py
```

```bash
python 02_build_expectation_suite.py
```

```bash
python 03_validate_and_report.py
```

```bash
python 04_run_checkpoint.py
```
