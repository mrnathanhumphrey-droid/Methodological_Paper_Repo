"""
T_lead_2x2.py — exploit the structural collapse P^{+-}(c) = 0 + class-c symmetry
to reduce the rate operator to a 2x2 matrix on (P_{++}, P_{--}).

For n ≥ 2:
  P^{++}(1) = P^{++}(2) =: P_n^+  (call it just P_+)
  P^{--}(1) = P^{--}(2) =: P_n^-  (call it just P_-)
  P^{+-}(c) = 0 for c=1,2

Then S_n = 2(P_+ + P_-).

Asymptotic targets: P_+ → 7/150, P_- → 28/150.

The recursion (P_n^+, P_n^-) → (P_{n+1}^+, P_{n+1}^-) is determined by Tao's recursion.
We FIT a linear (affine) model from observed data and identify the eigenvalues.

Data: from previous run,
  Level 2: P_+ = 1/21,  P_- = 4/21
  Level 3: P_+ = 0.04616, P_- = 0.18463
  Level 4: ?
  Level 5: ?
  Level 6: ?
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


def compute_P_plus_minus(pi_q, coprime, k):
    """Compute P_+ := P^++(c=1) = P^++(c=2) and P_- := P^--(c=1) = P^--(c=2) exactly.

    P^++(c) = Σ_{ξ in (Z/3^k)*, ξ≡c mod 3} |μ̂_n^+(ξ)|²
    where μ̂_n^+(ξ) = Σ_{r ≡ 1 mod 3} π_n(r) e^{-2πi r ξ/3^k}.

    Note: |μ̂^+(ξ)|² is the squared magnitude. We compute over Q[ω] using ω = e^{2πi/3}
    expansions, but for simplicity here use float complex.
    """
    N = 3**k
    pi_dict = {coprime[i]: pi_q[i] for i in range(len(coprime))}
    P_plus_c1 = Fraction(0)
    P_plus_c2 = Fraction(0)
    P_minus_c1 = Fraction(0)
    P_minus_c2 = Fraction(0)

    # |μ̂^a(ξ)|² involves Σ_r,r' π(r) π(r') e^{-2πi (r-r') ξ/N}, which is a
    # complex sum. To get rational result, expand via cosines.
    # μ̂^a(ξ) μ̂^a*(ξ) = Σ_{r,r' both in class a} π(r) π(r') e^{-2πi (r-r') ξ/N}
    # Sum over ξ ≡ c mod 3 of e^{-2πi (r-r') ξ/N}:
    #   = Σ_{ξ in coprime classes} e^{-2πi (r-r') ξ/N} restricted to ξ ≡ c
    # We compute this NUMERICALLY for now (over float).
    pi_f = {r: float(p) for r, p in pi_dict.items()}

    P_plus_c = [0.0, 0.0]  # c=1, c=2 (index 0=c=1, index 1=c=2)
    P_minus_c = [0.0, 0.0]

    for xi in coprime:
        c_idx = (xi % 3) - 1  # 0 if c=1, 1 if c=2
        mu_plus = sum(pi_f[r] * cmath.exp(-2j * cmath.pi * r * xi / N)
                      for r in coprime if r % 3 == 1)
        mu_minus = sum(pi_f[r] * cmath.exp(-2j * cmath.pi * r * xi / N)
                       for r in coprime if r % 3 == 2)
        P_plus_c[c_idx] += abs(mu_plus) ** 2
        P_minus_c[c_idx] += abs(mu_minus) ** 2

    return P_plus_c, P_minus_c


def main():
    print("# Rate-1/2 operator T_2x2 on (P_+, P_-)")
    print()

    # Compute (P_+, P_-) at levels 2..6
    print("# Computing (P_+, P_-) at levels k = 2..6 (heavy at k=6)...")
    data = []
    for k in [2, 3, 4, 5]:
        t0 = time.time()
        K, coprime = build_markov_rational(k)
        pi_q = stationary_rational(K)
        elapsed_pi = time.time() - t0
        t0 = time.time()
        P_plus_c, P_minus_c = compute_P_plus_minus(pi_q, coprime, k)
        elapsed_P = time.time() - t0
        # Verify symmetry
        assert abs(P_plus_c[0] - P_plus_c[1]) < 1e-10, f"P_+ asymmetry at k={k}"
        assert abs(P_minus_c[0] - P_minus_c[1]) < 1e-10, f"P_- asymmetry at k={k}"
        P_plus = P_plus_c[0]
        P_minus = P_minus_c[0]
        S_k = 2 * (P_plus + P_minus)
        data.append((k, P_plus, P_minus, S_k))
        print(f"  k={k} ({len(coprime)} states): π in {elapsed_pi:.1f}s, P in {elapsed_P:.1f}s, "
              f"P_+ = {P_plus:.10f}, P_- = {P_minus:.10f}, S_k = {S_k:.10f}")

    print()
    print("# Asymptotic targets:")
    print(f"  P_+ target = 7/150 = {7/150:.10f}")
    print(f"  P_- target = 14/75 = 28/150 = {14/75:.10f}")
    print(f"  S_∞ target = 7/15 = {7/15:.10f}")
    print()

    # Fit linear recursion (P_+, P_-) → (P_+, P_-) of the form
    # P_+^{n+1} - C_+ = a · (P_+^n - C_+) + b · (P_-^n - C_-)
    # P_-^{n+1} - C_- = c · (P_+^n - C_+) + d · (P_-^n - C_-)
    # where C_+ = 7/150, C_- = 14/75 are the limits
    print("# Fit linear recursion T (deviations from limits):")
    C_plus = 7/150
    C_minus = 14/75

    devs = [(P_plus - C_plus, P_minus - C_minus) for k, P_plus, P_minus, S in data]
    print(f"  Deviations (P_+ - 7/150, P_- - 14/75):")
    for i, (k, _, _, _) in enumerate(data):
        print(f"    k={k}: ({devs[i][0]:+.6e}, {devs[i][1]:+.6e})")
    print()

    # Use 2 transitions (k=2→3 and k=3→4) to fit T:
    # devs[1] = T · devs[0]
    # devs[2] = T · devs[1]
    # 2 equations × 2 dim = 4 scalar equations; T has 4 unknowns → exactly determined
    d0 = np.array(devs[0])
    d1 = np.array(devs[1])
    d2 = np.array(devs[2])

    # Build the matrix system: D_in = [d0, d1], D_out = [d1, d2]
    # T · D_in = D_out → T = D_out · D_in^{-1}
    D_in = np.column_stack([d0, d1])
    D_out = np.column_stack([d1, d2])
    if np.linalg.det(D_in) != 0:
        T = D_out @ np.linalg.inv(D_in)
        print(f"  Fitted T (from k=2→3, k=3→4):")
        print(f"    {T[0,0]:+.6f}   {T[0,1]:+.6f}")
        print(f"    {T[1,0]:+.6f}   {T[1,1]:+.6f}")
        eigvals = np.linalg.eigvals(T)
        print(f"  Eigenvalues: {eigvals}")
        print(f"  |Eigenvalues|: {np.abs(eigvals)}")
        print()
        # Verify on k=4→5
        d3 = np.array(devs[3])
        d3_pred = T @ d2
        print(f"  Verification on k=4→5:")
        print(f"    Actual d_3 = ({d3[0]:+.6e}, {d3[1]:+.6e})")
        print(f"    Predicted = ({d3_pred[0]:+.6e}, {d3_pred[1]:+.6e})")
        print(f"    Residual = ({d3[0] - d3_pred[0]:+.2e}, {d3[1] - d3_pred[1]:+.2e})")

    # Save data
    out = os.path.join(OUTDIR, "P_plus_minus_table.csv")
    with open(out, 'w') as f:
        f.write("k,P_plus,P_minus,S_k,P_plus_minus_target_diff,P_minus_target_diff\n")
        for k, P_plus, P_minus, S_k in data:
            f.write(f"{k},{P_plus:.15f},{P_minus:.15f},{S_k:.15f},"
                    f"{P_plus - C_plus:+.6e},{P_minus - C_minus:+.6e}\n")
    print(f"\n[save] {out}")


if __name__ == "__main__":
    main()
