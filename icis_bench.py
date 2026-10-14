#!/usr/bin/env python3
"""
ICIS 2026 - Syntax-error benchmark for C++ (g++), C# (Roslyn via dotnet) and Rust (rustc).

Usage
  python3 icis_bench.py gen                 # write base programs + 96 mutants into ./cases
  python3 icis_bench.py run [cpp cs rs]     # compile every case with the available compilers -> results.csv
  python3 icis_bench.py analyze             # metrics + statistics -> summary.md
  python3 icis_bench.py loc                 # readability/writability proxies of the valid base programs

Design: 4 base programs x 8 mutation operators = 32 faulty programs per language, exactly ONE injected
syntax fault per program. Ground-truth line = line where the fault was injected (+/-1 tolerance).
"""
import csv, glob, json, os, re, shutil, subprocess, sys, statistics, itertools

ROOT = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(ROOT, "cases")
EXT = {"cpp": "cpp", "cs": "cs", "rs": "rs"}

# ----------------------------------------------------------------------------- base programs (K&R brace style everywhere)
BASE = {
"P1": {  # arithmetic helper + loop + branching
"cpp": '''#include <iostream>

int add(int a, int b) {
    return a + b;
}

int main() {
    int total = 0;
    for (int i = 1; i <= 10; i++) {
        total = add(total, i);
    }
    if (total > 50) {
        std::cout << "large " << total << std::endl;
    } else {
        std::cout << "small " << total << std::endl;
    }
    return 0;
}
''',
"cs": '''using System;

class Program {
    static int Add(int a, int b) {
        return a + b;
    }

    static void Main() {
        int total = 0;
        for (int i = 1; i <= 10; i++) {
            total = Add(total, i);
        }
        if (total > 50) {
            Console.WriteLine("large " + total);
        } else {
            Console.WriteLine("small " + total);
        }
    }
}
''',
"rs": '''fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    let mut total: i32 = 0;
    for i in 1..=10 {
        total = add(total, i);
    }
    if total > 50 {
        println!("large {}", total);
    } else {
        println!("small {}", total);
    }
}
'''},
"P2": {  # class / struct with methods
"cpp": '''#include <iostream>
#include <string>

class Counter {
public:
    Counter(std::string name) : name_(name), value_(0) {}
    void increment(int step) {
        value_ = value_ + step;
    }
    int get() const {
        return value_;
    }
private:
    std::string name_;
    int value_;
};

int main() {
    Counter c("clicks");
    c.increment(3);
    c.increment(4);
    std::cout << c.get() << std::endl;
    return 0;
}
''',
"cs": '''using System;

class Counter {
    private string name;
    private int value;
    public Counter(string name) {
        this.name = name;
        this.value = 0;
    }
    public void Increment(int step) {
        this.value = this.value + step;
    }
    public int Get() {
        return this.value;
    }
}

class Program {
    static void Main() {
        Counter c = new Counter("clicks");
        c.Increment(3);
        c.Increment(4);
        Console.WriteLine(c.Get());
    }
}
''',
"rs": '''struct Counter {
    name: String,
    value: i32,
}

impl Counter {
    fn new(name: &str) -> Counter {
        Counter { name: name.to_string(), value: 0 }
    }
    fn increment(&mut self, step: i32) {
        self.value = self.value + step;
    }
    fn get(&self) -> i32 {
        return self.value;
    }
}

fn main() {
    let mut c = Counter::new("clicks");
    c.increment(3);
    c.increment(4);
    println!("{}", c.get());
}
'''},
"P3": {  # collection traversal with while loop
"cpp": '''#include <iostream>
#include <vector>

int sum(const std::vector<int>& values) {
    int result = 0;
    int idx = 0;
    while (idx < static_cast<int>(values.size())) {
        result = result + values[idx];
        idx = idx + 1;
    }
    return result;
}

int main() {
    std::vector<int> data = {4, 8, 15, 16, 23, 42};
    int s = sum(data);
    std::cout << "sum=" << s << std::endl;
    return 0;
}
''',
"cs": '''using System;
using System.Collections.Generic;

class Program {
    static int Sum(List<int> values) {
        int result = 0;
        int idx = 0;
        while (idx < values.Count) {
            result = result + values[idx];
            idx = idx + 1;
        }
        return result;
    }

    static void Main() {
        List<int> data = new List<int> { 4, 8, 15, 16, 23, 42 };
        int s = Sum(data);
        Console.WriteLine("sum=" + s);
    }
}
''',
"rs": '''fn sum(values: &Vec<i32>) -> i32 {
    let mut result: i32 = 0;
    let mut idx: usize = 0;
    while idx < values.len() {
        result = result + values[idx];
        idx = idx + 1;
    }
    return result;
}

fn main() {
    let data: Vec<i32> = vec![4, 8, 15, 16, 23, 42];
    let s = sum(&data);
    println!("sum={}", s);
}
'''},
"P4": {  # nested branching + string-returning function
"cpp": '''#include <iostream>
#include <string>

int maxOf(int a, int b) {
    if (a > b) {
        return a;
    }
    return b;
}

std::string label(int n) {
    if (n % 2 == 0) {
        return "even";
    } else {
        return "odd";
    }
}

int main() {
    int m = maxOf(7, 12);
    std::string tag = label(m);
    std::cout << m << " is " << tag << std::endl;
    return 0;
}
''',
"cs": '''using System;

class Program {
    static int MaxOf(int a, int b) {
        if (a > b) {
            return a;
        }
        return b;
    }

    static string Label(int n) {
        if (n % 2 == 0) {
            return "even";
        } else {
            return "odd";
        }
    }

    static void Main() {
        int m = MaxOf(7, 12);
        string tag = Label(m);
        Console.WriteLine(m + " is " + tag);
    }
}
''',
"rs": '''fn max_of(a: i32, b: i32) -> i32 {
    if a > b {
        return a;
    }
    return b;
}

fn label(n: i32) -> String {
    if n % 2 == 0 {
        return String::from("even");
    } else {
        return String::from("odd");
    }
}

fn main() {
    let m = max_of(7, 12);
    let tag = label(m);
    println!("{} is {}", m, tag);
}
'''},
}

