#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.

This file loads helper functions from the template and generation script
so they're available to all test modules.
"""

import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools"))

# Load template module - extract only Python code before Jinja2 template
template_file = project_root / "tools" / "templates" / "universal_dependencies.tmpl"

# Read and extract Python code (before the class definition which contains Jinja2)
with open(template_file, "r", encoding="utf-8") as f:
    template_lines = f.readlines()

# Extract lines until we hit the Jinja2 template section
# The template starts with _CITATION at around line 262
python_code_lines = []
for line in template_lines:
    # Stop when we reach the Jinja2 template section
    if line.strip().startswith("_CITATION") or line.strip().startswith("_DESCRIPTION"):
        break
    python_code_lines.append(line)

python_code = "".join(python_code_lines)

# Add necessary imports that the functions depend on
python_code = "import sys\nfrom pathlib import Path\nfrom io import StringIO\nfrom typing import Dict, Optional\n" + python_code

# Create a module namespace and execute the Python code
import types
ud_module = types.ModuleType("ud_template")
ud_module.__file__ = str(template_file)

# Execute Python code in the module's namespace
exec(python_code, ud_module.__dict__)

# Make helper functions available globally to tests
sys.modules["ud_template"] = ud_module

# Load generation script functions
gen_script = project_root / "tools" / "04_generate_parquet.py"
spec = importlib.util.spec_from_file_location("generate_parquet", gen_script)
generate_parquet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_parquet)

sys.modules["generate_parquet"] = generate_parquet
