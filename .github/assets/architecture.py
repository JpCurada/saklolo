"""Generate the architecture diagram: python architecture.py <aws-icons svg folder>.

Writes architecture.svg next to this file. Icons come from the aws-icons npm package
(official AWS Architecture Icons). Update the tiles here when the deployment changes.
"""

import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
INK, MUTED, LINE = "#16191f", "#545b64", "#232f3e"
FONT = "'Segoe UI', Arial, sans-serif"
TILE = 100

ICON_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
out: list[str] = []
count = 0


def text(x, y, value, size=24, weight=400, fill=INK, anchor="middle", italic=False):
    style = ' font-style="italic"' if italic else ""
    out.append(
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}"{style}>{html.escape(value)}</text>'
    )


def icon(name, x, y, size=TILE):
    global count
    count += 1
    svg = (ICON_DIR / name).read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', svg)
    body = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.S).rsplit("</svg>", 1)[0]
    prefix = f"i{count}-"
    ids = re.findall(r'id="([^"]+)"', body)
    for found in ids:
        body = body.replace(f'id="{found}"', f'id="{prefix}{found}"')
        body = body.replace(f"url(#{found})", f"url(#{prefix}{found})")
        body = body.replace(f'href="#{found}"', f'href="#{prefix}{found}"')
    out.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view[1]}">{body}</svg>')


def service(name, cx, top, title, note):
    icon(name, cx - TILE / 2, top)
    text(cx, top + TILE + 34, title, 25, 600)
    text(cx, top + TILE + 64, note, 21, 400, MUTED, italic=True)


def generic(cx, top, glyph, title, note, fill="#232f3e"):
    x = cx - TILE / 2
    out.append(f'<rect x="{x}" y="{top}" width="{TILE}" height="{TILE}" fill="{fill}"/>')
    text(cx, top + 66, glyph, 44, 700, "#ffffff")
    text(cx, top + TILE + 34, title, 25, 600)
    text(cx, top + TILE + 64, note, 21, 400, MUTED, italic=True)


def arrow(points, label=None, at=None, both=False):
    path = " ".join(f"{x},{y}" for x, y in points)
    start = ' marker-start="url(#tail)"' if both else ""
    out.append(
        f'<polyline points="{path}" fill="none" stroke="{LINE}" stroke-width="3" '
        f'marker-end="url(#head)"{start}/>'
    )
    if label and at:
        text(at[0], at[1], label, 21, 400, INK, italic=True)


def badge(number, x, y):
    out.append(f'<circle cx="{x}" cy="{y}" r="21" fill="{LINE}"/>')
    text(x, y + 8, str(number), 23, 700, "#ffffff")


def box(x, y, width, height, dash=False):
    extra = ' stroke-dasharray="10 8"' if dash else ""
    out.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="none" '
        f'stroke="{LINE}" stroke-width="3"{extra}/>'
    )


def chip(x, y, width, label, strong=False):
    fill = "#232f3e" if strong else "#eef1f4"
    color = "#ffffff" if strong else INK
    out.append(f'<rect x="{x}" y="{y}" width="{width}" height="44" rx="6" fill="{fill}"/>')
    text(x + width / 2, y + 30, label, 20, 600, color)


# --- Actors
icon("resource/Users.svg", 60, 185, 110)
text(115, 330, "Residents", 25, 600)
text(115, 360, "Telegram, Messenger,", 20, 400, MUTED, italic=True)
text(115, 386, "simulated SMS", 20, 400, MUTED, italic=True)
icon("resource/User.svg", 60, 790, 110)
text(115, 935, "Dispatcher", 25, 600)
text(115, 965, "Web browser", 20, 400, MUTED, italic=True)

# --- Application
box(240, 60, 540, 930, dash=True)
text(262, 104, "Saklolo application", 27, 600, anchor="start")
generic(510, 190, "API", "Saklolo API", "FastAPI, Strands Agents")
generic(510, 800, "UI", "Dispatcher dashboard", "Next.js, MapLibre")