# ----------------------------------------------------------------------------- mutation operators
OPS = {
 "M1": "Missing statement terminator (statement followed by another statement)",
 "M2": "Missing closing brace",
 "M3": "Extra closing brace",
 "M4": "Missing closing parenthesis",
 "M5": "Misspelled keyword",
 "M6": "Invalid identifier in declaration",
 "M7": "Missing operand",
 "M8": "Unterminated string literal",
}

def mutate(op, src):
    """Return (mutated_source, root_line(1-based), accepted_lines:set). None if operator not applicable."""
    L = src.split("\n")
    if L and L[-1] == "":
        L = L[:-1]
    n = len(L)
    def first(pred, rng=None):
        for i in (rng or range(n)):
            if pred(L[i]):
                return i
        return None
    if op == "M1":
        def m1(k):
            if not re.match(r"^\s+(?!return\b|for\b).*[=(].*;\s*$", L[k]): return False
            nxt = next((L[j].strip() for j in range(k + 1, n) if L[j].strip()), "")
            return nxt != "" and not nxt.startswith("}")
        i = next((k for k in range(n) if m1(k)), None)
        if i is None: return None
        L[i] = re.sub(r";\s*$", "", L[i]); root = i + 1; acc = {root - 1, root, root + 1}
    elif op == "M2":
        idx = [i for i in range(n) if L[i] == "}"]
        if not idx: return None
        i = idx[-1]; del L[i]; root = i + 1; acc = {root - 1, root, root + 1, len(L), len(L) + 1}
    elif op == "M3":
        L.append("}"); root = len(L); acc = {root - 1, root, root + 1}
    elif op == "M4":
        i = first(lambda s: re.search(r"\(.*\)\s*;\s*$", s))
        if i is None: return None
        L[i] = re.sub(r"\)(\s*;\s*)$", r"\1", L[i]); root = i + 1; acc = {root - 1, root, root + 1}
    elif op == "M5":
        i = first(lambda s: re.match(r"^\s+return\b", s))
        if i is None: return None
        L[i] = L[i].replace("return", "retrun", 1); root = i + 1; acc = {root - 1, root, root + 1}
    elif op == "M6":
        pat = r"^(\s+(?:int|let mut|let|Counter|std::vector<int>|List<int>|string|std::string)\s+)(\w+)(\s*(?:=|;|:))"
        i = first(lambda s: re.match(pat, s))
        if i is None: return None
        L[i] = re.sub(pat, lambda m: m.group(1) + "1" + m.group(2) + m.group(3), L[i], count=1)
        root = i + 1; acc = {root - 1, root, root + 1}
    elif op == "M7":
        i = first(lambda s: re.search(r"(\+|>) [\w\.\[\]]+", s))
        if i is None: return None
        L[i] = re.sub(r"(\+|>) [\w\.\[\]]+", r"\1 ", L[i], count=1); root = i + 1; acc = {root - 1, root, root + 1}
    elif op == "M8":
        i = first(lambda s: s.count('"') >= 2)
        if i is None: return None
        a = L[i].index('"'); b = L[i].index('"', a + 1)
        L[i] = L[i][:b] + L[i][b + 1:]; root = i + 1; acc = {root - 1, root, root + 1}
    else:
        raise ValueError(op)
    return "\n".join(L) + "\n", root, acc

