## 量子代码智能转换系统 - Agent架构详细规划

### 整体架构

就像一个资深程序员接到任务时的工作方式，我们的系统通过几个专门的Agent来模拟这个过程。每个Agent就像程序员大脑中的不同思维模式。
系统由三个主Agent、一个测试助手、一个协调器和RAG知识库组成，模拟资深量子计算程序员的完整工作流程。

### Agent 1: 代码理解专家 - 设计说明

### 一、 Agent定位与模拟目标

#### 1\. 模拟对象：经验丰富的量子计算程序员

想象一位精通Python/Qiskit和Julia/ITensors的资深量子计算程序员。当他接到一个“将这份Python代码用Julia重写”的任务时，他不会直接开始逐行翻译。相反，他会经历一个先看整体结构，然后深入每个函数理解功能，最后整理出"要实现什么"和"用什么参数"的过程。他会怎么做？首先，他会通读一遍代码，搞清楚整体在干什么。然后深入每个函数，理解具体的实现细节。最后，他会在纸上列出一个清单："我需要在Julia中实现这些功能，参数是这些。"

Agent 1 的核心任务就是**完全模拟**这位专家的思维过程。

#### 2\. 工作方式：从宏观到微观的认知过程

这位专家的工作流程通常是：

1.  **快速浏览 (Skimming):** 首先，他会通读一遍代码，了解整体结构和目标。“哦，这是一个VQE算法，用来找TFIM模型的基态能量。主函数调用了哈密顿量构建和线路构建两个部分。有个main函数，调用了build_tfim_h建哈密顿量，tfim_hea造线路，然后跑VQE。”
2.  **深入理解 (Deep Dive):** 接着，他会逐个函数地精读，理解其内部的物理和算法逻辑。“`build_tfim_h`"这是在构建TFIM模型的哈密顿量，先加X项，每个量子比特一个，系数是-hx。然后加ZZ项，相邻的量子比特，系数是-j。"。`tfim_hea`"这是在造一个参数化线路。先给所有量子比特加H门初始化，然后重复几层，每层先做ZZ纠缠门（用CX-RZ-CX实现的），再做单比特的RX旋转。"，里面有个`_assign_edges_to_layers`的内部函数，"等等，这里有个内部函数，在做什么？哦，这是个贪心算法，把边分成几组，每组内的边可以同时执行因为不共享量子比特。这是个优化技巧，得记下来。
3.  **解构与规划 (Deconstruction & Planning):** 最后，他会在脑中或纸上形成一个清晰的“实现清单”。“Qiskit的`VQE`类在Julia里没有现成的，我需要自己实现优化循环。哈密顿量可以用MPO来表示。那个边分层算法的逻辑必须完整复现。所有参数值是n=4, hx=1.5...”

Agent 1 的设计完全遵循这个认知模型，确保其输出不仅是信息的罗列，而是一份可以直接用于代码重建的、充满洞察的“实现指南”。

#### 3\. 核心职责：回答关键问题

模拟程序员阅读和理解Python代码的过程，但不是表面理解，而是深入到"能够在另一种语言中重建"的程度，Agent 1 必须能准确回答以下问题：

  - **物理问题：** 这段代码在解决什么物理问题？（例如：横向场伊辛模型）
  - **核心算法：** 它使用了什么关键算法？（例如：变分量子本征求解器 VQE）
  - **关键参数：** 哪些是必须保留的核心参数？（例如：量子比特数 `n`，哈密顿量系数 `hx`, `j`）
  - **实现细节：** 有哪些隐藏的算法或优化技巧？（例如：并行化的边分层贪心算法）
  - **依赖解构：** 哪些部分是源语言的高度封装API，在新语言中需要被拆解实现？（例如：Qiskit的 `VQE` 类）

### 二、 工作核心：三层分析架构

为了系统化地实现上述目标，Agent 1 采用三层分析架构，每层对应程序员认知过程的一个阶段。

#### 第一层：结构扫描器 (AST分析)

**目的：** 获得代码的完整“地图”，对应程序员的“快速浏览”阶段。

**具体工作：**

