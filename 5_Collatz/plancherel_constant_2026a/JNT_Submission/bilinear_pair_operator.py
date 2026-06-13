"""
bilinear_pair_operator.py — build the bilinear pair-form operator T_M acting on
M_n: (Z/3^n)* → C defined by

  M_n(η) := Σ_{ξ ∈ Z/3^n, 3∤ξ} μ̂_n(ξ) · μ̂_n*(ξ·η)

for η ∈ (Z/3^n)*. Note M_n(1) = Σ |μ̂_n(ξ)|² = S_n.

Tao recursion: μ̂_{n+1}(ξ) = Σ_v 2^{-v} e^{-2πi ξ 2^{-v}/3^{n+1}} μ̂_n(ξ·2^{-v} mod 3^n)

Leads to recursion on M:
  M_{n+1}(η) = ... (formula derived in §3 of c_seven_forty_fifth.md)

The rate of convergence S_n → 7/15 is governed by the SUBDOMINANT EIGENVALUE of T_M
acting on the full bilinear space.

Strategy:
1. Compute μ̂_n(ξ) for all ξ ∈ Z/3^n at levels n = 1, 2, 3 exactly via complex-Fraction
2. Compute M_n(η) exactly for η ∈ (Z/3^n)* (bilinear pair moments)
3. Verify M_n(1) = S_n
4. Look for level-jumping recursion structure linking M_n → M_{n+1}
5. Extract finite-rank approximation of T_M and compute its spectrum
"""
import sys
import os
import time
from fractions import Fraction
import cmath
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OUTDIR = r"C:\Collatz\experiments_output"
os.makedirs(OUTDIR, exist_ok=True)


def build_markov_rational(k):
    N = 3**k
    M = 2 * 3**(k-1)
    inv2 = pow(2, -1, N)
    powers_inv2 = [pow(inv2, v, N) for v in range(1, M + 1)]
    coprime_states = [r for r in range(N) if r % 3 != 0]
    state_idx = {r: i for i, r in enumerate(coprime_states)}
    n = len(coprime_states)
    K = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    Z_v = Fraction(2**M - 1, 2**M)
    for r in coprime_states:
        for r_v in range(1, M + 1):
            p = Fraction(1, 2**r_v) / Z_v
            target = ((3 * r + 1) * powers_inv2[r_v - 1]) % N
            K[state_idx[r]][state_idx[target]] += p
    return K, coprime_states


def stationary_rational(K):
    n = len(K)
    A = [[K[j][i] - (Fraction(1) if i == j else Fraction(0)) for j in range(n)] for i in range(n)]
    A[n - 1] = [Fraction(1)] * n
    b = [Fraction(0)] * n
    b[n - 1] = Fraction(1)
    for col in range(n):
        pivot = -1
        for row in range(col, n):
            if A[row][col] != 0:
                pivot = row
                break
        if pivot == -1:
            raise ValueError(f"Singular at col {col}")
        if pivot != col:
            A[col], A[pivot] = A[pivot], A[col]
            b[col], b[pivot] = b[pivot], b[col]
        piv = A[col][col]
        for j in range(col, n):
            A[col][j] /= piv
        b[col] /= piv
        for row in range(n):
            if row != col and A[row][col] != 0:
                factor = A[row][col]
                for j in range(col, n):
                    A[row][j] -= factor * A[col][j]
                b[row] -= factor * b[col]
    return b


def char_func_complex(pi, coprime, k, xi):
    """μ̂_k(ξ) = Σ_r π_k(r) e^{-2πi r ξ / 3^k} (numerical complex)."""
    N = 3**k
    z = complex(0, 0)
    for i, r in enumerate(coprime):
        p = float(pi[i])
        z += p * cmath.exp(-2j * cmath.pi * r * xi / N)
    return z


def compute_M_n(pi, coprime, k):
    """Compute M_n(η) for all η in (Z/3^k)* using μ̂_k(ξ).
    M_n(η) = Σ_{ξ: 3∤ξ in Z/3^k} μ̂_k(ξ) μ̂_k*(ξ·η mod 3^k)
    Returns dict η → complex value.
    """
    N = 3**k
    coprime_set = set(coprime)
    # Compute μ̂_k(ξ) for all ξ in Z/3^k
    mu_hat = {}
    for xi in range(N):
        mu_hat[xi] = char_func_complex(pi, coprime, k, xi)

    M = {}
    for eta in coprime:
        total = complex(0, 0)
        for xi in coprime:  # ξ coprime to 3
            xi_eta = (xi * eta) % N
            total += mu_hat[xi] * mu_hat[xi_eta].conjugate()
        M[eta] = total
    return M


