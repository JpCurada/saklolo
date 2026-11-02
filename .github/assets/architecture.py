"""Generate the architecture diagram.

    python architecture.py <aws-icons svg folder> <logo folder>

Writes architecture.svg next to this file. AWS icons come from the aws-icons npm
package (official AWS Architecture Icons). The logo folder holds telegram-logo.png,
messenger-logo.png, strands.png, and osm.svg. Update the tiles when the deployment
changes.
"""

import base64
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
INK, MUTED, LINE = "#16191f", "#545b64", "#232f3e"
FONT = "'Segoe UI', Arial, sans-serif"
TILE = 100
WIDTH, HEIGHT = 2400, 1350

ICONS = Path(sys.argv[1])
LOGOS = Path(sys.argv[2])
out: list[str] = []
count = 0


def text(x, y, value, size=24, weight=400, fill=INK, anchor="middle", italic=False):
    style = ' font-style="italic"' if italic else ""
    out.append(
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}"{style}>{html.escape(value)}</text>'
    )


def labels(cx, top, title, note, size=TILE):
    text(cx, top + size + 34, title, 25, 600)
    if note:
        text(cx, top + size + 64, note, 21, 400, MUTED, italic=True)


def icon(name, x, y, size=TILE):
    global count
    count += 1
    svg = (ICONS / name).read_text(encoding="utf-8")
    view = re.search(r'viewBox="([^"]+)"', svg)
    body = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.S).rsplit("</svg>", 1)[0]
    for found in re.findall(r'id="([^"]+)"', body):
        new = f"i{count}-{found}"
        body = body.replace(f'id="{found}"', f'id="{new}"').replace(f"#{found}", f"#{new}")
    out.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view[1]}">{body}</svg>')