1.  **函数识别：** 使用抽象语法树（AST）解析，列出所有函数及其签名（参数、返回值类型）。
2.  **调用链分析：** 标记函数间的调用关系（谁调用了谁），形成调用图。
3.  **依赖识别：** 识别所有使用的外部库、类和函数（如 `qiskit.algorithms.VQE`）。
4.  **结构标记：** 特别标记出内部函数（Nested Functions），防止遗漏。
5.  **常量提取：** 提取全局或局部的硬编码参数值。

**输出示例 (JSON):**

```json
{
  "functions_found": {
    "build_tfim_h": {"params": ["n", "hx", "j"], "returns": "SparsePauliOp"},
    "tfim_hea": {"params": ["n", "reps"], "returns": "QuantumCircuit"},
    "_assign_edges_to_layers": {"params": ["edges"], "location": "nested_in_tfim_hea"}
  },
  "external_apis": ["qiskit.algorithms.VQE", "qiskit.optimizers.L_BFGS_B", "qiskit.opflow.SparsePauliOp"],
  "call_chain": "main -> build_tfim_h -> tfim_hea -> VQE.run()"
}
```

#### 第二层：功能理解器 (算法语义分析)

**目的：** 理解每个代码块的“做什么”和“怎么做”，对应程序员的“深入理解”阶段。

**具体工作：**
针对第一层识别出的每个关键函数，进行深度分析：

1.  **功能目的 (Purpose):** 用一句话概括函数的核心目标。
2.  **实现方法 (Method):** 描述其采取的技术路径。
3.  **算法逻辑 (Algorithm):** 详细拆解其内部的算法步骤、数学公式或物理模型。

**输出示例 (JSON):**

```json
{
  "build_tfim_h": {
    "purpose": "构建一维横向场伊辛模型（TFIM）的哈密顿量",
    "method": "通过迭代向SparsePauliOp对象中添加泡利项",
    "details": {
      "X_terms": "为每个量子比特添加一个泡利X算符，系数为 -hx",
      "ZZ_terms": "为每对相邻的量子比特添加泡利ZZ算符，系数为 -j",
      "formula": "H = -hx * Σ(Xi) - j * Σ(Zi * Z(i+1))"
    }
  },
  "_assign_edges_to_layers": {
    "purpose": "将图的边进行分层，以在量子线路上实现门操作的并行化",
    "method": "使用贪心算法",
    "algorithm": "迭代地构建每一层，每层中选择与该层已选边不共享顶点的边加入。这是关键的性能优化。"
  }
}
```

#### 第三层：参数提取器

**目的：** 搜集所有用于代码执行的具体数值，对应程序员记录关键参数的阶段。

**具体工作：**

1.  **变量赋值：** 提取主执行流程中的所有参数赋值。
2.  **函数实参：** 记录函数调用时传递的实际参数值。
3.  **计算参数：** 识别由其他参数派生出的变量（如参数总数）,并且能够知道python里索引从0开始，Julia从1开始这种语言上的区别。
4.  **硬编码常量：** 提取代码中写死的特殊数值（如旋转角度 `np.pi/2`）。

**输出示例 (JSON):**

```json
{
  "main_parameters": {
    "n": 4,
    "hx": 1.5,
    "j": 1.0,
    "reps": 2
  },
  "optimizer_settings": {
    "maxiter": 5000
  },
  "derived_parameters": {
    "num_zz_params": "n - 1",
    "num_x_params": "n",
    "total_params": "reps * (num_zz_params + num_x_params)"
  } ,
    "constants": {
    "theta_zz": "-pi/2"
  }
}
```

### 三、 最终产出：智能整合与实现指南

Agent 1 的最终输出不是三份独立的分析报告，而是将三层分析结果**智能整合**成一份给 Agent 2 的、清晰可执行的\*\*“实现指南” (Implementation Guide)\*\*。这份指南就像一位资深程序员给另一位程序员的交接文档——清晰、实用、无废话。

**整合输出示例 (JSON):**

