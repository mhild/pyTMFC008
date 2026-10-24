"""Run the pytest suite against one or more running API instances and write a Markdown report.

    python scripts/test_report.py \\
        --target "PostgreSQL|http://127.0.0.1:8001|postgresql+asyncpg://app:secret@localhost:5432/app_db" \\
        --target "Oracle|http://127.0.0.1:8002|oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1" \\
        --output docs/test-report.md

Each target is "label|API base URL|DATABASE_URL" (the database URL is only used to read the server version).
"""
import argparse
import ast
import asyncio
import datetime
import os
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from importlib import metadata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_DIR = os.path.join(ROOT, "tests", "pytest")
PACKAGES = ["fastapi", "uvicorn", "pydantic", "SQLAlchemy", "alembic", "asyncpg", "oracledb", "cryptography", "httpx", "pytest"]
STATUS_ICON = {"passed": "✅ passed", "failed": "❌ failed", "error": "❌ error", "skipped": "⏭️ skipped"}


def sh(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ROOT).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


# --------------------------------------------------------------------------- #
# system information

def cpu_info() -> str:
    fields = {}
    for line in sh("lscpu").splitlines():
        key, _, value = line.partition(":")
        fields.setdefault(key.strip(), value.strip())
    model = next((v for v in (fields.get("Model name"), fields.get("Vendor ID")) if v and v != "-"), "unknown")
    if fields.get("Model name") == "-" and fields.get("Vendor ID"):
        model = f"{fields['Vendor ID']} ({fields.get('Architecture', platform.machine())}, model name not exposed to the VM)"
    return f"{model}, {fields.get('CPU(s)') or os.cpu_count()} CPUs"


def memory_info() -> str:
    try:
        with open("/proc/meminfo") as f:
            kb = int(next(line for line in f if line.startswith("MemTotal")).split()[1])
        return f"{kb / 1024 / 1024:.1f} GiB"
    except (OSError, StopIteration, ValueError):
        return "unknown"


def os_info() -> str:
    pretty = ""
    try:
        with open("/etc/os-release") as f:
            pretty = next((l.split("=", 1)[1].strip().strip('"') for l in f if l.startswith("PRETTY_NAME=")), "")
    except OSError:
        pass
    u = platform.uname()
    return f"{pretty} (Kernel {u.release}, {u.machine})" if pretty else f"{u.system} {u.release} ({u.machine})"


def git_info() -> str:
    commit = sh("git", "rev-parse", "--short", "HEAD")
    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")
    dirty = " + uncommitted changes" if sh("git", "status", "--porcelain") else ""
    return f"`{branch}` @ `{commit}`{dirty}" if commit else "unknown"


def container_images() -> list:
    out = sh("docker", "ps", "--format", "{{.Image}}\t{{.Status}}")
    return [line.split("\t") for line in out.splitlines() if line]


async def database_version(url: str) -> str:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            if engine.dialect.name == "oracle":
                version = (await conn.execute(text("SELECT banner_full FROM v$version"))).scalar()
            else:
                version = (await conn.execute(text("SELECT version()"))).scalar()
            count = (await conn.execute(text("SELECT COUNT(*) FROM service"))).scalar()
        return f"{' '.join(version.split())} – {count:,} services in table"
    except Exception as exc:  # noqa: BLE001 - report, don't fail
        return f"not reachable ({type(exc).__name__})"
    finally:
        await engine.dispose()


# --------------------------------------------------------------------------- #
# tests

def docstrings():
    """{module: (module docstring, {test function: first docstring line})} from the test sources."""
    result = {}
    for name in sorted(os.listdir(TEST_DIR)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        with open(os.path.join(TEST_DIR, name)) as f:
            tree = ast.parse(f.read())
        funcs = {
            node.name: (ast.get_docstring(node) or "").strip().splitlines()[0] if ast.get_docstring(node) else ""
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        }
        result[name[:-3]] = (ast.get_docstring(tree) or "", funcs)
    return result


def run_pytest(base_url: str):
    """-> ({(module, test id): (status, seconds, message)}, summary line)"""
    with tempfile.TemporaryDirectory() as tmp:
        junit = os.path.join(tmp, "junit.xml")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", TEST_DIR, "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"],
            capture_output=True, text=True, cwd=ROOT, env={**os.environ, "TMF_BASE_URL": base_url},
        )
        summary = (proc.stdout.strip().splitlines() or [""])[-1]
        results = OrderedDict()
        for case in ET.parse(junit).getroot().iter("testcase"):
            module = case.get("classname").rsplit(".", 1)[-1]
            status, message = "passed", ""
            for child in case:
                if child.tag in ("failure", "error", "skipped"):
                    status = {"failure": "failed"}.get(child.tag, child.tag)
                    message = (child.get("message") or "").splitlines()[0][:160]
            results[(module, case.get("name"))] = (status, float(case.get("time") or 0), message)
    return results, summary


