| Metric | C++ (g++) | C# (Roslyn) | Rust (rustc) |
|---|---|---|---|
| Mean errors per injected fault (EPF) | 1.44 | 1.50 | 1.03 |
| First-error localization hit, primary span (FLH) | 100.0% | 100.0% | 84.4% |
| First-error localization hit, any labelled span (FLH-L) | 100.0% | 100.0% | 90.6% |
| Mean off-root diagnostics (ORD) | 0.22 | 0.03 | 0.19 |
| Expected-token stated (ET) | 87.5% | 84.4% | 62.5% |
| Machine-applicable fix-it present (FIX) | 21.9% | 0.0% | 25.0% |
| Mean words in first message (MLW) | 4.63 | 4.81 | 4.38 |
| Valid mutants (n) | 32 | 32 | 32 |
| Median EPF | 1.00 | 1.00 | 1.00 |

Per-operator mean EPF:

| Operator | C++ (g++) | C# (Roslyn) | Rust (rustc) |
|---|---|---|---|
| M1 Missing statement terminator (statement followed by another statement) | 1.75 | 1.00 | 1.00 |
| M2 Missing closing brace | 1.00 | 1.00 | 1.00 |
| M3 Extra closing brace | 1.00 | 1.00 | 1.00 |
| M4 Missing closing parenthesis | 1.00 | 1.00 | 1.00 |
| M5 Misspelled keyword | 1.00 | 1.75 | 1.00 |
| M6 Invalid identifier in declaration | 2.50 | 2.50 | 1.00 |
| M7 Missing operand | 1.00 | 1.00 | 1.25 |
| M8 Unterminated string literal | 2.25 | 2.75 | 1.00 |

Paired analysis on n = 32 program-operator pairs.
- Friedman test on n_err: chi2 = 11.78, p = 0.002763
  - C++ (g++) vs C# (Roslyn): Wilcoxon p = 0.5637, Holm-adj. p = 0.5637, dominance = -0.03
  - C++ (g++) vs Rust (rustc): Wilcoxon p = 0.005043, Holm-adj. p = 0.01513, dominance = +0.31
  - C# (Roslyn) vs Rust (rustc): Wilcoxon p = 0.00609, Holm-adj. p = 0.01513, dominance = +0.28
- Friedman test on off_root: chi2 = 3.50, p = 0.1738
  - C++ (g++) vs C# (Roslyn): Wilcoxon p = 0.08357, Holm-adj. p = 0.1763, dominance = +0.12
  - C++ (g++) vs Rust (rustc): Wilcoxon p = 0.7762, Holm-adj. p = 0.7762, dominance = -0.03
  - C# (Roslyn) vs Rust (rustc): Wilcoxon p = 0.05878, Holm-adj. p = 0.1763, dominance = -0.16