def main():
    print("# Bilinear pair operator T_M for rate-1/2 spectral identification")
    print()

    # Compute stationary at levels 1, 2, 3
    pis = {}
    for k in [1, 2, 3]:
        K, coprime = build_markov_rational(k)
        pi_q = stationary_rational(K)
        pis[k] = (pi_q, coprime)
        print(f"  k={k}: {len(coprime)} states")
    print()

    # Compute M_n(η) for each level
    print("# M_n(η) for η ∈ (Z/3^n)*: bilinear pair moments")
    print()
    Ms = {}
    for k in [1, 2, 3]:
        pi_q, coprime = pis[k]
        M_dict = compute_M_n(pi_q, coprime, k)
        Ms[k] = M_dict
        print(f"## k = {k}: M_{k} on {len(coprime)} values of η")
        print(f"   M_{k}(1) = {M_dict[1]:.10f}  (should = S_{k})")
        print()
        for eta in coprime:
            v = M_dict[eta]
            print(f"   M_{k}(η={eta:>3}): {v.real:+.6f} {v.imag:+.6f}i,   |M| = {abs(v):.6f}")
        print()

    # Verify M_n(1) = S_n: from earlier S_1 = 2/3, S_2 = 10/21, S_3 = 31370/67963
    print("# Verify M_n(1) = S_n")
    for k in [1, 2, 3]:
        S_known = {1: 2/3, 2: 10/21, 3: 31370/67963}
        M1 = Ms[k][1].real
        print(f"  k={k}: M_{k}(1) = {M1:.10f}, S_{k} = {S_known[k]:.10f}, diff = {M1 - S_known[k]:.2e}")
    print()

    # Symmetry: M_n(η) = M_n(η^{-1})* (conjugate inversion symmetry)
    # because M_n(η) = sum_ξ μ̂(ξ) μ̂*(ξη), substitute ξ' = ξη: = sum_ξ' μ̂(ξ'/η) μ̂*(ξ') = M_n(1/η)*
    print("# Symmetry check: M_n(η) = M_n(η^{-1})*")
    for k in [2, 3]:
        N = 3**k
        coprime = pis[k][1]
        M_dict = Ms[k]
        all_match = True
        for eta in coprime:
            eta_inv = pow(eta, -1, N)
            lhs = M_dict[eta]
            rhs = M_dict[eta_inv].conjugate()
            if abs(lhs - rhs) > 1e-10:
                all_match = False
                print(f"    k={k} η={eta} η^{-1}={eta_inv}: M(η)={lhs}, M(η^{-1})*={rhs}, diff={abs(lhs-rhs):.2e}")
        if all_match:
            print(f"  k={k}: symmetry M_n(η) = M_n(η^{{-1}})* verified ✓")
    print()

    # Now examine the recursion structure: M_{n+1}(η) for η ∈ (Z/3^{n+1})*.
    # Each η at level n+1 has an η mod 3^n at level n. Let's see how M_{n+1}(η) relates
    # to M_n(η mod 3^n) and other M_n values.
    print("# Recursion fingerprint: M_{n+1}(η) vs M_n(η mod 3^n)")
    print()
    for k in [1, 2]:
        N_k = 3**k
        coprime_kp1 = pis[k+1][1]
        M_n_dict = Ms[k]
        M_np1_dict = Ms[k+1]
        print(f"## k={k} → k+1={k+1}:")
        for eta in coprime_kp1[:6]:  # first 6
            eta_modk = eta % N_k
            if eta_modk == 0 or eta_modk % 3 == 0:
                continue
            M_n_val = M_n_dict.get(eta_modk, 'N/A')
            M_np1_val = M_np1_dict[eta]
            print(f"   η = {eta:>3} (mod 3^{k+1}); η mod 3^{k} = {eta_modk}: "
                  f"M_{k+1}(η) = {M_np1_val.real:+.4f}{M_np1_val.imag:+.4f}i, "
                  f"M_{k}(η mod 3^{k}) = {M_n_val.real:+.4f}{M_n_val.imag:+.4f}i, "
                  f"ratio = {M_np1_val/M_n_val:.4f}")
        print()

    # Save M values
    out = os.path.join(OUTDIR, "M_n_bilinear_moments.csv")
    with open(out, 'w') as f:
        f.write("k,eta,M_real,M_imag,abs_M\n")
        for k in [1, 2, 3]:
            for eta in pis[k][1]:
                v = Ms[k][eta]
                f.write(f"{k},{eta},{v.real:.15f},{v.imag:.15f},{abs(v):.15f}\n")
    print(f"[save] {out}")


if __name__ == "__main__":
    main()
