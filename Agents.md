### RAG知识库构建

**设计原则**
- 只存储中立的技术文档
- 不包含任何"应该怎么用"的策略指导
- 保持信息的纯净性

**知识库内容结构**

每个API条目格式：
```json
{
  "api_name": "productMPS",
  "library": "ITensors",
  "signature": "productMPS(sites::Vector{Index}, states::Vector{String})",
  "description": "Creates an MPS in a product state configuration",
  "parameters": {
    "sites": "Vector of site indices",
    "states": "Vector of state labels like 'Up', 'Dn'"
  },
  "returns": "MPS object representing the product state",
  "example": "psi = productMPS(sites, [\"Up\", \"Up\", \"Dn\", \"Up\"])",
  "common_pitfalls": "State labels must match the site types",
  "related_apis": ["randomMPS", "MPO", "inner"]
}
```

**更新机制**
- 当Julia库版本更新时，只更新知识库
- Agent逻辑不需要改动
- 保证系统的长期可维护性

### 关键实现约束

**必须遵守的原则**

1. **零硬编码**：不能有任何"if Python用了X则Julia用Y"的规则
2. **理解驱动**：所有决策基于理解，不是基于模板
3. **物理优先**：物理等价性高于代码相似性
4. **专业标准**：生成的代码必须像人类专家写的

**质量保证要点**

- 每个Agent的输出都要有明确的格式要求
- 关键信息不能在传递中丢失
- 测试必须验证物理等价性，不只是代码运行
- 协调器要能识别并处理各种异常情况

### 开发实施指南

按这个规划实施时，要确保：

1. Agent 1的三层分析真正并行且独立
2. Agent 2查询RAG但不依赖RAG提供策略
3. Agent 3的"边查边写"是真实的迭代过程
4. 测试Agent的物理验证要严格
5. 协调器要有清晰的判断标准和处理流程

这个规划是否足够清晰和具体？是否还有需要细化的部分？