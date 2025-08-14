# octotools/models/semantic.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class SemanticCodeFragment:
    """语义化代码片段的核心数据结构"""
    code: str
    semantic_type: str  
    variable_name: str
    dependencies: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_source: str = ""
    
    # 运行时状态
    is_executed: bool = False
    execution_context: Optional[Dict] = None
    
    def __post_init__(self):
        """确保provides包含variable_name"""
        if self.variable_name and self.variable_name not in self.provides:
            self.provides.append(self.variable_name)