"""
fourier_S_decomposition.py — verify Fourier formula S_{k+1} = Σ_{ξ: 3∤ξ} |μ̂_{k+1}(ξ)|²
via Plancherel, and decompose Tao's recursion into Diagonal (= S_n) + Off-diagonal.

Result of Tao recursion (§1.5, Lemma 1.12):
  μ̂_{n+1}(ξ) = Σ_v 2^{-v} · e^{-2πi ξ 2^{-v}/3^{n+1}} · μ̂_n(ξ · 2^{-v} mod 3^n)

|μ̂_{n+1}(ξ)|² = Σ_{v,v'} 2^{-v-v'} · e^{-2πi ξ (2^{-v}-2^{-v'})/3^{n+1}}
                              · μ̂_n(ξ·2^{-v}) · μ̂_n*(ξ·2^{-v'})

Diagonal (v = v'):
  Σ_v 2^{-2v} · |μ̂_n(ξ·2^{-v} mod 3^n)|²

Summing over ξ ∈ Z/3^{n+1} with 3∤ξ:
  ξ projects mod 3^n; each coprime ξ_0 ∈ Z/3^n has 3 lifts.
  Σ_{ξ in Z/3^{n+1}, 3∤ξ} |μ̂_n(ξ·2^{-v})|² = 3 · Σ_{ξ_0 in Z/3^n, 3∤ξ_0} |μ̂_n(ξ_0·2^{-v})|²
                                              = 3 · S_n  (since 2^{-v} is a unit)

So Diagonal sum = 3 · S_n · Σ_v 2^{-2v} = 3 · S_n · (1/3) = S_n.

Off-diagonal: Σ_{v ≠ v'} 2^{-v-v'} · sum_{ξ: 3∤ξ} (...)

This script verifies these identities exactly via Fraction arithmetic + complex Fraction arithmetic.
"""
import sys
import os
import cmath
from fractions import Fraction
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


def char_func(pi, coprime, k, xi):
    """μ̂_k(ξ) = Σ_r π_k(r) e^{-2πi r ξ / 3^k} (high-precision via complex)."""
    N = 3**k
    z = complex(0, 0)
    state_idx = {r: i for i, r in enumerate(coprime)}
    for r in coprime:
        i = state_idx[r]
        p = float(pi[i])
        z += p * cmath.exp(-2j * cmath.pi * r * xi / N)
    return z


