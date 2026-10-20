from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "charts" / "level_1_agent_internals.svg"

WIDTH = 1600
HEIGHT = 940


def wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def card(x: int, y: int, w: int, h: int, title: str, subtitle: str, accent: str) -> str:
    parts = [
        "<g>",
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="#d8dee8" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="{accent}"/>',
    ]
    text_y = y + 38
    for line in wrap(title, 26):
        parts.append(f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="title">{escape(line)}</text>')
        text_y += 22
    text_y += 9
    for line in wrap(subtitle, 34)[:2]:
        parts.append(f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="subtitle">{escape(line)}</text>')
        text_y += 19
    parts.append("</g>")
    return "\n".join(parts)


def pill(x: int, y: int, w: int, label: str, accent: str) -> str:
    return "\n".join(
        [
            "<g>",
            f'<rect x="{x}" y="{y}" width="{w}" height="44" rx="22" fill="#ffffff" stroke="#d8dee8" stroke-width="1.5"/>',
            f'<circle cx="{x + 25}" cy="{y + 22}" r="7" fill="{accent}"/>',
            f'<text x="{x + 44}" y="{y + 28}" class="pill-text">{escape(label)}</text>',
            "</g>",
        ]
    )


def arrow(x1: int, y1: int, x2: int, y2: int, label: str | None = None, dashed: bool = False) -> str:
    cls = "arrow dashed" if dashed else "arrow"
    parts = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#arrowhead)"/>']
    if label:
        parts.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 14}" text-anchor="middle" class="label">{escape(label)}</text>')
    return "\n".join(parts)


def generate_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Level 1 Multi-Agent Architecture with Agent Internals</title>
  <desc id="desc">A cleaner Level 1 architecture diagram showing inputs, three agents, shared context, data outputs, and the feedback loop.</desc>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#475569"/>
    </marker>
    <style>
      .bg {{ fill: #f8fafc; }}
      .band {{ fill: #ffffff; stroke: #e2e8f0; stroke-width: 2; }}
      .band-title {{ font: 700 17px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .eyebrow {{ font: 600 18px Arial, sans-serif; fill: #2563eb; letter-spacing: 0; }}
      .heading {{ font: 700 34px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .subheading {{ font: 400 17px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .title {{ font: 700 18px Arial, sans-serif; fill: #111827; letter-spacing: 0; }}
      .subtitle {{ font: 400 14px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .pill-text {{ font: 600 14px Arial, sans-serif; fill: #334155; letter-spacing: 0; }}
      .label {{ font: 600 13px Arial, sans-serif; fill: #64748b; letter-spacing: 0; }}
      .arrow {{ stroke: #475569; stroke-width: 2.4; stroke-linecap: round; }}
      .dashed {{ stroke-dasharray: 7 7; }}
      .loop {{ fill: none; stroke: #64748b; stroke-width: 2.4; stroke-dasharray: 7 7; stroke-linecap: round; }}
      .boundary {{ fill: #fefce8; stroke: #facc15; stroke-width: 2; stroke-dasharray: 8 8; }}
      .boundary-text {{ font: 700 14px Arial, sans-serif; fill: #854d0e; letter-spacing: 0; }}
      .note {{ font: 400 14px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
    </style>
  </defs>

  <rect class="bg" width="{WIDTH}" height="{HEIGHT}"/>
  <text x="70" y="70" class="eyebrow">Level 1 Architecture</text>
  <text x="70" y="112" class="heading">Agent Internals and Data Boundaries</text>
  <text x="70" y="146" class="subheading">A cleaner view of what each agent consumes and produces before the final client report.</text>

  <rect x="60" y="190" width="1480" height="118" rx="16" class="band"/>
  <text x="88" y="226" class="band-title">Inputs</text>
  {pill(110, 248, 230, "Client brief", "#2563eb")}
  {pill(370, 248, 260, "Meetings and emails", "#2563eb")}
  {pill(660, 248, 260, "Client history", "#0891b2")}
  {pill(950, 248, 260, "Company product decks", "#7c3aed")}
  {pill(1240, 248, 230, "Uploaded files", "#f59e0b")}

  <rect x="60" y="360" width="1480" height="252" rx="16" class="band"/>
  <text x="88" y="396" class="band-title">Agent Collaboration</text>
  {card(130, 432, 280, 126, "PM Agent", "Frames client problem and report angle", "#0891b2")}
  {card(520, 432, 280, 126, "BA Agent", "Turns requirements into analysis asks", "#16a34a")}
  {card(910, 432, 280, 126, "DA Agent", "Runs Python analysis and charts", "#f59e0b")}
  {card(1300, 432, 180, 126, "PM Report", "Client-ready narrative", "#7c3aed")}

  {arrow(410, 495, 520, 495, "requirements")}
  {arrow(800, 495, 910, 495, "analysis ask")}
  {arrow(1190, 495, 1300, 495, "approved findings")}
  <path d="M1050 578 C1050 654 660 654 660 578" class="loop" marker-end="url(#arrowhead)"/>
  <text x="855" y="680" text-anchor="middle" class="label">BA feedback loop for recalculation</text>

  <rect x="60" y="664" width="1480" height="150" rx="16" class="band"/>
  <text x="88" y="700" class="band-title">Shared Context and Artifacts</text>
  {card(130, 724, 260, 62, "RAG Store", "retrieved document context", "#7c3aed")}
  {card(450, 724, 260, 62, "Column Profile", "schema, types, missingness", "#f59e0b")}
  {card(770, 724, 260, 62, "Numeric Summaries", "aggregates, comparisons", "#f59e0b")}
  {card(1090, 724, 260, 62, "Chart Artifacts", "paths and chart summaries", "#f59e0b")}

  {arrow(260, 724, 260, 558, "context", True)}
  {arrow(580, 724, 1000, 558, "columns", True)}
  {arrow(900, 724, 660, 558, "evidence", True)}
  {arrow(1220, 724, 660, 558, "charts", True)}

  <rect x="470" y="842" width="660" height="50" rx="12" class="boundary"/>
  <text x="800" y="873" text-anchor="middle" class="boundary-text">Raw tables stay inside DA tooling. LLM agents see profiles, summaries, chart notes, and retrieved context.</text>
</svg>
"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_svg(), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
