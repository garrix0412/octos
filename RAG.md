## RAG知识库构建方案

### 设计原则

RAG知识库就像一本Julia的技术手册，程序员需要查什么函数怎么用时，翻开就能找到。但这本手册只告诉你"这个函数是什么"，不告诉你"你应该用它来实现某个算法"。

### 知识库内容分类

#### 1. ITensors.jl API举例子

```json
{
  "api_name": "productMPS",
  "library": "ITensors",
  "signature": "productMPS(sites::Vector{<:Index}, states::Vector{String}) -> MPS",
  "description": "Create an MPS initialized as a product state",
  "parameters": {
    "sites": "Vector of site indices defining the Hilbert space",
    "states": "Vector of state labels like 'Up', 'Dn', '0', '1'"
  },
  "returns": "An MPS object in the specified product state",
  "example": "psi = productMPS(sites, [\"Up\", \"Up\", \"Dn\", \"Up\"])",
  "usage_context": "Initial state preparation, quantum state initialization",
  "related_apis": ["randomMPS", "random_mps", "siteinds"],
  "common_pitfalls": "State labels must match the physical dimension of sites"
}
```


```json
{
  "api_name": "OpSum",
  "library": "ITensors",
  "signature": "OpSum() -> OpSum",
  "description": "Create an operator sum for building MPOs",
  "parameters": {},
  "returns": "Empty OpSum object to which terms can be added",
  "example": "os = OpSum(); os += \"Sz\", 1, \"Sz\", 2",
  "usage_context": "Hamiltonian construction, operator building",
  "related_apis": ["MPO", "add!", "splitblocks"],
  "common_pitfalls": "Terms must be added before conversion to MPO"
}
```


```json
{
  "api_name": "op",
  "library": "ITensors",
  "signature": "op(opname::String, site::Index...) -> ITensor",
  "description": "Create a quantum gate or operator as an ITensor",
  "parameters": {
    "opname": "Name of the operator like 'X', 'Y', 'Z', 'H'",
    "site": "Site indices where operator acts"
  },
  "returns": "ITensor representing the operator",
  "example": "gate = op(\"X\", sites[1])",
  "usage_context": "Gate application, operator construction",
  "related_apis": ["apply", "replacetags!", "prime"],
  "common_pitfalls": "Operator name must be defined for the site type"
}
```

#### 2. OptimKit.jl API文档举例

```json
{
  "api_name": "optimize",
  "library": "OptimKit",
  "signature": "optimize(f, x0, algorithm; kwargs...) -> x_opt, f_opt, info",
  "description": "Minimize a scalar function using specified algorithm",
  "parameters": {
    "f": "Function to minimize, returns (value, gradient)",
    "x0": "Initial parameter vector",
    "algorithm": "Optimization algorithm like LBFGS()"
  },
  "returns": "Optimized parameters, final value, optimization info",
  "example": "x_opt, f_min, _ = optimize(loss, params, LBFGS())",
  "usage_context": "Parameter optimization, variational algorithms",
  "related_apis": ["LBFGS", "GradientDescent", "ConjugateGradient"],
  "common_pitfalls": "Function must return both value and gradient for gradient-based methods"
}
```

### 查询接口设计

Agent 2和Agent 3查询RAG的方式不同：

**Agent 2的查询**（宏观）
```
Query: "Julia quantum state representations"
Returns: ["MPS (ITensors)", "State vectors (QuantumOptics.jl)", "Density matrices"]

Query: "Julia optimization libraries"
Returns: ["OptimKit.jl - specialized for quantum", "Optim.jl - general purpose"]
```

**Agent 3的查询**（具体）
```
Query: "productMPS function signature"
Returns: Complete API entry with parameters and example

Query: "How to apply gate to MPS"
Returns: apply! function documentation
```

### 关键内容范围

**必须包含**：
- ITensors.jl核心API（MPS, MPO, sites, gates）
- OptimKit.jl优化器接口
- LinearAlgebra基础操作
- 基本的Julia语法特性（broadcasting, type system）

**不包含**：
- "如何用MPS实现VQE"这种策略指导
- Python到Julia的对应关系
- 算法实现模板

### 更新维护策略

当Julia库更新时：
1. 更新API签名和参数
2. 添加新增的函数
3. 标记废弃的API
4. 保持向后兼容的记录

这样Agent即使面对新版本的库，也能正确工作。

### 示例：一个完整的API条目

```json
{
  "api_name": "inner",
  "library": "ITensors",
  "signature": "inner(psi::MPS, H::MPO, phi::MPS) -> Complex",
  "description": "Compute matrix element <psi|H|phi>",
  "parameters": {
    "psi": "Left MPS (bra)",
    "H": "MPO operator", 
    "phi": "Right MPS (ket)"
  },
  "returns": "Complex number representing the expectation value",
  "example": "energy = real(inner(psi, H, psi))",
  "usage_context": "Expectation values, energy calculations",
  "related_apis": ["expect", "correlation_matrix", "norm"],
  "common_pitfalls": "All three arguments must have matching site indices"
}
```