def test_levels():
    """{module: {test function: "API" | "Unit"}}: API if the test (directly or via a fixture) uses the HTTP `client`."""
    result = {}
    for name in sorted(os.listdir(TEST_DIR)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        with open(os.path.join(TEST_DIR, name)) as f:
            funcs = [node for node in ast.parse(f.read()).body if isinstance(node, ast.FunctionDef)]
        uses = {node.name: {a.arg for a in node.args.args} for node in funcs}
        api = {"client"}
        while True:  # fixtures depending on fixtures that use the client
            more = {fixture for fixture, args in uses.items() if args & api and not fixture.startswith("test_")} - api
            if not more:
                break
            api |= more
        result[name[:-3]] = {f: "API" if args & api else "Unit" for f, args in uses.items() if f.startswith("test_")}
    return result


def describe(func: str, funcs: dict) -> str:
    """Docstring of the test, else its name as words (test_merge_patch -> "merge patch")."""
    return funcs.get(func) or func.removeprefix("test_").replace("_", " ")


def run_bench(base_url: str, db_url: str, runs: int):
    """-> (latency table, execution plans) as printed by scripts/bench.py"""
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "bench.py"), "--base-url", base_url, "--runs", str(runs), "--plans"],
        capture_output=True, text=True, cwd=ROOT, env={**os.environ, "DATABASE_URL": db_url},
    )
    if proc.returncode:
        return f"bench.py failed:\n{proc.stderr[-2000:]}", ""
    table, _, plans = proc.stdout.partition("\n=== ")
    return table.strip(), ("=== " + plans).strip() if plans else ""


