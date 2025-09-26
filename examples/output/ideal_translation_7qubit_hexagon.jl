"""
理想翻译目标：Python test_7qubit_hexagon.py → Julia/ITensors MPS实现
这是翻译系统应该生成的目标代码
"""

using ITensors
using LinearAlgebra
using Statistics

# ================== 拓扑结构定义 ==================

struct FlexibleTopology
    """任意拓扑结构的抽象表示"""
    n_qubits::Int
    edges::Vector{Tuple{Int,Int}}
    sites::Vector{<:Index}
end

function create_custom_topology_2d(edges::Vector{Vector{Int}}, n_qubits::Union{Nothing,Int}=nothing)
    """
    Python → Julia 转换点1: 边列表索引转换
    Python: [[0,1], [1,2]] (0-indexed)
    Julia:  [(1,2), (2,3)] (1-indexed)
    """
    # 转换Python的0-indexed到Julia的1-indexed
    edge_tuples = [(edge[1]+1, edge[2]+1) for edge in edges]

    # 自动推断qubit数量
    if n_qubits === nothing
        all_qubits = Set{Int}()
        for (q1, q2) in edge_tuples
            push!(all_qubits, q1)
            push!(all_qubits, q2)
        end
        n_qubits = maximum(all_qubits)
    end

    # 创建MPS的site indices
    sites = siteinds("S=1/2", n_qubits)

    return FlexibleTopology(n_qubits, edge_tuples, sites)
end

# ================== 门分层策略 ==================

function partition_edges_to_layers(edges::Vector{Tuple{Int,Int}})
    """
    Python → Julia 转换点2: 内嵌函数提升为独立函数
    智能分层：确保每层内的门可以并行应用
    """
    layers = Vector{Vector{Tuple{Int,Int}}}()
    remaining_edges = Set(edges)

    while !isempty(remaining_edges)
        current_layer = Vector{Tuple{Int,Int}}()
        used_qubits = Set{Int}()

        for edge in collect(remaining_edges)
            q1, q2 = edge
            if !(q1 in used_qubits) && !(q2 in used_qubits)
                push!(current_layer, edge)
                push!(used_qubits, q1)
                push!(used_qubits, q2)
                delete!(remaining_edges, edge)
            end
        end
        push!(layers, current_layer)
    end

    return layers
end

# ================== MPS演化核心 ==================

