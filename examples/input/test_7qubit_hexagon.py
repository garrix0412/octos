import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp

def create_custom_topology_2d(edges: list, n_qubits: int = None) -> dict:
    edge_tuples = [tuple(edge) for edge in edges]
    if n_qubits is None:
        all_qubits = set()
        for edge in edge_tuples:
            all_qubits.update(edge)
        n_qubits = len(all_qubits)
        if all_qubits != set(range(n_qubits)):
            n_qubits = max(all_qubits) + 1
    topology_data = {
        "n_qubits": n_qubits,
        "edges": edge_tuples
    }
    return topology_data

def apply_trotter_evolution_2d(topology_data: dict, theta_h: float, n_trotter_steps: int) -> QuantumCircuit:
    def _assign_edges_to_layers(edges: list) -> list:
        layers = []
        remaining_edges = set(edges)
        while remaining_edges:
            current_layer = []
            used_qubits = set()
            for edge in list(remaining_edges):
                q1, q2 = edge
                if q1 not in used_qubits and q2 not in used_qubits:
                    current_layer.append(edge)
                    used_qubits.add(q1)
                    used_qubits.add(q2)
                    remaining_edges.remove(edge)
            layers.append(current_layer)
        return layers

    n_qubits = topology_data["n_qubits"]
    edges = topology_data["edges"]
    circuit = QuantumCircuit(n_qubits)
    zz_layers = _assign_edges_to_layers(edges)
    theta_zz = -np.pi / 2

    for step in range(n_trotter_steps):
        if abs(theta_h) > 1e-10:
            for q in range(n_qubits):
                circuit.rx(theta_h, q)
        for layer_edges in zz_layers:
            for (q1, q2) in layer_edges:
                circuit.rzz(theta_zz, q1, q2)

    return circuit

def compute_magnetization_2d(trotter_circuit: QuantumCircuit) -> float:
    n_qubits = trotter_circuit.num_qubits
    initial_state = Statevector.from_label('0' * n_qubits)
    final_state = initial_state.evolve(trotter_circuit)
    z_values = []
    for i in range(n_qubits):
        pauli = ['I'] * n_qubits
        pauli[i] = 'Z'
        pauli_string = ''.join(pauli)
        z_op = SparsePauliOp([pauli_string], [1.0])
        z_exp = final_state.expectation_value(z_op)
        if np.iscomplex(z_exp) and abs(z_exp.imag) < 1e-10:
            z_exp = z_exp.real
        z_values.append(float(z_exp))
    mz = np.mean(z_values)
    return float(mz)

def run_tfim_2d_magnetization_sweep_flexible(edges: list, J: float, h: float, theta_h_start: float, theta_h_end: float, theta_h_points: int, n_trotter_steps: int) -> dict:
    topology_data = create_custom_topology_2d(edges)
    theta_h_values = np.linspace(theta_h_start, theta_h_end, theta_h_points)
    magnetization_values = []
    for theta_h in theta_h_values:
        trotter_circuit = apply_trotter_evolution_2d(topology_data, theta_h, n_trotter_steps)
        mz = compute_magnetization_2d(trotter_circuit)
        magnetization_values.append(mz)
    magnetization_values = np.array(magnetization_values)
    return {
        "theta_h_values": theta_h_values.tolist(),
        "magnetization_values": magnetization_values.tolist()
    }

def main():
    edges = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [0, 6], [1, 6], [2, 6]]
    n_qubits = 7
    theta_h = 0.785
    n_trotter_steps = 5
    J = 1.0
    h = 0.5
    theta_h_start = 0.0
    theta_h_end = 1.57
    theta_h_points = 10
    
    result = run_tfim_2d_magnetization_sweep_flexible(edges, J, h, theta_h_start, theta_h_end, theta_h_points, n_trotter_steps)
    print(result)

if __name__ == "__main__":
    main()