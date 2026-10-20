from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "docs" / "charts" / "level_2_api_deployment.svg"

WIDTH = 1680
HEIGHT = 1060


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


def box(x: int, y: int, w: int, h: int, title: str, subtitle: str, accent: str) -> str:
    parts = [
        "<g>",
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="#d8dee8" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="7" rx="3.5" fill="{accent}"/>',
    ]
    text_y = y + 36
    for line in wrap(title, 24):
        parts.append(f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="title">{escape(line)}</text>')
        text_y += 21
    text_y += 8
    for line in wrap(subtitle, 30)[:2]:
        parts.append(f'<text x="{x + w / 2}" y="{text_y}" text-anchor="middle" class="subtitle">{escape(line)}</text>')
        text_y += 18
    parts.append("</g>")
    return "\n".join(parts)


def arrow(x1: int, y1: int, x2: int, y2: int, dashed: bool = False) -> str:
    cls = "arrow dashed" if dashed else "arrow"
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#arrowhead)"/>'


def generate_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Level 2 Multi-Agent API and Kubernetes Deployment Architecture</title>
  <desc id="desc">A clean deployment-level diagram with straight connectors and no overlapping labels.</desc>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#475569"/>
    </marker>
    <style>
      .bg {{ fill: #f8fafc; }}
      .boundary {{ fill: #ffffff; stroke: #cbd5e1; stroke-width: 2; }}
      .cluster {{ fill: #f8fafc; stroke: #94a3b8; stroke-width: 2; stroke-dasharray: 8 8; }}
      .boundary-title {{ font: 700 18px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .eyebrow {{ font: 600 18px Arial, sans-serif; fill: #2563eb; letter-spacing: 0; }}
      .heading {{ font: 700 34px Arial, sans-serif; fill: #0f172a; letter-spacing: 0; }}
      .subheading {{ font: 400 17px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .title {{ font: 700 17px Arial, sans-serif; fill: #111827; letter-spacing: 0; }}
      .subtitle {{ font: 400 13.5px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
      .arrow {{ stroke: #475569; stroke-width: 2.2; stroke-linecap: round; }}
      .dashed {{ stroke-dasharray: 7 7; }}
      .lane-text {{ font: 700 13px Arial, sans-serif; fill: #64748b; letter-spacing: 0; }}
      .note {{ font: 400 14px Arial, sans-serif; fill: #475569; letter-spacing: 0; }}
    </style>
  </defs>

  <rect class="bg" width="{WIDTH}" height="{HEIGHT}"/>
  <text x="70" y="70" class="eyebrow">Level 2 Architecture</text>
  <text x="70" y="112" class="heading">API, UI, and Kubernetes Deployment View</text>
  <text x="70" y="146" class="subheading">Straight-line deployment view with UI, gateway, agent APIs, storage, and platform services.</text>

  <rect x="60" y="190" width="260" height="720" rx="16" class="boundary"/>
  <text x="88" y="226" class="boundary-title">Client Layer</text>
  {box(95, 285, 190, 94, "React UI", "chat, upload, report", "#2563eb")}
  {box(95, 445, 190, 94, "Streamlit UI", "internal demo app", "#2563eb")}

  <rect x="370" y="190" width="850" height="720" rx="16" class="cluster"/>
  <text x="398" y="226" class="boundary-title">Kubernetes Cluster</text>

  {box(420, 285, 230, 104, "Ingress / Gateway", "TLS, auth, routing", "#0f766e")}
  {box(420, 515, 230, 112, "Orchestrator API", "coordinates all agent APIs", "#0891b2")}

  {box(745, 265, 210, 104, "PM Agent API", "requirements and report", "#0891b2")}
  {box(745, 440, 210, 104, "BA Agent API", "planning and synthesis", "#16a34a")}
  {box(745, 615, 210, 104, "DA Agent API", "analysis and charts", "#f59e0b")}

  {box(1010, 265, 170, 84, "Vector DB", "RAG chunks", "#7c3aed")}
  {box(1010, 405, 170, 84, "Object Storage", "uploads and charts", "#f59e0b")}
  {box(1010, 545, 170, 84, "Metadata DB", "runs and status", "#16a34a")}
  {box(1010, 685, 170, 84, "Secrets", "keys and config", "#64748b")}

  <rect x="1270" y="190" width="350" height="720" rx="16" class="boundary"/>
  <text x="1298" y="226" class="boundary-title">External Platform Services</text>
  {box(1310, 285, 250, 94, "LLM Provider", "chat and embeddings", "#111827")}
  {box(1310, 445, 250, 94, "Observability", "logs, metrics, traces", "#64748b")}
  {box(1310, 605, 250, 94, "CI/CD Registry", "images and manifests", "#2563eb")}
  {box(1310, 765, 250, 94, "Auth Provider", "SSO and JWT", "#0f766e")}

  <text x="350" y="258" text-anchor="middle" class="lane-text">HTTPS</text>
  {arrow(285, 332, 420, 332)}
  {arrow(285, 492, 420, 332)}
  {arrow(535, 389, 535, 515)}

  <text x="700" y="250" text-anchor="middle" class="lane-text">Agent API Calls</text>
  {arrow(650, 571, 745, 317)}
  {arrow(650, 571, 745, 492)}
  {arrow(650, 571, 745, 667)}

  <text x="985" y="250" text-anchor="middle" class="lane-text">Shared Services</text>
  {arrow(955, 317, 1010, 307, True)}
  {arrow(955, 492, 1010, 447, True)}
  {arrow(955, 667, 1010, 447, True)}
  {arrow(650, 571, 1010, 587, True)}
  {arrow(650, 571, 1010, 727, True)}

  <text x="1245" y="258" text-anchor="middle" class="lane-text">Platform Calls</text>
  {arrow(1180, 307, 1310, 332, True)}
  {arrow(1180, 307, 1310, 492, True)}
  {arrow(1180, 727, 1310, 812, True)}
  {arrow(1180, 587, 1310, 492, True)}

  <text x="850" y="770" text-anchor="middle" class="lane-text">BA and DA iterate through orchestrated API calls</text>
  {arrow(850, 615, 850, 544, True)}
  {arrow(850, 440, 850, 369, True)}

  <g>
    <rect x="370" y="940" width="1250" height="58" rx="12" fill="#ffffff" stroke="#e2e8f0"/>
    <text x="400" y="974" class="note">Deployment principle: each agent is independently served by FastAPI and scaled as its own Kubernetes Deployment behind the orchestrator.</text>
  </g>
</svg>
"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generate_svg(), encoding="utf-8")
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
