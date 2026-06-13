"""
c_seven_forty_fifth_derivation.py — pursue rigorous c = 7/45 in ||d_{k+1}||² ≈ c·(1/3)^k.

Approach:
1. Compute ||d_{k+1}||² exactly (rationals) for k=1..4
2. Build the pure deviation lifting operator L_k (orthogonal to π-conservation modes)
3. Compute leading singular value of L_k cleanly
4. Identify whether 1/√3 emerges exactly
5. Test whether c = 7/45 is the leading mode's L²-norm × initial conditions
"""
import sys
import math
import os
from fractions import Fraction
from collections import defaultdict
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
OUTDIR = r"C:\Collatz\experiments_output"


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


def compute_d_squared_exact(pi_k, coprime_k, pi_kp1, coprime_kp1, k):
    """||d_{k+1}||² = Σ_r' π_{k+1}(r')² - (1/3) Σ_r π_k(r)²  (R74's identity)."""
    sum_pi_k_sq = sum(p * p for p in pi_k)
    sum_pi_kp1_sq = sum(p * p for p in pi_kp1)
    return sum_pi_kp1_sq - sum_pi_k_sq / 3


def compute_pure_deviation_operator_numerical(k, pi_k_float, coprime_k, pi_kp1_float, coprime_kp1):
    """Build L_k restricted to deviation subspace, return leading singular values.

    L_k maps π_k → π_{k+1} via the lifting structure. To isolate the 'pure deviation' mode,
    we remove the π-conservation direction.

    The approach: compute the actual sub-cell ratios (α, β, γ) at each r', stack them as
    a 3·n_k × 1 vector (deviation from uniform), and look at how they scale with iterating k.
    """
    N_k = 3**k
    state_idx_kp1 = {r: i for i, r in enumerate(coprime_kp1)}

    # Build deviation vector d_{k+1} (each cell contributes 3 components summing to 0)
    d_components = []
    for i, r in enumerate(coprime_k):
        lifts = [r, r + N_k, r + 2 * N_k]
        masses = [pi_kp1_float[state_idx_kp1[lift]] for lift in lifts]
        m_total = sum(masses)
        if m_total == 0:
            continue
        # Deviation from uniform split: each lift_mass - m_total/3
        for mass in masses:
            d_components.append(mass - m_total / 3)
    return np.array(d_components)