```json
{
  "implementation_tasks": [
    {
      "task_id": "hamiltonian_builder",
      "description": "构建TFIM哈密顿量",
      "methodology": {
        "summary": "构建泡利算符的线性组合",
        "formula": "H = -hx * Σ(Xi) - j * Σ(Zi * Z(i+1))",
        "implementation_hint": "源文件使用SparsePauliOp。在Julia/ITensors中，这通常对应于构建一个MPO（矩阵乘积算符）。"
      },
      "parameters_needed": ["n", "hx", "j"]
    },
    {
      "task_id": "ansatz_circuit_creator",
      "description": "创建硬件高效拟设（HEA）参数化线路",
      "methodology": {
        "initialization": "对所有量子比特施加Hadamard门",
        "layer_structure": "重复 'reps' 次：1. ZZ纠缠层 (通过CX-RZ-CX实现); 2. 单比特旋转层 (RX门)。",
        "implementation_hint": "参数的组织顺序和数量必须与源文件保持一致，以确保优化过程的正确性。"
      },
      "parameters_needed": ["n", "reps", "parameter_vector"]
    },
    {
      "task_id": "edge_partitioning_algorithm",
      "description": "实现用于并行化操作的边分层算法",
      "methodology": {
        "algorithm": "基于贪心策略，迭代地为每一层选择不共享顶点的边。",
        "purpose": "这是一个关键的性能优化，必须在目标代码中等效实现。",
        "criticality": "High"
      },
      "parameters_needed": ["edges"]
    },
    {
      "task_id": "vqe_optimization_framework",
      "description": "搭建VQE优化框架",
      "methodology": {
        "components": [
          "定义损失函数：计算给定参数下Ansatz线路状态的哈密顿量期望值。",
          "初始化参数。",
          "使用优化器（如L-BFGS-B）进行迭代优化，更新参数以最小化损失函数。",
          "返回最低能量和对应的最优参数。"
        ],
        "implementation_hint": "源文件中的qiskit.algorithms.VQE是一个高度封装的类，需要将其手动拆解为上述基本组件。"
      },
      "parameters_needed": ["optimizer_type", "maxiter", "initial_parameters"]
    }
  ],
  "parameter_values": {
    "n": 4,
    "hx": 1.5,
    "j": 1.0,
    "reps": 2,
    "maxiter": 5000
  },
  "implementation_constraints": {
    "must_preserve": [
      "边分层贪心算法的逻辑。",
      "ZZ旋转门通过CX-RZ-CX的分解方式。",
      "参数化线路中参数的排列顺序。"
    ],
    "high_level_apis_to_decompose": [
      "qiskit.algorithms.VQE",
      "qiskit.opflow.SparsePauliOp"
    ]
  }
}
```

### 四、 完整工作流程

```mermaid
graph TD
    A[输入: Python/Qiskit 源代码] --> B{Agent 1: 代码理解专家};
    B --> C[第一层: 结构扫描器] → 获得完整代码地图;
    C --> D[第二层: 功能理解器] → 理解每个部分在做什么;
    D --> E[第三层: 参数提取器] → 获取所有具体数值;
    E --> F[智能整合模块] → 生成"实现任务清单";
    F --> G[输出: 实现指南 (JSON)];
    G --> H[交付给 Agent 2: 代码生成专家];
```

### 五、 预期效果与成功标准

**预期效果：**
Agent 1的输出应让 Agent 2（代码生成专家）在不阅读原始Python代码的情况下，就能完全掌握重建任务所需的所有信息。它得到的不是代码的分析报告，而是一份清晰的“待办事项清单 (To-Do List)”。

**成功标准：**
如果将 Agent 1 的输出交给一位真实的、不熟悉原始Python代码的Julia量子计算程序员，他应该能够：

1.  **立即理解**需要实现的几个核心功能模块。
2.  **准确把握**每个模块的算法逻辑和物理含义。
3.  **不会遗漏**任何关键的实现细节或隐藏的优化（如边分层算法）。
4.  **拥有所有**必需的参数值来复现原始计算。

简而言之，这位程序员会认为：“这份交接文档非常到位，所有关键点都已指出，我可以立刻开始工作了。” 这就是 Agent 1 设计的最终目标。