function apply_rx_layer!(ψ::MPS, sites::Vector{<:Index}, θh::Float64)
    """
    Python → Julia 转换点3: circuit.rx → MPS单体门应用
    """
    if abs(θh) < 1e-10
        return ψ
    end

    N = length(sites)
    for j in 1:N
        # 构建RX门矩阵
        c = cos(θh/2)
        s_val = -im * sin(θh/2)

        rx_data = zeros(ComplexF64, 2, 2)
        rx_data[1,1] = c
        rx_data[1,2] = s_val
        rx_data[2,1] = s_val
        rx_data[2,2] = c

        # 创建ITensor门
        gate = ITensor(rx_data, sites[j]', sites[j])

        # 应用到MPS
        ψ[j] = noprime(gate * ψ[j])
    end

    return ψ
end

function apply_rzz_gate!(ψ::MPS, sites::Vector{<:Index}, i::Int, j::Int, θ::Float64;
                        χ::Int=64, cutoff::Float64=1e-10)
    """
    Python → Julia 转换点4: circuit.rzz → MPS两体门应用
    使用MPO处理任意距离的RZZ门，避免SWAP操作
    RZZ(θ) = exp(-iθ/2 * Z_i ⊗ Z_j)
    """

    if abs(i-j) == 1
        # 相邻门：使用高效的直接ITensor实现
        orthogonalize!(ψ, i)

        # 构建RZZ门矩阵
        c = cos(θ/2)
        s_val = -im * sin(θ/2)

        gate_data = zeros(ComplexF64, 2, 2, 2, 2)
        gate_data[1,1,1,1] = c - im*s_val  # |00⟩
        gate_data[1,2,1,2] = c + im*s_val  # |01⟩
        gate_data[2,1,2,1] = c + im*s_val  # |10⟩
        gate_data[2,2,2,2] = c - im*s_val  # |11⟩

        gate = ITensor(gate_data, sites[i]', sites[j]', sites[i], sites[j])

        # 合并张量并SVD分解
        wf = ψ[i] * ψ[j]
        wf = noprime(gate * wf)
        left_inds = uniqueinds(ψ[i], ψ[j])
        U, S, V = svd(wf, left_inds; maxdim=χ, cutoff=cutoff)

        ψ[i] = U
        ψ[j] = S * V

    else
        # 长程门：使用MPO实现
        # 构建 RZZ(θ) = exp(-iθ/2 * Z_i ⊗ Z_j)
        # = cos(θ/2) * I - i*sin(θ/2) * Z_i ⊗ Z_j

        ampo = OpSum()
        ampo += cos(θ/2), "Id", 1  # 身份算子项 (ITensors使用"Id"而非"I")
        ampo += -im*sin(θ/2), "Z", i, "Z", j  # ZZ相互作用项

        # 构建MPO并应用
        gate_mpo = MPO(ampo, sites)
        ψ = apply(gate_mpo, ψ; cutoff=cutoff, maxdim=χ)
        normalize!(ψ)
    end

    return ψ
end

function apply_trotter_evolution_2d(topology::FlexibleTopology,
                                   θh::Float64,
                                   n_trotter_steps::Int;
                                   χ::Int=64,
                                   cutoff::Float64=1e-10)
    """
    Python → Julia 转换点5: QuantumCircuit演化 → MPS Trotter演化
    核心转换：从量子电路构建转为直接MPS演化
    """
    # 初始化MPS为|000...0⟩态
    states = ["Up" for _ in 1:topology.n_qubits]
    ψ = productMPS(topology.sites, states)

    # 分层门结构
    zz_layers = partition_edges_to_layers(topology.edges)
    θ_zz = -π/2  # 固定的ZZ旋转角

    # Trotter演化循环
    for step in 1:n_trotter_steps
        # RX层
        apply_rx_layer!(ψ, topology.sites, θh)

        # RZZ层（分层并行）
        for layer_edges in zz_layers
            for (q1, q2) in layer_edges
                apply_rzz_gate!(ψ, topology.sites, q1, q2, θ_zz; χ=χ, cutoff=cutoff)
            end
        end

        # 归一化保持数值稳定
        normalize!(ψ)
    end

    return ψ
end

# ================== 可观测量测量 ==================

function compute_magnetization_2d(ψ::MPS, sites::Vector{<:Index})
    """
    Python → Julia 转换点6: Statevector期望值 → MPS期望值
    直接在MPS表示下计算，避免指数增长的态向量
    """
    N = length(sites)
    z_values = Float64[]

    for j in 1:N
        orthogonalize!(ψ, j)

        # 构建Z算符
        z_data = zeros(ComplexF64, 2, 2)
        z_data[1,1] = 1.0   # |0⟩⟨0|
        z_data[2,2] = -1.0  # |1⟩⟨1|
        z_op = ITensor(z_data, sites[j]', sites[j])

        # 计算局域期望值
        ψj_z = noprime(z_op * ψ[j])
        z_exp = real(scalar(dag(ψ[j]) * ψj_z))

        push!(z_values, z_exp)
    end

    # 返回平均磁化强度
    mz = mean(z_values)
    return mz
end

# ================== 参数扫描主函数 ==================

function run_tfim_2d_magnetization_sweep_flexible(edges::Vector{Vector{Int}},
                                                 J::Float64,  # 未使用，但保持接口兼容
                                                 h::Float64,  # 未使用，但保持接口兼容
                                                 θh_start::Float64,
                                                 θh_end::Float64,
                                                 θh_points::Int,
                                                 n_trotter_steps::Int;
                                                 χ::Int=64,
                                                 cutoff::Float64=1e-10)
    """
    Python → Julia 转换点7: 完整工作流重构
    优化：复用拓扑结构，只演化不同参数
    """
    # 创建拓扑（一次性）
    topology = create_custom_topology_2d(edges)

    # 参数扫描点
    θh_values = range(θh_start, θh_end, length=θh_points)
    magnetization_values = Float64[]

    println("Starting MPS evolution for $(topology.n_qubits)-qubit system")
    println("Bond dimension: χ=$χ, Cutoff: $cutoff")

    # 扫描循环
    for (idx, θh) in enumerate(θh_values)
        # 演化到最终态
        ψ_final = apply_trotter_evolution_2d(topology, θh, n_trotter_steps; χ=χ, cutoff=cutoff)

        # 测量磁化强度
        mz = compute_magnetization_2d(ψ_final, topology.sites)
        push!(magnetization_values, mz)

        # 进度输出
        max_bond = maxlinkdim(ψ_final)
        println("[$idx/$θh_points] θh=$(round(θh/π, digits=3))π: Mz=$mz, max_χ=$max_bond")
    end

    # 返回结果字典（保持Python接口兼容）
    return Dict(
        "theta_h_values" => collect(θh_values),
        "magnetization_values" => magnetization_values
    )
end

# ================== 主函数 ==================

function main()
    """
    Python → Julia 转换点8: 主函数结构保持一致
    """
    # 7-qubit六边形拓扑
    edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 6], [1, 6], [2, 6]]

    # 参数设置
    n_qubits = 7  # 其实可以自动推断
    θh = 0.785
    n_trotter_steps = 5
    J = 1.0  # TFIM耦合强度
    h = 0.5  # 横场强度
    θh_start = 0.0
    θh_end = 1.57
    θh_points = 10

    # 运行扫描
    @time result = run_tfim_2d_magnetization_sweep_flexible(
        edges, J, h, θh_start, θh_end, θh_points, n_trotter_steps;
        χ=64,  # 可调节的键维
        cutoff=1e-10
    )

    # 输出结果
    println("\n========== Results ==========")
    println("θh values: ", round.(result["theta_h_values"]/π, digits=3), "π")
    println("Mz values: ", round.(result["magnetization_values"], digits=4))

    return result
end

# 如果直接运行此文件
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end