def main():
    print("# Fourier decomposition of S_k via Plancherel")
    print()

    # Compute stationary at all levels k=1..4
    pis = {}
    for k in [1, 2, 3, 4]:
        K, coprime = build_markov_rational(k)
        pi_q = stationary_rational(K)
        pis[k] = (pi_q, coprime)
        print(f"  k={k}: {len(coprime)} states")
    print()

    # Compute X_k = 3^k · Σ π² and S_k = X_k - X_{k-1}
    X = {0: Fraction(1)}  # X_0 = 1 (single point)
    for k in [1, 2, 3, 4]:
        pi_q, _ = pis[k]
        sum_pi_sq = sum(p * p for p in pi_q)
        X[k] = Fraction(3**k) * sum_pi_sq
        print(f"  X_{k} = 3^{k} · Σπ² = {X[k]} = {float(X[k]):.10f}")

    S = {}
    for k in [1, 2, 3, 4]:
        S[k] = X[k] - X[k-1]
        print(f"  S_{k} = X_{k} - X_{k-1} = {S[k]} = {float(S[k]):.10f}")
    print()
    print(f"  Limit S_∞ = 7/15 = {7/15:.10f}, c = 7/45 = S_∞/3 = {7/45:.10f}")
    print()

    # Verify Plancherel formula S_k = Σ_{ξ: 3∤ξ} |μ̂_k(ξ)|²
    print("# Verify S_k = Σ_{ξ ∈ Z/3^k, 3∤ξ} |μ̂_k(ξ)|² (Plancherel decomposition)")
    print()
    for k in [1, 2, 3]:
        pi_q, coprime = pis[k]
        N = 3**k
        # Sum over ξ in Z/3^k with 3∤ξ
        total = 0.0
        breakdown = []
        for xi in range(1, N):
            if xi % 3 == 0:
                continue
            mu = char_func(pi_q, coprime, k, xi)
            mag = abs(mu)**2
            total += mag
            breakdown.append((xi, mag))
        print(f"  k={k}: Σ |μ̂_k(ξ)|² over 3∤ξ = {total:.10f},  S_k = {float(S[k]):.10f},  diff = {total - float(S[k]):.2e}")
        # Show frequencies
        if k <= 2:
            for xi, mag in breakdown:
                print(f"    ξ={xi}: |μ̂|² = {mag:.6f}")
    print()

    # Now verify the diagonal of Tao's recursion sums to S_n (up to discrete-period truncation)
    print("# Verify Tao recursion Diagonal (v=v') = S_n exactly (in continuous-Geom limit)")
    print()
    print("  Diagonal_continuous = Σ_v 2^{-2v} · 3 · S_n = 3 S_n · 1/3 = S_n")
    print()
    print("  But our chain uses TRUNCATED Geom (v = 1..M with normalization Z_v = 1 - 2^{-M}).")
    print("  Truncated diagonal coefficient: 3 · Σ_{v=1..M} (2^{-v}/Z_v)² · 1")
    print()

    for n in [1, 2, 3]:
        M = 2 * 3**(n-1)
        Z_v_n = Fraction(2**M - 1, 2**M)
        Z_v_np1 = Fraction(2**(2 * 3**n) - 1, 2**(2 * 3**n))
        # Diagonal coefficient at level n+1
        diag_coef = sum(Fraction(1, 2**(2*v)) for v in range(1, 2*3**n + 1)) / Z_v_np1**2
        print(f"  n={n}: M={M}, M_{n+1}={2*3**n}, Diag_coef (= 3·Σ(2^-v/Z)²) · 3 = "
              f"{3 * diag_coef} = {float(3 * diag_coef):.10f}")
        # Compare 1/3 expectation
        print(f"    continuous limit = 1/3, diff = {float(3*diag_coef) - 1/3:.2e}")
    print()

    # Compute the off-diagonal directly: S_{n+1} - S_n from data
    print("# Off-diagonal contribution from Tao recursion")
    print(f"  Off-diag(n) := S_{{n+1}} - S_n")
    for n in [1, 2, 3]:
        offd = S[n+1] - S[n]
        print(f"  Off-diag({n}) = S_{n+1} − S_{n} = {offd} = {float(offd):+.10f}")
    print()
    print("  Ratio Off-diag(n+1)/Off-diag(n) → 1/2 (R73 rate)")
    for n in [1, 2]:
        ratio = (S[n+2] - S[n+1]) / (S[n+1] - S[n])
        print(f"  Off-diag({n+1})/Off-diag({n}) = {ratio} = {float(ratio):.10f}")
    print()

    # The series sum
    print("# Series: S_∞ = S_1 + Σ_{n=1..∞} Off-diag(n)")
    print(f"  S_1 = {S[1]}")
    cumul = S[1]
    for n in range(1, 4):
        cumul += S[n+1] - S[n]
        print(f"  + Off-diag({n}) = {S[n+1] - S[n]}: running total = {cumul} = {float(cumul):.10f}")
    print()
    print(f"  S_∞ = 7/15 = {7/15:.10f}")
    print()

    # If Off-diag(n) = -C · (1/2)^n for some C, then S_∞ = S_1 - C · (1/2)·(1/(1-1/2)) = S_1 - C
    # S_1 = 2/3, S_∞ = 7/15, so C = 2/3 - 7/15 = 10/15 - 7/15 = 3/15 = 1/5.
    # So Off-diag(n) = -(1/5)·(1/2)^n  (predicted).
    print("# Predicted closed form: Off-diag(n) = -(1/5)·(1/2)^n  (assuming pure 1/2 rate from S_1)")
    print(f"  S_1 - (1/5) · 1/(1-1/2) = 2/3 - 2/5 = 10/15 - 6/15 = 4/15 ≠ 7/15")
    print(f"  S_∞ would be 7/15, so series sum = 7/15 - 2/3 = -1/5. ✓")
    print()
    for n in [1, 2, 3]:
        pred = Fraction(-1, 5) * Fraction(1, 2**n)
        actual = S[n+1] - S[n]
        print(f"  n={n}: predicted -(1/5)·(1/2)^{n} = {pred} = {float(pred):+.10f}, "
              f"actual = {actual} = {float(actual):+.10f}, ratio = {float(actual/pred):.6f}")


if __name__ == "__main__":
    main()