def duration(seconds: float) -> str:
    """JUnit XML has millisecond resolution: shorter tests are reported as 0.000 s."""
    return "< 1 ms" if seconds < 0.001 else f"{seconds * 1000:.0f} ms"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", action="append", required=True, help="label|API base URL|DATABASE_URL")
    parser.add_argument("--output", default=os.path.join(ROOT, "docs", "test-report.md"))
    parser.add_argument("--bench-runs", type=int, default=30, help="requests per benchmark query (0: no benchmark)")
    args = parser.parse_args()
    targets = [t.split("|", 2) for t in args.target]

    runs, versions, benches = [], [], []
    for label, base_url, db_url in targets:
        print(f"Running tests against {label} ({base_url}) ...", file=sys.stderr)
        runs.append(run_pytest(base_url))
        versions.append(asyncio.run(database_version(db_url)))
    for label, base_url, db_url in targets if args.bench_runs else []:
        print(f"Running benchmark against {label} ...", file=sys.stderr)
        benches.append((label, run_bench(base_url, db_url, args.bench_runs)))

    docs = docstrings()
    levels = test_levels()
    labels = [t[0] for t in targets]
    now = datetime.datetime.now().astimezone()
    out = [
        "# Test report",
        "",
        f"Generated on {now:%Y-%m-%d %H:%M %Z} by `scripts/test_report.py`. To regenerate, see [Reproduce](#reproduce).",
        "",
        "## Result",
        "",
        "| Backend | API | Result |",
        "|---|---|---|",
    ]
    for (label, base_url, _), (_, summary) in zip(targets, runs):
        out.append(f"| {label} | `{base_url}` | {md_escape(summary)} |")

    out += ["", "## Test environment", "", "| | |", "|---|---|"]
    out += [
        f"| Code version | {git_info()} |",
        f"| Operating system | {md_escape(os_info())} |",
        f"| CPU | {md_escape(cpu_info())} |",
        f"| Memory | {memory_info()} |",
        f"| Python | {platform.python_version()} ({platform.python_implementation()}) |",
    ]
    for label, version in zip(labels, versions):
        out.append(f"| Database {label} | {md_escape(version)} |")
    for image, status in container_images():
        out.append(f"| Container | `{image}` ({status}) |")
    out.append("| Packages | " + ", ".join(f"{p} {metadata.version(p)}" for p in PACKAGES if _installed(p)) + " |")
    out += [
        "",
        "For each test run the API ran as a separate uvicorn instance (one worker, `HISTORY_ENABLED=true`: the history tests are skipped without it) on the same host as the tests.",
    ]

    # one table per test module
    keys = list(OrderedDict.fromkeys(k for results, _ in runs for k in results))
    level_of = {k: levels.get(k[0], {}).get(k[1].split("[", 1)[0], "Unit") for k in keys}
    counts = {level: sum(1 for v in level_of.values() if v == level) for level in ("API", "Unit")}
    out += [
        "", "## Test cases", "",
        "| Level | Tests | What runs |",
        "|---|---:|---|",
        f"| API | {counts['API']} | HTTP request via httpx → FastAPI → SQLAlchemy → database (end-to-end against the running API) |",
        f"| Unit | {counts['Unit']} | parser and SQL renderers only – no API, no database (run once per backend nevertheless) |",
        "",
    ]
    for module in OrderedDict.fromkeys(m for m, _ in keys):
        module_doc, funcs = docs.get(module, ("", {}))
        out += [f"### `{module}.py`", ""]
        if module_doc:
            out += ["```text", module_doc, "```", ""] if "\n" in module_doc else [module_doc, ""]
        out.append("| Test | Level | Description | " + " | ".join(labels) + " |")
        out.append("|---|---|---|" + "---|" * len(labels))
        for mod, test_id in (k for k in keys if k[0] == module):
            func = test_id.split("[", 1)[0]
            cells = []
            for results, _ in runs:
                status, seconds, message = results.get((mod, test_id), ("–", 0.0, ""))
                cell = STATUS_ICON.get(status, status) + (f" ({duration(seconds)})" if status != "–" else "")
                cells.append(cell + (f"<br>{md_escape(message)}" if message else ""))
            out.append(f"| `{md_escape(test_id)}` | {level_of[(mod, test_id)]} | {md_escape(describe(func, funcs))} | " + " | ".join(cells) + " |")
        out.append("")

    if benches:
        out += [
            "## Performance",
            "",
            f"`scripts/bench.py`: {args.bench_runs} requests per query via the HTTP API (after a warm-up), "
            "end-to-end latency including `X-Total-Count`; data from `scripts/seed.py`. "
            "The execution plans show the SQL the API generates for each query.",
            "",
        ]
        for label, (table, plans) in benches:
            out += [f"### {label}", "", "```text", table, "```", ""]
            if plans:
                out += ["<details><summary>Execution plans</summary>", "", "```text", plans, "```", "", "</details>", ""]

    out += [
        "## Not included",
        "",
        "* The Bruno collection (`tests/TMFC008`) is not part of this report (Bruno CLI not installed in the devcontainer).",
        "",
        "## Reproduce",
        "",
        "```bash",
        "docker compose up -d db oracle",
        "export PG=postgresql+asyncpg://app:secret@localhost:5432/app_db",
        "export ORA='oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1'",
        "DATABASE_URL=$PG alembic upgrade head && DATABASE_URL=$ORA alembic upgrade head",
        "HISTORY_ENABLED=true DATABASE_URL=$PG  uvicorn openapi_server.main:app --port 8001 &",
        "HISTORY_ENABLED=true DATABASE_URL=$ORA uvicorn openapi_server.main:app --port 8002 &",
        "DATABASE_URL=${PG/+asyncpg/} python scripts/seed.py --count 50000 --truncate   # data for the performance measurement",
        "DATABASE_URL=${ORA/_async/} python scripts/seed.py --count 50000 --truncate",
        'python scripts/test_report.py --target "PostgreSQL|http://127.0.0.1:8001|$PG" --target "Oracle|http://127.0.0.1:8002|$ORA"',
        "```",
        "",
    ]

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write("\n".join(out))
    print(f"Wrote {args.output}", file=sys.stderr)


def _installed(package: str) -> bool:
    try:
        metadata.version(package)
        return True
    except metadata.PackageNotFoundError:
        return False


if __name__ == "__main__":
    main()
