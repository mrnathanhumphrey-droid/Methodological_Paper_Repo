"""
T_lead_operator.py — build the explicit T_lead operator on class-resolved bilinear
moments P_n^{a,b}(c), find its spectrum, identify rate-1/2 eigenvalue.

Strategy:
1. Compute μ̂_n^+(ξ), μ̂_n^-(ξ) at level n (class-resolved characters)
2. Compute 8-component P_n vector: P^{ab}(c) for (a,b) ∈ {+,-}², c ∈ {1,2}
3. Verify R_n = M_n(1+3^{n-1}) and S_n in terms of P_n
4. Build T matrix P_n → P_{n+1} via Tao recursion + symbolic expansion
5. Compute T's eigenvalues — look for 1/2

For now: numerical (float) verification at n=1, 2. Exact over Q[ω] is the next step
but heavy.
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


def char_funcs_class_resolved(pi, coprime, k):
    """Compute μ̂_k^+(ξ) and μ̂_k^-(ξ) for all ξ ∈ Z/3^k.
    + = class 1 (r ≡ 1 mod 3), - = class 2 (r ≡ 2 mod 3)."""
    N = 3**k
    pi_dict = {coprime[i]: float(pi[i]) for i in range(len(coprime))}
    mu_plus = {}
    mu_minus = {}
    for xi in range(N):
        plus = complex(0, 0)
        minus = complex(0, 0)
        for r in coprime:
            phase = cmath.exp(-2j * cmath.pi * r * xi / N)
            term = pi_dict[r] * phase
            if r % 3 == 1:
                plus += term
            else:  # r % 3 == 2
                minus += term
        mu_plus[xi] = plus
        mu_minus[xi] = minus
    return mu_plus, mu_minus


def compute_P_vector(mu_plus, mu_minus, coprime, k):
    """Compute 8-component P vector: P^{ab}(c) for (a,b) in {+,-}², c in {1,2}."""
    P = {
        ('+', '+', 1): complex(0),
        ('+', '+', 2): complex(0),
        ('-', '-', 1): complex(0),
        ('-', '-', 2): complex(0),
        ('+', '-', 1): complex(0),
        ('+', '-', 2): complex(0),
        ('-', '+', 1): complex(0),
        ('-', '+', 2): complex(0),
    }
    for xi in coprime:
        c = xi % 3  # 1 or 2
        P[('+', '+', c)] += mu_plus[xi] * mu_plus[xi].conjugate()
        P[('-', '-', c)] += mu_minus[xi] * mu_minus[xi].conjugate()
        P[('+', '-', c)] += mu_plus[xi] * mu_minus[xi].conjugate()
        P[('-', '+', c)] += mu_minus[xi] * mu_plus[xi].conjugate()
    return P


def compute_S_n(P):
    """S_n = Σ_ξ |μ̂_n(ξ)|² over coprime ξ
            = (P^++(1) + P^++(2)) + (P^--(1) + P^--(2)) + 2 Re[P^+-(1) + P^+-(2)]
    """
    return (P[('+', '+', 1)].real + P[('+', '+', 2)].real +
            P[('-', '-', 1)].real + P[('-', '-', 2)].real +
            2 * (P[('+', '-', 1)].real + P[('+', '-', 2)].real))


def compute_R_n(P):
    """R_n = M_n(1 + 3^{n-1}) using ω = e^{2πi/3}.
    Derivation in result_77_sketch.md §4:
    R_n = ω̄·[P^++(1) + P^+-(2) + P^-+(1) + P^--(2)]
        + ω·[P^++(2) + P^+-(1) + P^-+(2) + P^--(1)]
    """
    omega = cmath.exp(2j * cmath.pi / 3)
    omega_bar = omega.conjugate()
    omega_part = (P[('+', '+', 2)] + P[('+', '-', 1)] + P[('-', '+', 2)] + P[('-', '-', 1)])
    omega_bar_part = (P[('+', '+', 1)] + P[('+', '-', 2)] + P[('-', '+', 1)] + P[('-', '-', 2)])
    return omega * omega_part + omega_bar * omega_bar_part


def main():
    print("# Build T_lead operator on class-resolved bilinear moments")
    print()

    # Compute level-n data
    pis = {}
    for k in [1, 2, 3]:
        K, coprime = build_markov_rational(k)
        pi_q = stationary_rational(K)
        pis[k] = (pi_q, coprime)

    # Compute class-resolved μ̂ and P vectors at each level
    P_vectors = {}
    for k in [1, 2, 3]:
        pi_q, coprime = pis[k]
        mu_plus, mu_minus = char_funcs_class_resolved(pi_q, coprime, k)
        P = compute_P_vector(mu_plus, mu_minus, coprime, k)
        P_vectors[k] = P

        # Verify S_n via P-formula
        S_via_P = compute_S_n(P)
        R_via_P = compute_R_n(P)

        print(f"## k = {k}: |coprime|={len(coprime)}, π_k = {[float(p) for p in pi_q]}")
        print(f"  P^++(1) = {P[('+','+',1)]:.8f},  P^++(2) = {P[('+','+',2)]:.8f}")
        print(f"  P^--(1) = {P[('-','-',1)]:.8f},  P^--(2) = {P[('-','-',2)]:.8f}")
        print(f"  P^+-(1) = {P[('+','-',1)]:.8f},  P^+-(2) = {P[('+','-',2)]:.8f}")
        print(f"  P^-+(1) = {P[('-','+',1)]:.8f},  P^-+(2) = {P[('-','+',2)]:.8f}")
        print(f"  S_n via P = {S_via_P:.10f}")
        print(f"  R_n via P (= M_n(1+3^{k-1})) = {R_via_P.real:+.10f} {R_via_P.imag:+.4f}i")
        if k >= 2:
            print(f"     -2·R_n = {(-2*R_via_P).real:.10f}  (should = S_{k} which we know)")
        print()

    # Now test R_n = -S_n/2 via Theorem 76.3 (relating M_n(1+3^{n-1}) to S_n at level n)
    # Hmm wait — Theorem 76.3 was at level n+1: S_{n+1} = -2 M_{n+1}(1+3^n).
    # So at level n, S_n = -2 M_n(1+3^{n-1}) = -2 R_n.
    # Check:
    print("# Verify Theorem 76.3 at each level: S_n = -2·R_n")
    for k in [2, 3]:
        S_n = compute_S_n(P_vectors[k])
        R_n = compute_R_n(P_vectors[k])
        print(f"  k={k}: S_n = {S_n:.10f},  -2·R_n = {(-2*R_n).real:.10f},  diff = {S_n - (-2*R_n).real:.2e}")
    print()

    # Build P-vector representation: 8 complex (or use real basis)
    # P^{ab}(c) for (a,b) ∈ {(+,+),(-,-),(+,-),(-,+)} × c ∈ {1,2}
    # Constraints: P^{ab}(c) = (P^{ba}(c))*, so P^{-+}(c) = (P^{+-}(c))*
    # Hermitian: P^{++}(c), P^{--}(c) are real.
    # So 4 real (P^{++}(1), P^{++}(2), P^{--}(1), P^{--}(2)) + 2 complex (P^{+-}(1), P^{+-}(2)) = 8 real dofs
    #
    # Build vector v_n ∈ R^8:
    # v_n = (P^{++}(1), P^{++}(2), P^{--}(1), P^{--}(2),
    #        Re P^{+-}(1), Im P^{+-}(1), Re P^{+-}(2), Im P^{+-}(2))

    def P_to_vec(P):
        return np.array([
            P[('+', '+', 1)].real,
            P[('+', '+', 2)].real,
            P[('-', '-', 1)].real,
            P[('-', '-', 2)].real,
            P[('+', '-', 1)].real,
            P[('+', '-', 1)].imag,
            P[('+', '-', 2)].real,
            P[('+', '-', 2)].imag,
        ])

    print("# v_n vectors (R^8 representation)")
    print(f"  Components: [P^++(1), P^++(2), P^--(1), P^--(2), Re P^+-(1), Im P^+-(1), Re P^+-(2), Im P^+-(2)]")
    for k in [1, 2, 3]:
        v = P_to_vec(P_vectors[k])
        print(f"  v_{k} = {[f'{x:+.6f}' for x in v]}")
        print(f"    |v_{k}| = {np.linalg.norm(v):.6f}")
    print()

    # Examine if there's a transition pattern: v_2 = T · v_1?
    # v has 8 components; the recursion T must be some 8 × 8 matrix.
    # However, level n has 2·3^{n-1} coprime ξ values, so the actual phase/frequency
    # structure depends on level. The 8-dim P representation is a PROJECTION onto
    # the {ξ mod 3} class structure, losing fine structure.
    #
    # So T_8x8 is not a true representation of the level-jumping operator.
    # The full operator acts on a HIGHER-dim space tracking individual μ̂_n(ξ).
    #
    # Still, we can examine the 8-dim "moment recursion" empirically.

    # Try: is there an 8 × 8 matrix T such that v_{n+1} = T · v_n?
    # 3 vectors → 24 equations → can fit 8x8 (64 unknowns) — undetermined.
    # Need more data points. But concept checks if "ratio" pattern is consistent.

    print("# Ratios v_{n+1} / v_n component-wise:")
    v1 = P_to_vec(P_vectors[1])
    v2 = P_to_vec(P_vectors[2])
    v3 = P_to_vec(P_vectors[3])
    for i in range(8):
        r12 = v2[i] / v1[i] if abs(v1[i]) > 1e-10 else float('nan')
        r23 = v3[i] / v2[i] if abs(v2[i]) > 1e-10 else float('nan')
        print(f"  comp {i}: v_2/v_1 = {r12:+.6f},  v_3/v_2 = {r23:+.6f}")
    print()


if __name__ == "__main__":
    main()