def gen():
    shutil.rmtree(CASES, ignore_errors=True)
    meta = []
    for p, langs in BASE.items():
        for lang, src in langs.items():
            d = os.path.join(CASES, lang, p); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, f"base.{EXT[lang]}"), "w").write(src)
            for op in OPS:
                r = mutate(op, src)
                if r is None:
                    print("not applicable:", p, lang, op); continue
                m, root, acc = r
                open(os.path.join(d, f"{op}.{EXT[lang]}"), "w").write(m)
                meta.append(dict(lang=lang, prog=p, op=op, root=root, accepted=sorted(acc), nlines=len(m.splitlines())))
    json.dump(meta, open(os.path.join(CASES, "meta.json"), "w"), indent=1)
    print("generated", len(meta), "mutants")

# ----------------------------------------------------------------------------- compilers
def which(x): return shutil.which(x)

def compiler_available(lang):
    if lang == "cpp": return which("g++") is not None
    if lang == "rs": return which("rustc") is not None
    if lang == "cs": return which("dotnet") is not None
    return False

def version(lang):
    try:
        if lang == "cpp": return subprocess.run(["g++", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        if lang == "rs": return subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip()
        if lang == "cs": return "dotnet SDK " + subprocess.run(["dotnet", "--version"], capture_output=True, text=True).stdout.strip()
    except Exception as e:
        return f"unknown ({e})"

def compile_case(lang, path):
    """Return list of diagnostics dicts: line, msg, fixit(bool)."""
    diags = []
    if lang == "cpp":
        p = subprocess.run(["g++", "-std=c++17", "-fsyntax-only", "-fdiagnostics-parseable-fixits", "-fno-diagnostics-color", path],
                           capture_output=True, text=True, timeout=120)
        out = p.stderr
        fix_lines = set()
        for m in re.finditer(r'^fix-it:".*?":\{(\d+):\d+-\d+:\d+\}:', out, re.M):
            fix_lines.add(int(m.group(1)))
        for m in re.finditer(r"^.+?:(\d+):(\d+): (?:fatal )?error: (.*)$", out, re.M):
            diags.append(dict(line=int(m.group(1)), msg=m.group(3), fixit=False))
        has_fix = bool(fix_lines)
        return diags, has_fix, p.returncode, p.stderr
    if lang == "rs":
        import tempfile
        tmpd = tempfile.mkdtemp(prefix="rsout_")
        p = subprocess.run(["rustc", "--edition", "2021", "--emit=metadata", "--crate-type=bin", "--out-dir", tmpd,
                            "--error-format=json", path], capture_output=True, text=True, timeout=120)
        shutil.rmtree(tmpd, ignore_errors=True)
        has_fix = False
        for ln in p.stderr.splitlines():
            ln = ln.strip()
            if not ln.startswith("{"): continue
            try: d = json.loads(ln)
            except Exception: continue
            if d.get("level") != "error" or not d.get("spans"): continue
            prim = [s for s in d["spans"] if s.get("is_primary")] or d["spans"]
            diags.append(dict(line=prim[0]["line_start"], msg=d["message"], fixit=False,
                              lines=sorted({s_["line_start"] for s_ in d["spans"]})))
            for ch in d.get("children", []):
                for s in ch.get("spans", []):
                    if s.get("suggested_replacement") is not None: has_fix = True
        return diags, has_fix, p.returncode, p.stderr
    if lang == "cs":
        d = os.path.join(os.path.dirname(path), "_build_" + os.path.basename(path).split(".")[0])
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        shutil.copy(path, os.path.join(d, "Program.cs"))
        tfm = "net" + subprocess.run(["dotnet", "--version"], capture_output=True, text=True).stdout.split(".")[0] + ".0"
        open(os.path.join(d, "p.csproj"), "w").write(
            f'<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>{tfm}</TargetFramework>'
            '<Nullable>disable</Nullable><ImplicitUsings>disable</ImplicitUsings><EnableDefaultCompileItems>false</EnableDefaultCompileItems>'
            '</PropertyGroup><ItemGroup><Compile Include="Program.cs"/></ItemGroup></Project>')
        p = subprocess.run(["dotnet", "build", "-nologo", "-v:q", "-clp:NoSummary", "--configuration", "Debug"],
                           cwd=d, capture_output=True, text=True, timeout=300)
        seen = set()
        for m in re.finditer(r"Program\.cs\((\d+),(\d+)\): error (CS\d+): (.*?)(?: \[.*\])?$", p.stdout + p.stderr, re.M):
            key = (m.group(1), m.group(2), m.group(3), m.group(4))
            if key in seen: continue
            seen.add(key); diags.append(dict(line=int(m.group(1)), msg=f"{m.group(3)}: {m.group(4)}", fixit=False))
        shutil.rmtree(d, ignore_errors=True)
        return diags, False, p.returncode, p.stdout + p.stderr  # Roslyn CLI emits no machine-readable fix-its
    raise ValueError(lang)

def run(langs):
    meta = json.load(open(os.path.join(CASES, "meta.json")))
    rows = []
    for lang in langs:
        if not compiler_available(lang):
            print(f"[skip] compiler for {lang} not found"); continue
        print(f"[{lang}] {version(lang)}")
        # sanity: base programs must compile cleanly
        for p in BASE:
            diags, _, rc, raw = compile_case(lang, os.path.join(CASES, lang, p, f"base.{EXT[lang]}"))
            if diags or rc != 0:
                print(f"  !! base program {p}/{lang} does NOT compile cleanly (rc={rc}) -> fix before trusting results", diags[:2])
                print("     raw output:", raw.strip()[:400].replace("\n", " | "))
        for m in [x for x in meta if x["lang"] == lang]:
            path = os.path.join(CASES, lang, m["prog"], f"{m['op']}.{EXT[lang]}")
            diags, has_fix, rc, raw = compile_case(lang, path)
            valid = int(bool(diags))
            if not diags:
                print(f"  !! mutant {lang}/{m['prog']}/{m['op']} produced NO error diagnostic (rc={rc}) -> excluded as invalid mutant")
            acc = set(m["accepted"])
            n = len(diags)
            first_hit = int(bool(diags) and diags[0]["line"] in acc)
            any_hit = int(any(d["line"] in acc for d in diags))
            first_hit_label = int(bool(diags) and any(l in acc for l in diags[0].get("lines", [diags[0]["line"]])))
            off = sum(1 for d in diags if d["line"] not in acc)
            et = int(any(re.search(r"expect", d["msg"], re.I) for d in diags))
            words = len(re.findall(r"\w+", diags[0]["msg"])) if diags else 0
            rows.append(dict(lang=lang, prog=m["prog"], op=m["op"], n_err=n, first_hit=first_hit, any_hit=any_hit,
                             off_root=off, fixit=int(has_fix), expected_token=et, first_words=words,
                             valid=valid, first_hit_label=first_hit_label,
                             first_msg=(diags[0]["msg"][:90] if diags else ""), compiler=version(lang)))
    old = []
    f = os.path.join(ROOT, "results.csv")
    if os.path.exists(f):
        old = [r for r in csv.DictReader(open(f)) if r["lang"] not in langs]
    allrows = old + rows
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else list(old[0].keys()))
        w.writeheader(); [w.writerow(r) for r in allrows]
    print("wrote", f, len(allrows), "rows")

# ----------------------------------------------------------------------------- analysis
def analyze():
    allrows = list(csv.DictReader(open(os.path.join(ROOT, "results.csv"))))
    rows = [r for r in allrows if r.get("valid", "1") == "1"]
    excluded = len(allrows) - len(rows)
    langs = [l for l in ("cpp", "cs", "rs") if any(r["lang"] == l for r in rows)]
    name = {"cpp": "C++ (g++)", "cs": "C# (Roslyn)", "rs": "Rust (rustc)"}
    out = []
    out.append("| Metric | " + " | ".join(name[l] for l in langs) + " |")
    out.append("|---|" + "---|" * len(langs))
    def agg(l, key, fn=statistics.mean):
        v = [float(r[key]) for r in rows if r["lang"] == l]; return fn(v)
    def fmt(x, pct=False): return f"{100*x+1e-9:.1f}%" if pct else f"{x+1e-9:.2f}"
    for label, key, pct in [("Mean errors per injected fault (EPF)", "n_err", False),
                            ("First-error localization hit, primary span (FLH)", "first_hit", True),
                            ("First-error localization hit, any labelled span (FLH-L)", "first_hit_label", True),
                            ("Mean off-root diagnostics (ORD)", "off_root", False),
                            ("Expected-token stated (ET)", "expected_token", True),
                            ("Machine-applicable fix-it present (FIX)", "fixit", True),
                            ("Mean words in first message (MLW)", "first_words", False)]:
        out.append(f"| {label} | " + " | ".join(fmt(agg(l, key), pct) for l in langs) + " |")
    out.append("| Valid mutants (n) | " + " | ".join(str(sum(1 for r in rows if r["lang"] == l)) for l in langs) + " |")
    out.append("| Median EPF | " + " | ".join(fmt(agg(l, "n_err", statistics.median)) for l in langs) + " |")
    out.append("")
    out.append("Per-operator mean EPF:")
    out.append("")
    out.append("| Operator | " + " | ".join(name[l] for l in langs) + " |")
    out.append("|---|" + "---|" * len(langs))
    for op, desc in OPS.items():
        cells = []
        for l in langs:
            v = [float(r["n_err"]) for r in rows if r["lang"] == l and r["op"] == op]
            cells.append(f"{statistics.mean(v):.2f}" if v else "-")
        out.append(f"| {op} {desc} | " + " | ".join(cells) + " |")
    # statistics (paired by program x operator)
    try:
        from scipy import stats
        key = lambda r: (r["prog"], r["op"])
        by = {l: {key(r): r for r in rows if r["lang"] == l} for l in langs}
        common = sorted(set.intersection(*[set(by[l]) for l in langs])) if langs else []
        out.append("")
        if len(langs) == 3 and common:
            out.append(f"Paired analysis on n = {len(common)} program-operator pairs.")
            for metric in ("n_err", "off_root"):
                arrs = [[float(by[l][k][metric]) for k in common] for l in langs]
                fr = stats.friedmanchisquare(*arrs)
                out.append(f"- Friedman test on {metric}: chi2 = {fr.statistic:.2f}, p = {fr.pvalue:.4g}")
                pairs = list(itertools.combinations(range(3), 2))
                ps = []
                for a, b in pairs:
                    try: w = stats.wilcoxon(arrs[a], arrs[b]); p = w.pvalue
                    except ValueError: p = 1.0
                    ps.append(p)
                order = sorted(range(len(ps)), key=lambda i: ps[i]); holm = [None] * len(ps); prev = 0
                for rank, i in enumerate(order):
                    holm[i] = max(prev, min(1, ps[i] * (len(ps) - rank))); prev = holm[i]
                for (a, b), p, h in zip(pairs, ps, holm):
                    gt = sum(x > y for x, y in zip(arrs[a], arrs[b])); lt = sum(x < y for x, y in zip(arrs[a], arrs[b]))
                    delta = (gt - lt) / len(common)  # Cliff-style dominance on paired data
                    out.append(f"  - {name[langs[a]]} vs {name[langs[b]]}: Wilcoxon p = {p:.4g}, Holm-adj. p = {h:.4g}, dominance = {delta:+.2f}")
        else:
            out.append("(Inferential tests need all three compilers in results.csv.)")
    except ImportError:
        out.append("\n(scipy not installed: pip install scipy for inferential tests.)")
    open(os.path.join(ROOT, "summary.md"), "w").write("\n".join(out) + "\n")
    print("\n".join(out))

# ----------------------------------------------------------------------------- readability / writability proxies
TOK = re.compile(r'"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|::|->|=>|\.\.=|\+\+|<<|>>|<=|>=|==|!=|&&|\|\||[^\s\w]')
def loc_metrics():
    rows = []
    for lang in ("cpp", "cs", "rs"):
        loc = tok = chars = 0; idlen = []; punct = 0
        for p in BASE:
            s = BASE[p][lang]
            lines = [l for l in s.split("\n") if l.strip()]
            loc += len(lines); chars += sum(len(l.strip()) for l in lines)
            toks = TOK.findall(s); tok += len(toks)
            for t in toks:
                if re.match(r"[A-Za-z_]", t): idlen.append(len(t))
                elif not t[0].isdigit() and t[0] != '"': punct += 1
        rows.append((lang, loc, tok, chars, statistics.mean(idlen), punct / tok))
    print("lang,LOC,tokens,chars,mean_identifier_length,punctuation_token_ratio")
    for r in rows: print(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]:.2f},{r[5]:.3f}")
    return rows

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "gen": gen()
    elif cmd == "run": run(sys.argv[2:] or ["cpp", "cs", "rs"])
    elif cmd == "analyze": analyze()
    elif cmd == "loc": loc_metrics()
    else: print(__doc__)