def picture(name, x, y, size):
    data = (LOGOS / name).read_bytes()
    kind = {"webp": "image/webp", "png": "image/png", "svg": "image/svg+xml"}[name.rsplit(".", 1)[1]]
    uri = f"data:{kind};base64,{base64.b64encode(data).decode()}"
    out.append(f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="{uri}"/>')


def service(name, cx, top, title, note):
    icon(name, cx - TILE / 2, top)
    labels(cx, top, title, note)


def arrow(points, both=False, dashed=False):
    path = " ".join(f"{x},{y}" for x, y in points)
    start = ' marker-start="url(#tail)"' if both else ""
    dash = ' stroke-dasharray="10 7"' if dashed else ""
    out.append(
        f'<polyline points="{path}" fill="none" stroke="{LINE}" stroke-width="3" '
        f'stroke-linejoin="round" marker-end="url(#head)"{start}{dash}/>'
    )


def badge(number, x, y):
    out.append(f'<circle cx="{x}" cy="{y}" r="21" fill="{LINE}"/>')
    text(x, y + 8, str(number), 23, 700, "#ffffff")


def note(x, y, value, anchor="middle"):
    text(x, y, value, 21, 400, INK, anchor, italic=True)


# --- People and channels, outside AWS
icon("resource/Users.svg", 30, 320, 110)
labels(85, 320, "Residents", "", 110)
icon("resource/User.svg", 30, 795, 110)
labels(85, 795, "Dispatcher", "Web browser", 110)

for top, logo, title, sub in [
    (120, "telegram-logo.png", "Telegram", "Bot API"),
    (330, "messenger-logo.png", "Messenger", "Page webhook"),
    (540, None, "SMS", "Text message"),
]:
    if logo:
        picture(logo, 285, top, 90)
    else:
        out.append(f'<rect x="285" y="{top}" width="90" height="90" rx="20" fill="#34a853"/>')
        out.append(
            f'<path d="M305 {top + 26} h50 a6 6 0 0 1 6 6 v24 a6 6 0 0 1 -6 6 h-30 l-12 10 v-10 '
            f'h-8 a6 6 0 0 1 -6 -6 v-24 a6 6 0 0 1 6 -6z" fill="#ffffff"/>'
        )
    labels(330, top, title, sub, 90)

# --- AWS Cloud
out.append(f'<rect x="500" y="40" width="1860" height="1040" fill="none" stroke="{LINE}" stroke-width="3"/>')
out.append(f'<rect x="500" y="40" width="56" height="56" fill="{LINE}"/>')
text(528, 78, "aws", 22, 700, "#ffffff")
text(576, 80, "AWS Cloud · ap-southeast-1", 27, 600, anchor="start")

# Container images for both Lambdas
icon("architecture-service/AmazonElasticContainerRegistry.svg", 978, 55, 64)
text(1056, 83, "Amazon ECR", 23, 600, anchor="start")
text(1056, 109, "API and worker images", 19, 400, MUTED, anchor="start", italic=True)

service("architecture-service/AWSLambda.svg", 720, 190, "AWS Lambda", "saklolo-api, FastAPI")
service("architecture-service/AmazonSimpleQueueService.svg", 1010, 190, "Amazon SQS", "Intake queue")
service("architecture-service/AWSLambda.svg", 1300, 190, "AWS Lambda", "saklolo-worker")
service("architecture-service/AmazonBedrock.svg", 1640, 190, "Amazon Bedrock", "Nova Lite")
service("architecture-service/AmazonBedrock.svg", 1930, 190, "Titan Embeddings", "Bedrock, us-east-1")
service("architecture-service/AmazonLocationService.svg", 2220, 190, "Amazon Location", "Places, ap-southeast-2")

# The agents, inside the worker
out.append('<rect x="1150" y="400" width="300" height="104" rx="8" fill="#f2fbf4" stroke="#1fb954" stroke-width="2"/>')
picture("strands.png", 1164, 412, 40)
text(1216, 440, "Strands Agents", 23, 700, anchor="start")
text(1300, 485, "8-step Graph, 3-agent Swarm", 19, 600)

service("architecture-service/AmazonCloudFront.svg", 720, 800, "Amazon CloudFront", "Dashboard and /api/*")
service("architecture-service/AmazonSimpleStorageService.svg", 1010, 800, "Amazon S3", "Dashboard build")
service("architecture-service/AmazonDynamoDB.svg", 1300, 800, "Amazon DynamoDB", "Cases, decisions")
service("architecture-service/AmazonBedrockAgentCore.svg", 1640, 800, "AgentCore Memory", "Corrections")
service("architecture-service/AmazonCognito.svg", 1930, 800, "Amazon Cognito", "Dispatcher sign-in")

# --- Outside AWS
text(150, 1193, "Outside AWS", 27, 600)
for x, logo, title, sub in [
    (500, None, "Project NOAH", "Flood hazard map (ODbL)"),
    (920, "osm.svg", "OpenStreetMap", "Map tiles"),
]:
    out.append(f'<rect x="{x}" y="1130" width="380" height="110" rx="10" fill="#ffffff" stroke="#aab7b8" stroke-width="2"/>')
    if logo:
        picture(logo, x + 30, 1150, 70)
        text(x + 120, 1178, title, 25, 600, anchor="start")
        text(x + 120, 1214, sub, 21, 400, MUTED, anchor="start", italic=True)
    else:
        text(x + 190, 1176, title, 25, 600)
        text(x + 190, 1212, sub, 21, 400, MUTED, italic=True)

# --- Flows. Arrows end on a tile's edge, so each head touches what it points at.
# 1 Residents write on any channel
for y in (165, 375, 585):
    arrow([(140, 375), (215, 375), (215, y), (285, y)])
badge(1, 175, 375)
# 2 Channels reach the API; replies go back the same way
arrow([(375, 165), (590, 165), (590, 215), (670, 215)], both=True)
arrow([(375, 375), (615, 375), (615, 240), (670, 240)], both=True)
arrow([(375, 585), (640, 585), (640, 265), (670, 265)], both=True)
badge(2, 530, 165)
# Both Lambdas run as container images from ECR
arrow([(1010, 119), (1010, 150), (720, 150), (720, 190)], dashed=True)
arrow([(1010, 150), (1270, 150), (1270, 190)], dashed=True)
note(865, 141, "images")
# 3 The API queues new messages
arrow([(770, 220), (960, 220)])
badge(3, 880, 220)
note(825, 204, "queued")
# 4 The worker runs the agents
arrow([(1060, 220), (1250, 220)])
badge(4, 1155, 220)
note(1155, 268, "one at a time")
# 5 Bedrock for extract, triage, and the Swarm
arrow([(1350, 220), (1590, 220)], both=True)
badge(5, 1410, 220)
note(1500, 204, "extract, triage")
# 6 Embeddings and places
arrow([(1330, 190), (1330, 135), (1930, 135), (1930, 190)])
arrow([(1930, 135), (2220, 135), (2220, 190)])
badge(6, 1640, 135)
note(1790, 122, "dedupe")
note(2080, 122, "geolocate")
# 7 Cases and corrections
arrow([(1350, 255), (1500, 255), (1500, 850), (1350, 850)])
arrow([(1500, 850), (1590, 850)])
badge(7, 1500, 620)
note(1522, 690, "cases, corrections", "start")
# 8 The API reads cases and records decisions
arrow([(770, 245), (900, 245), (900, 740), (1275, 740), (1275, 800)], both=True)
badge(8, 1000, 740)
note(1150, 728, "reads, decisions")
# 9 The dispatcher opens the dashboard through CloudFront
arrow([(140, 850), (670, 850)])
badge(9, 420, 850)
arrow([(770, 870), (960, 870)])
note(865, 900, "dashboard")
arrow([(770, 825), (860, 825), (860, 270), (770, 270)])
note(850, 520, "/api/*", "end")
# 10 Sign-in
arrow([(140, 885), (210, 885), (210, 1040), (1800, 1040), (1800, 850), (1880, 850)])
badge(10, 700, 1040)
note(870, 1028, "sign in")

head = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
    f'width="{WIDTH}" height="{HEIGHT}"><defs>'
    # Fixed-size heads whose tip sits on the line's end, so the line runs into the head.
    f'<marker id="head" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="14" '
    f'refX="17" refY="7" orient="auto"><path d="M0,0 L18,7 L0,14 z" fill="{LINE}"/></marker>'
    f'<marker id="tail" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="14" '
    f'refX="1" refY="7" orient="auto"><path d="M18,0 L0,7 L18,14 z" fill="{LINE}"/></marker>'
    f'</defs><rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>'
)
(HERE / "architecture.svg").write_text(head + "".join(out) + "</svg>", encoding="utf-8", newline="\n")
