from .models import ArchitectureIR


def json_schema() -> dict:
    return ArchitectureIR.model_json_schema()
