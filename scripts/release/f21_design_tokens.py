"""JIANSHI F2.1 / G1 semantic design tokens (stdlib, no runtime I/O).

Only authored CSS is emitted. Keep page templates stable while centralizing
new features' theme; older views can migrate token-by-token.
"""
from __future__ import annotations

from collections import OrderedDict

TOKENS = OrderedDict([
    ("bg-dark", "#081120"),
    ("bg-light", "#F6F8FC"),
    ("surface", "#FFFFFF"),
    ("text-main", "#132038"),
    ("text-muted", "#64748B"),
    ("border", "#E0E7F2"),
    ("accent-blue", "#538DFF"),
    ("accent-purple", "#9975FF"),
    ("radius-card", "16px"),
    ("radius-control", "12px"),
    ("content-max", "1180px"),
])

# Bounded semantic token injection for first G1 rollout, not blanket rebranding.
# Do not use wildcards or override legacy research page CSS.
SELECTORS = (
    "html{scroll-padding-top:80px}",
    "body{color:var(--js21-text-main)}",
    ".hero{background:var(--js21-bg-dark)}",
    ".top{background:var(--js21-bg-dark)}",
    ".card{border-color:var(--js21-border);border-radius:var(--js21-radius-card)}",
    ".card p,.lead{color:var(--js21-text-muted)}",
    ".tool-panel{border-color:var(--js21-border);border-radius:var(--js21-radius-card)}",
    "#j2 .j2-mast{background:var(--js21-bg-dark)}",
    "#j2 .j2-content{background:var(--js21-bg-light)}",
    "#j2 .j2-project,#j2 .j2-solution{border-color:var(--js21-border)}",
    "@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}",
)


def render_css() -> str:
    for name, value in TOKENS.items():
        if (not name or not all(c.islower() or c.isdigit() or c == "-" for c in name)
                or any(c in value for c in ";{}<>")):
            raise RuntimeError("Unsafe F2.1 design token")
    variables = "".join(f"--js21-{name}:{value};" for name, value in TOKENS.items())
    return "/* F2.1 common brand semantics; safe to append once */:root{" + variables + "}\n" + "\n".join(SELECTORS) + "\n"
