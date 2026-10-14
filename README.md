# Syntax-error benchmark for C++, C# and Rust compilers (ICIS 2026)

Replication package for "Comparative Analysis of Syntax Error Handling and
Parser Accuracy in C++, C#, and Rust Compilers".

Compilers used: g++ 13.3.0, Roslyn (.NET SDK 10.0.402), rustc 1.99.0.

## Contents
- icis_bench.py : base programs, 8 mutation operators, compiler runner, metrics, statistics
- results.csv   : raw results (96 faulty programs)
- summary.md    : metrics and statistical tests reported in the paper
- cases/        : generated base programs and mutants

## Reproduce
pip install scipy
python icis_bench.py gen          # generate the 96 mutants
python icis_bench.py run cpp cs rs  # needs g++, dotnet SDK and rustc
python icis_bench.py analyze      # metrics + Friedman / Wilcoxon-Holm tests
python icis_bench.py loc          # readability/writability proxies
