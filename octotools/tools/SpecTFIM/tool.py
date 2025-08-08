# octotools/tools/spec_tfim/tool.py
from octotools.tools.base import BaseTool

class SpecTFIM_Tool(BaseTool):
    require_llm_engine = False

    def __init__(self):
        super().__init__(
            tool_name="SpecTFIM",
            tool_description="Normalize TFIM problem spec (sites=qubit) with controlled defaults.",
            tool_version="0.1.0",
            input_types={
                "model": "str - must be 'TFIM'",
                "N": "int - number of qubits/spins",
                "boundary": "str - 'open'|'periodic' (optional)",
                "hx": "float - transverse field (optional)",
                "J": "float - coupling (optional)",
                "sites": "str - must be 'qubit' (optional)",
                "dtype": "str - 'float64'|'float32' (optional)"
            },
            output_type="dict - normalized spec IR",
            demo_commands=[{
                "command": "tool.execute(model='TFIM', N=8)",
                "description": "Build a minimal TFIM spec with defaults"
            }],
            user_metadata={
                "routing": {"task_type": "SpinVQE", "models_supported": ["TFIM"]},
                "defaults": {"N": 8, "boundary": "open", "J": 1.0, "hx": 0.5, "sites": "qubit", "dtype": "float64"},
                "notes": "Schema-only tool. No heavy deps in __init__."
            }
        )

    def execute(self, **kwargs):
        N = int(kwargs.get("N", 8))
        spec = {
            "Model": "TFIM",
            "N": N,
            "Boundary": kwargs.get("boundary", "open"),
            "Couplings": {"J": float(kwargs.get("J", 1.0)), "hx": float(kwargs.get("hx", 0.5))},
            "Sites": kwargs.get("sites", "qubit"),
            "DType": kwargs.get("dtype", "float64")
        }
        return {"SpecIR": spec, "warnings": []}

    def get_metadata(self):
        return super().get_metadata()