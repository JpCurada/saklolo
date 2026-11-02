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
WIDTH, HEIGHT = 2300, 1360

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


def arrow(points, both=False):
    path = " ".join(f"{x},{y}" for x, y in points)
    start = ' marker-start="url(#tail)"' if both else ""
    out.append(
        f'<polyline points="{path}" fill="none" stroke="{LINE}" stroke-width="3" '
        f'stroke-linejoin="round" marker-end="url(#head)"{start}/>'
    )


def badge(number, x, y):
    out.append(f'<circle cx="{x}" cy="{y}" r="21" fill="{LINE}"/>')
    text(x, y + 8, str(number), 23, 700, "#ffffff")


def note(x, y, value, anchor="middle"):
    text(x, y, value, 21, 400, INK, anchor, italic=True)


# --- People and channels, outside AWS
icon("resource/Users.svg", 30, 280, 110)
labels(85, 280, "Residents", "", 110)
icon("resource/User.svg", 30, 900, 110)
labels(85, 900, "Dispatcher", "Web browser", 110)

for top, logo, title, sub in [
    (110, "telegram-logo.png", "Telegram", "Bot API"),
    (300, "messenger-logo.png", "Messenger", "Page webhook"),
    (490, None, "SMS", "Text message"),
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
out.append(f'<rect x="470" y="40" width="1800" height="1130" fill="none" stroke="{LINE}" stroke-width="3"/>')
out.append(f'<rect x="470" y="40" width="56" height="56" fill="{LINE}"/>')
text(498, 78, "aws", 22, 700, "#ffffff")
text(546, 80, "AWS Cloud · ap-southeast-1", 27, 600, anchor="start")

service("architecture-service/AWSLambda.svg", 680, 150, "AWS Lambda", "saklolo-api, FastAPI")
service("architecture-service/AmazonSimpleQueueService.svg", 960, 150, "Amazon SQS", "Intake queue")
service("architecture-service/AWSLambda.svg", 1240, 150, "AWS Lambda", "saklolo-worker")
service("architecture-service/AmazonBedrock.svg", 1560, 150, "Amazon Bedrock", "Nova Lite")
service("architecture-service/AmazonBedrock.svg", 1820, 150, "Titan Embeddings", "Bedrock, us-east-1")
service("architecture-service/AmazonLocationService.svg", 2080, 150, "Amazon Location", "Places, ap-southeast-2")

# The agents, inside the worker
out.append('<rect x="1110" y="340" width="260" height="190" rx="8" fill="#f2fbf4" stroke="#1fb954" stroke-width="2"/>')
picture("strands.png", 1126, 356, 44)
text(1182, 386, "Strands Agents", 23, 700, anchor="start")
text(1240, 432, "Graph: 8 steps", 20, 600)
text(1240, 466, "Swarm: 3 agents", 20, 600)
text(1240, 506, "for unsure cases", 19, 400, MUTED, italic=True)

service("architecture-service/AmazonDynamoDB.svg", 1240, 640, "Amazon DynamoDB", "Cases, messages, decisions")
service("architecture-service/AmazonBedrockAgentCore.svg", 1560, 640, "AgentCore Memory", "Dispatcher corrections")
service("architecture-service/AmazonElasticContainerRegistry.svg", 2080, 640, "Amazon ECR", "Lambda images")

service("architecture-service/AmazonCloudFront.svg", 680, 880, "Amazon CloudFront", "Dashboard and /api/*")
service("architecture-service/AmazonSimpleStorageService.svg", 960, 880, "Amazon S3", "Dashboard build")
service("architecture-service/AmazonCognito.svg", 1240, 880, "Amazon Cognito", "Dispatcher sign-in")

# --- Outside AWS
text(140, 1262, "Outside AWS", 27, 600)
for x, logo, title, sub in [
    (470, None, "Project NOAH", "Flood hazard map (ODbL)"),
    (900, "osm.svg", "OpenStreetMap", "Map tiles"),
]:
    out.append(f'<rect x="{x}" y="1200" width="380" height="118" rx="10" fill="#ffffff" stroke="#aab7b8" stroke-width="2"/>')
    if logo:
        picture(logo, x + 30, 1224, 70)
        text(x + 120, 1252, title, 25, 600, anchor="start")
        text(x + 120, 1288, sub, 21, 400, MUTED, anchor="start", italic=True)
    else:
        text(x + 190, 1248, title, 25, 600)
        text(x + 190, 1284, sub, 21, 400, MUTED, italic=True)

# --- Flows
# 1 Residents write on any channel
for y in (155, 345, 535):
    arrow([(145, 335), (215, 335), (215, y), (279, y)])
badge(1, 175, 335)
# 2 Channels reach the API; replies go back the same way
arrow([(381, 155), (560, 155), (560, 180), (624, 180)], both=True)
arrow([(381, 345), (585, 345), (585, 205), (624, 205)], both=True)
arrow([(381, 535), (605, 535), (605, 230), (624, 230)], both=True)
badge(2, 500, 155)
# 3 The API queues new messages
arrow([(736, 190), (904, 190)])
badge(3, 875, 190)
note(790, 174, "queued")
# 4 The worker runs the agents
arrow([(1016, 190), (1184, 190)])
badge(4, 1100, 190)
note(1100, 236, "one at a time")
# 5 Bedrock for extract, triage, and the Swarm
arrow([(1296, 190), (1504, 190)], both=True)
badge(5, 1330, 190)
note(1445, 174, "extract, triage")
# 6 Embeddings and places
arrow([(1240, 150), (1240, 110), (1820, 110), (1820, 144)])
arrow([(1820, 110), (2080, 110), (2080, 144)])
badge(6, 1560, 110)
note(1700, 97, "dedupe")
note(1950, 97, "geolocate")
# 7 Cases and corrections
arrow([(1296, 225), (1440, 225), (1440, 670), (1296, 670)])
arrow([(1440, 670), (1504, 670)])
badge(7, 1440, 560)
note(1462, 610, "cases, corrections", "start")
# 8 The API reads cases and records decisions
arrow([(736, 215), (850, 215), (850, 710), (1184, 710)], both=True)
badge(8, 1110, 710)
note(980, 692, "reads, decisions")
# 9 The dispatcher opens the dashboard through CloudFront
arrow([(145, 945), (624, 945)])
badge(9, 400, 945)
arrow([(736, 930), (904, 930)])
note(820, 962, "dashboard")
arrow([(736, 905), (815, 905), (815, 240), (736, 240)])
note(805, 560, "/api/*", "end")
# 10 Sign-in
arrow([(145, 980), (200, 980), (200, 1120), (1110, 1120), (1110, 940), (1184, 940)])
badge(10, 650, 1120)
note(820, 1108, "sign in")

head = (
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
    f'width="{WIDTH}" height="{HEIGHT}"><defs>'
    f'<marker id="head" markerWidth="12" markerHeight="12" refX="10" refY="5" orient="auto">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
    f'<marker id="tail" markerWidth="12" markerHeight="12" refX="0" refY="5" orient="auto">'
    f'<path d="M10,0 L0,5 L10,10 z" fill="{LINE}"/></marker>'
    f'</defs><rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>'
)
(HERE / "architecture.svg").write_text(head + "".join(out) + "</svg>", encoding="utf-8", newline="\n")
