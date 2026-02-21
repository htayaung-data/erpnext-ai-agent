import json
from pathlib import Path
from collections import defaultdict, deque

META = Path("impl_factory/04_automation/logs/doctype_meta.json")
OUT  = Path("impl_factory/02_seed_data/_templates/IMPORT_ORDER_FROM_META.md")

DOCTYPES = [
    "Branch","Brand","UOM","Item Group","Price List","Territory","Customer Group",
    "Supplier","Customer","Sales Person","Department","Designation","Employee",
    "Warehouse","Cost Center","Mode of Payment","Item","Item Price"
]

def main():
    meta = json.loads(META.read_text(encoding="utf-8"))

    # Build dependency graph: dt -> depends_on (only within our list)
    deps = {dt: set() for dt in DOCTYPES}
    for dt in DOCTYPES:
        for lf in meta[dt].get("link_fields", []):
            target = (lf.get("options") or "").strip()
            if target in deps and target != dt:
                deps[dt].add(target)

    # Kahn topo sort
    indeg = {dt: 0 for dt in DOCTYPES}
    rev = defaultdict(set)
    for dt, dset in deps.items():
        indeg[dt] = len(dset)
        for d in dset:
            rev[d].add(dt)

    q = deque([dt for dt in DOCTYPES if indeg[dt] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for nxt in rev[n]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    # If cycle, fallback to given list
    if len(order) != len(DOCTYPES):
        order = DOCTYPES[:]

    lines = []
    lines.append("# Import Order (Derived from ERPNext Meta)\n")
    lines.append("This order is auto-derived from Link-field dependencies.\n")
    for i, dt in enumerate(order, 1):
        lines.append(f"{i}. {dt}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote:", OUT)

if __name__ == "__main__":
    main()
