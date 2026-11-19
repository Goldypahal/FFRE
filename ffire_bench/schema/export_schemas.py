"""
Utility script to export JSON schemas from Pydantic models.
"""

import json
from pathlib import Path
from ffire_bench.schema.models import Case, PredictionBundle


def export_json_schemas(output_dir: Path = None):
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent

    case_schema = Case.model_json_schema()
    bundle_schema = PredictionBundle.model_json_schema()

    case_file = output_dir / "case.schema.json"
    bundle_file = output_dir / "prediction_bundle.schema.json"

    with open(case_file, "w", encoding="utf-8") as f:
        json.dump(case_schema, f, indent=2)

    with open(bundle_file, "w", encoding="utf-8") as f:
        json.dump(bundle_schema, f, indent=2)

    print(f"Exported JSON schemas to:\n  - {case_file}\n  - {bundle_file}")


if __name__ == "__main__":
    export_json_schemas()
