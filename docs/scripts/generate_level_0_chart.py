from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "charts" / "level_0_basic_flow.svg"


WIDTH = 1440
HEIGHT = 760


def text_lines(text: str, max_chars: int = 30) -> list[str]:
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


def rect_node(x: int, y: int, w: int, h: int, title: str, subtitle: str, accent: str) -> str:
    title_lines = text_lines(title, 24)
    subtitle_lines = text_lines(subtitle, 34)
    parts = [
        f'<g class="node">',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#ffffff" stroke="#d8dee8" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="{accent}"/>',
    ]
    text_y = y + 44
    for line in title_lines:
        parts.append(
            f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="title">{escape(line)}</text>'
        )
        text_y += 24
    text_y += 10
    for line in subtitle_lines[:3]:
        parts.append(
            f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="subtitle">{escape(line)}</text>'
        )
        text_y += 20
    parts.append("</g>")
    return "\n".join(parts)


def arrow(x1: int, y1: int, x2: int, y2: int, label: str | None = None) -> str:
    parts = [
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="arrow" marker-end="url(#arrowhead)"/>'
    ]
    if label:
        parts.append(
            f'<text x="{(x1 + x2) / 2}" y="{y1 - 16}" text-anchor="middle" class="arrow-label">{escape(label)}</text>'
        )
    return "\n".join(parts)


def generate_svg() -> str:
    nodes = [
        {
            "x": 80,
            "y": 270,
            "w": 210,
            "h": 140,
            "title": "Client Input",
            "subtitle": "Brief text and optional files",
            "accent": "#2563eb",
        },
        {
            "x": 350,
            "y": 270,
            "w": 220,
            "h": 140,
            "title": "Product Manager Agent",
            "subtitle": "Understands client goal and frames the requirement",
            "accent": "#0891b2",
        },
        {
            "x": 640,
            "y": 270,
            "w": 220,
            "h": 140,
            "title": "Business Analyst Agent",
            "subtitle": "Connects business questions to data-backed insights",
            "accent": "#16a34a",
        },
        {
            "x": 930,
            "y": 270,
            "w": 220,
            "h": 140,
            "title": "Data Visualizer Agent",
            "subtitle": "Calculates numbers and prepares charts",
            "accent": "#f59e0b",
        },
        {
            "x": 1210,
            "y": 270,
            "w": 170,
            "h": 140,
            "title": "Client Report",
            "subtitle": "Clear recommendations with charts and next steps",
            "accent": "#7c3aed",
        },
    ]

    node_svg = "\n".join(rect_node(**node) for node in nodes)
    arrows = "\n".join(
        [
            arrow(290, 340, 350, 340),
            arrow(570, 340, 640, 340),
            arrow(860, 340, 930, 340),
            arrow(1150, 340, 1210, 340),
            '<path d="M1040 432 C1040 520 760 520 750 432" class="feedback" marker-end="url(#arrowhead-soft)"/>',
            '<text x="895" y="558" text-anchor="middle" class="arrow-label">Insight refinement loop</text>',
            '<path d="M750 252 C760 170 1040 170 1040 252" class="feedback" marker-end="url(#arrowhead-soft)"/>',
            '<text x="895" y="156" text-anchor="middle" class="arrow-label">Analysis request and chart updates</text>',
        ]
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Level 0 Multi-Agent Architecture Flow</title>
  <desc id="desc">A simple flow showing client input moving through PM, BA, and Data Visualizer agents to produce a client report.</desc>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#475569"/>
    </marker>
    <marker id="arrowhead-soft" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/>
    </marker>
    <style>
      .bg {{ fill: #f8fafc; }}
      .eyebrow {{ font: 600 18px Arial, sans-serif; fill: #2563eb; letter-spacing: 0; }}
      .heading {{ font: 700 34px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .subheading {{ font: 400 17px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .title {{ font: 700 20px Arial, sans-serif; fill: #111827; letter-spacing: 0; }}
      .subtitle {{ font: 400 15px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .arrow {{ stroke: #475569; stroke-width: 2.5; stroke-linecap: round; }}
      .feedback {{ fill: none; stroke: #94a3b8; stroke-width: 2.5; stroke-dasharray: 7 7; stroke-linecap: round; }}
      .arrow-label {{ font: 600 14px Arial, sans-serif; fill: #64748b; letter-spacing: 0; }}
      .note-title {{ font: 700 18px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .note {{ font: 400 15px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
    </style>
  </defs>

  <rect class="bg" width="{WIDTH}" height="{HEIGHT}"/>
  <text x="72" y="78" class="eyebrow">Level 0 Architecture</text>
  <text x="72" y="122" class="heading">Multi-Agent Client Report Flow</text>
  <text x="72" y="156" class="subheading">A stakeholder-friendly view of how client input becomes a polished, data-backed report.</text>

  {arrows}
  {node_svg}

  <g>
    <rect x="80" y="615" width="1300" height="82" rx="12" fill="#ffffff" stroke="#e2e8f0"/>
    <text x="112" y="652" class="note-title">Simple promise</text>
    <text x="112" y="679" class="note">The client gives context once. The agents collaborate behind the scenes. The final output is a clear report with business meaning, evidence, charts, and next steps.</text>
  </g>
</svg>
"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_svg(), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