def main():
    print("# Rigorous c = 7/45 derivation attempt")
    print()
    print("# Step 1: exact rational ||d_{k+1}||² for k = 1..3")
    print()

    # Compute stationary
    pis_q = {}
    pis_f = {}
    coprimes = {}
    for k in [1, 2, 3, 4]:
        K, coprime = build_markov_rational(k)
        pi_q = stationary_rational(K)
        pi_f = [float(p) for p in pi_q]
        pis_q[k] = pi_q
        pis_f[k] = pi_f
        coprimes[k] = coprime
        print(f"  k={k}: {len(pi_q)} states")

    # Compute ||d||² as exact rationals
    print()
    print(f"  {'k':>3}  {'||d_{k+1}||² exact':>30}  {'decimal':>12}  {'·3^k':>10}  {'limit 7/45':>10}")
    d_sq_data = []
    for k in [1, 2, 3]:
        d2 = compute_d_squared_exact(pis_q[k], coprimes[k], pis_q[k+1], coprimes[k+1], k)
        scaled = d2 * Fraction(3**k, 1)
        d_sq_data.append((k, d2, scaled))
        print(f"  {k:>3}  {str(d2):>30}  {float(d2):>12.6e}  {float(scaled):>10.6f}  {7/45:>10.6f}")

    # Numerical for k=4, 5
    print()
    print("# Numerical for k=4,5,6 (to see asymptote)")
    for k in [4, 5]:
        if k > 4:
            # Use power iteration since rational gets too slow
            from collections import defaultdict
            N = 3**k
            M = 2 * 3**(k-1)
            inv2 = pow(2, -1, N)
            powers_inv2 = [pow(inv2, v, N) for v in range(1, M + 1)]
            coprime = [r for r in range(N) if r % 3 != 0]
            si = {r: i for i, r in enumerate(coprime)}
            n = len(coprime)
            K = np.zeros((n, n))
            Z_v = 1.0 - 2.0**(-M)
            for r in coprime:
                for r_v in range(1, M + 1):
                    p = 2.0**(-r_v) / Z_v
                    target = ((3 * r + 1) * powers_inv2[r_v - 1]) % N
                    K[si[r], si[target]] += p
            pi = np.ones(n) / n
            for _ in range(200):
                pi = pi @ K
                pi = pi / pi.sum()
            pis_f[k] = list(pi)
            coprimes[k] = coprime
        sum_k = sum(p * p for p in pis_f[k-1])
        sum_kp1 = sum(p * p for p in pis_f[k])
        d2 = sum_kp1 - sum_k / 3
        scaled = d2 * 3**(k-1)
        print(f"  k={k-1}→{k}: ||d||²={d2:.6e}  ·3^{k-1}={scaled:.6f}  diff to 7/45 = {scaled - 7/45:+.6e}")

    # Step 2: Verify R74 identity rationally
    print()
    print("# Step 2: Verify R74 algebraic identity S_{k+1} = 3^{k+1} · ||d_{k+1}||² rationally")
    print()
    expected_S = {1: Fraction(2, 3), 2: Fraction(10, 21)}  # known exact
    for k, d2, scaled in d_sq_data:
        S_kp1_via_d = d2 * Fraction(3**(k+1), 1)  # from R74 identity
        print(f"  k={k}: 3^{k+1} · ||d_{k+1}||² = {str(S_kp1_via_d)} = {float(S_kp1_via_d):.6f}")
        if (k+1) in expected_S:
            match = S_kp1_via_d == expected_S[k+1]
            print(f"           expected S_{k+1} = {expected_S[k+1]} = {float(expected_S[k+1]):.6f}    match: {match}")

    # Step 3: Compute pure-deviation operator's leading singular value
    print()
    print("# Step 3: Leading singular value of pure deviation operator")
    print()
    print("  Approach: stack deviation vectors d_{k+1} (each cell deviation from uniform).")
    print("  Compute ratio of L²-norms of d_{k+1} / d_k as proxy for leading mode size.")
    print()

    d_vectors = {}
    for k in [1, 2, 3, 4, 5]:
        if k+1 not in pis_f:
            continue
        d_vec = compute_pure_deviation_operator_numerical(k, pis_f[k], coprimes[k], pis_f[k+1], coprimes[k+1])
        d_vectors[k] = d_vec
        norm = np.linalg.norm(d_vec)
        print(f"  k={k}: ||d_{k+1}||_2 = {norm:.6e} (from explicit deviation vector)")

    # Ratio
    print()
    print(f"  {'k':>3}  {'||d_{k+1}||_2':>14}  {'||d||²':>14}  {'ratio (k+1)/k':>15}")
    norms = {k: np.linalg.norm(d_vectors[k]) for k in d_vectors}
    norms_sq = {k: n**2 for k, n in norms.items()}
    prev = None
    for k in sorted(norms.keys()):
        ratio = norms_sq[k] / prev if prev else float('nan')
        print(f"  {k:>3}  {norms[k]:>14.6e}  {norms_sq[k]:>14.6e}  {ratio if prev else 'n/a':>15}")
        prev = norms_sq[k]

    # Step 4: Asymptotic ||d||² · 3^k convergence
    print()
    print("# Step 4: ||d||² · 3^k convergence to c = 7/45")
    print()
    print(f"  {'k':>3}  {'||d_{k+1}||²':>14}  {'||d||² · 3^k':>14}  {'7/45':>10}  {'diff':>14}")
    for k in sorted(norms_sq.keys()):
        scaled = norms_sq[k] * 3**k
        diff = scaled - 7/45
        print(f"  {k:>3}  {norms_sq[k]:>14.6e}  {scaled:>14.6f}  {7/45:>10.6f}  {diff:>+14.6e}")

    # Step 5: closed-form attempt — try to express asymptotic as eigenvalue identity
    # If ||d_{k+1}||² = c · (1/3)^k + lower order, taking ratio (||d_{k+1}||² / ||d_k||²) → 1/3
    print()
    print("# Step 5: Asymptotic rate test (||d_{k+1}||² / ||d_k||² → 1/3?)")
    prev = None
    for k in sorted(norms_sq.keys()):
        ratio = norms_sq[k] / prev if prev else float('nan')
        if not isinstance(ratio, str):
            print(f"  k={k}: ||d||²_k / ||d||²_{{k-1}} = {ratio:.6f}    (expected 1/3 = {1/3:.6f})")
        prev = norms_sq[k]

    # Save
    out = os.path.join(OUTDIR, "c_seven_forty_fifth.csv")
    with open(out, 'w') as f:
        f.write("k,d_squared,d_squared_times_3k,7_over_45,diff\n")
        for k in sorted(norms_sq.keys()):
            scaled = norms_sq[k] * 3**k
            f.write(f"{k},{norms_sq[k]:.10e},{scaled:.10f},{7/45:.10f},{scaled-7/45:.10e}\n")
    print(f"\n[save] {out}")


if __name__ == "__main__":
    main()
