import json
import sys
from pathlib import Path

def main():
    p = Path("data/usage-data.json")
    if not p.exists():
        print("data/usage-data.json not found")
        sys.exit(2)

    with p.open('r', encoding='utf-8') as f:
        d = json.load(f)

    results = []
    metrics = d.get("metrics", {})
    for cap, k in metrics.items():
        used = k.get("used", 0)
        limit = k.get("limit", 0)
        stored = k.get("percentage")
        computed = None
        if limit:
            computed = (used / limit) * 100
        else:
            computed = None

        results.append({
            "cap": cap,
            "used": used,
            "limit": limit,
            "computed": round(computed, 1) if computed is not None else None,
            "stored": stored
        })

    mismatches = [r for r in results if r["computed"] is not None and abs(r["computed"] - (r["stored"] or 0)) > 0.1]

    for r in results:
        print(f"{r['cap']}: used={r['used']}, limit={r['limit']}, computed={r['computed']}, stored={r['stored']}")

    if mismatches:
        print("\nMISMATCHES:")
        for m in mismatches:
            print(f"- {m['cap']}: computed={m['computed']}, stored={m['stored']}")
        sys.exit(1)
    else:
        print("\nAll percentages match (within 0.1%).")
        sys.exit(0)

if __name__ == '__main__':
    main()