out.append('<rect x="290" y="390" width="380" height="366" fill="#f8f9fa" stroke="#d5dbdb" stroke-width="2"/>')
text(480, 428, "Strands Graph", 24, 600)
for i, label in enumerate(["normalize", "prefilter", "extract", "geolocate", "dedupe", "verify"]):
    chip(300 + (i % 2) * 185, 446 + (i // 2) * 54, 175, label)
chip(392, 608, 175, "triage")
text(480, 684, "low confidence", 20, 400, MUTED, italic=True)
chip(300, 698, 360, "Strands Swarm: 3 agents", strong=True)

# --- AWS
box(830, 60, 1130, 930)
out.append(f'<rect x="830" y="60" width="56" height="56" fill="{LINE}"/>')
text(858, 98, "aws", 22, 700, "#ffffff")
text(906, 100, "AWS Cloud", 27, 600, anchor="start")

service("architecture-service/AmazonBedrock.svg", 1070, 200, "Amazon Bedrock", "Nova Lite, ap-southeast-1")
service("architecture-service/AmazonBedrock.svg", 1440, 200, "Titan Embeddings", "Bedrock, us-east-1")
service("architecture-service/AmazonLocationService.svg", 1790, 200, "Amazon Location", "Places, ap-southeast-2")
service("architecture-service/AmazonBedrockAgentCore.svg", 1070, 680, "AgentCore Memory", "Dispatcher corrections")
service("architecture-service/AmazonDynamoDB.svg", 1440, 680, "Amazon DynamoDB", "Cases, messages, decisions")

# --- Outside AWS
text(110, 1132, "Outside AWS", 27, 600)
for x, title, note in [
    (240, "Telegram Bot API", "Messages in, replies out"),
    (640, "Meta Messenger", "Signed webhook, Send API"),
    (1040, "Project NOAH", "Flood hazard map (ODbL)"),
    (1440, "OpenStreetMap", "Map tiles"),
]:
    out.append(f'<rect x="{x}" y="1070" width="360" height="118" rx="10" fill="#ffffff" stroke="#aab7b8" stroke-width="2"/>')
    text(x + 180, 1118, title, 25, 600)
    text(x + 180, 1154, note, 21, 400, MUTED, italic=True)

# --- Flows: one lane each, labels clear of lines
arrow([(175, 240), (455, 240)])
badge(1, 212, 200)
text(312, 268, "message", 21, italic=True)
arrow([(175, 845), (455, 845)])
badge(2, 212, 805)
arrow([(565, 850), (725, 850), (725, 285), (565, 285)])
text(645, 880, "REST, every 2 s", 21, italic=True)
arrow([(565, 225), (1012, 225)], both=True)
badge(3, 690, 225)
text(918, 210, "extract, triage, Swarm", 19, italic=True)
arrow([(510, 190), (510, 140), (1440, 140), (1440, 194)])
badge(4, 1180, 140)
text(1310, 126, "dedupe", 21, italic=True)
arrow([(1440, 140), (1790, 140), (1790, 194)])
badge(5, 1560, 140)
text(1690, 126, "geolocate", 21, italic=True)
arrow([(565, 255), (805, 255), (805, 640), (1440, 640), (1440, 674)])
badge(6, 1250, 640)
text(1365, 626, "cases, decisions", 21, italic=True)
arrow([(1070, 640), (1070, 674)])
badge(7, 900, 640)
text(990, 626, "corrections", 21, italic=True)
arrow([(420, 990), (420, 1064)], both=True)
arrow([(700, 990), (700, 1030), (820, 1030), (820, 1064)], both=True)
badge(8, 760, 1030)
text(560, 1037, "messages, replies", 21, italic=True)

head = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2000 1230" width="2000" height="1230">'
    '<defs>'
    f'<marker id="head" markerWidth="12" markerHeight="12" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
    f'<marker id="tail" markerWidth="12" markerHeight="12" refX="0" refY="5" orient="auto"><path d="M10,0 L0,5 L10,10 z" fill="{LINE}"/></marker>'
    '</defs><rect width="2000" height="1230" fill="#ffffff"/>'
)
(HERE / "architecture.svg").write_text(head + "".join(out) + "</svg>", encoding="utf-8", newline="\n")
