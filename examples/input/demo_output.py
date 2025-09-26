from qiskit.quantum_info import SparsePauliOp
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit_algorithms.optimizers import L_BFGS_B
from qiskit_algorithms import VQE
from qiskit.primitives import Estimator

def build_tfim_h(n: int, hx: float, j: float) -> SparsePauliOp:
    pauli_list = []
    for i in range(n):
        pauli_str = ['I'] * n
        pauli_str[i] = 'X'
        pauli_list.append((''.join(pauli_str), -hx))
    for i in range(n - 1):
        pauli_str = ['I'] * n
        pauli_str[i] = 'Z'
        pauli_str[i + 1] = 'Z'
        pauli_list.append((''.join(pauli_str), -j))
    return SparsePauliOp.from_list(pauli_list)

def tfim_hea(n: int, reps: int) -> QuantumCircuit:
    qc = QuantumCircuit(n)
    for i in range(n):
        qc.h(i)
    num_zz_params = n - 1
    num_x_params = n
    num_params_per_layer = num_zz_params + num_x_params
    total_params = reps * num_params_per_layer
    params = ParameterVector('θ', total_params)
    param_idx = 0
    for layer in range(reps):
        for i in range(n - 1):
            qc.cx(i, i + 1)
            qc.rz(params[param_idx], i + 1)
            qc.cx(i, i + 1)
            param_idx += 1
        for i in range(n):
            qc.rx(params[param_idx], i)
            param_idx += 1
    return qc

def create_l_bfgs_b_optimizer(maxiter: int):
    return L_BFGS_B(maxiter=maxiter)

def run_vqe(hamiltonian, ansatz, optimizer):
    estimator = Estimator()
    vqe = VQE(estimator, ansatz, optimizer)
    result = vqe.compute_minimum_eigenvalue(hamiltonian)
    energy = float(result.eigenvalue.real)
    print(f"VQE ground state energy: {energy:.6f}")
    return energy

def main():
    n = 4
    hx = 1.5
    j = 1.5
    reps = 2
    maxiter = 5000

    hamiltonian = build_tfim_h(n, hx, j)
    ansatz = tfim_hea(n, reps)
    optimizer = create_l_bfgs_b_optimizer(maxiter)
    
    result = run_vqe(hamiltonian, ansatz, optimizer)
    return result

if __name__ == "__main__":
    main()