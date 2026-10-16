from pathlib import Path
import pandas as pd
import subprocess

root = Path(".")
processed = root / "data" / "processed"

print("PROCESSED FILE INVENTORY")
rows = []
for path in sorted(processed.rglob("*")):
    if not path.is_file():
        continue
    info = {
        "file": str(path),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
    }
    if path.suffix.lower() == ".csv":
        try:
            info["rows"] = sum(1 for _ in open(path, encoding="utf-8-sig")) - 1
        except Exception:
            info["rows"] = "unreadable"
    rows.append(info)

inventory = pd.DataFrame(rows)
print(inventory.to_string(index=False))
print("\nTotal processed size MB:", round(inventory["size_mb"].sum(), 2))

print("\nGIT STATUS")
result = subprocess.run(
    ["git", "status", "--short"],
    capture_output=True,
    text=True,
)
print(result.stdout or "(clean working tree)")
if result.stderr:
    print(result.stderr)

print("\nGITIGNORE")
ignore = root / ".gitignore"
print(ignore.read_text(encoding="utf-8") if ignore.exists() else "(no .gitignore found)")
