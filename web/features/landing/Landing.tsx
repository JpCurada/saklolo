import Image from "next/image";

import {
  Badge,
  Bubble,
  Icon,
  LinkButton,
  PriorityBadge,
  Text,
  type IconName,
} from "@/components/ui";
import { DEMO_MODE } from "@/lib/demo";

/** The demo video's YouTube ID. Empty until it's published: the frame shows a placeholder. */
const DEMO_VIDEO_ID = "";

const PROBLEM = [
  {
    figure: "~20",
    label: "tropical cyclones enter the Philippine area each year",
    source: "PAGASA",
    href: "https://www.pagasa.dost.gov.ph/climate/tropical-cyclone-information",
  },
  {
    figure: "22 m",
    label: "Marikina River during Typhoon Ulysses in 2020, above Ondoy's 2009 peak",
    source: "Typhoon Vamco",
    href: "https://en.wikipedia.org/wiki/Typhoon_Vamco",
  },
  {
    figure: "1 inbox",
    label: "for thousands of pleas, repeats and old reposts, read by a handful of dispatchers",
    source: "the gap Saklolo fills",
  },
];

type Kind = "Rules" | "Model" | "Embeddings" | "Geocoder" | "Swarm";

const STEPS: { name: string; kind: Kind; does: string }[] = [
  {
    name: "Normalize",
    kind: "Rules",
    does: "Cleans spelling, emoji and texting shorthand. Keeps the original.",
  },
  { name: "Prefilter", kind: "Rules", does: "Sets aside jokes and chatter, never deletes them." },
  {
    name: "Extract",
    kind: "Model",
    does: "Reads Taglish: how many people, who is vulnerable, how deep the water is.",
  },
  {
    name: "Geolocate",
    kind: "Geocoder",
    does: "Turns “sto nino, near the chapel” into a barangay and a pin, or asks the resident.",
  },
  {
    name: "Dedupe",
    kind: "Embeddings",
    does: "Merges the same family's plea sent by five relatives.",
  },
  {
    name: "Verify",
    kind: "Rules",
    does: "Flags recycled posts, past dates and copy-paste senders, with flood maps.",
  },
  {
    name: "Triage",
    kind: "Model",
    does: "Sets P1 to P4 and writes the reason in one line of English.",
  },
  {
    name: "Escalate",
    kind: "Swarm",
    does: "Unsure cases go to three agents who can only raise the priority.",
  },
];

const PROMISES: { icon: IconName; title: string; body: string }[] = [
  {
    icon: "shield",
    title: "A person decides",
    body: "Agents sort and explain. A dispatcher assigns, overrides and closes. Nothing is closed by the system.",
  },
  {
    icon: "flag",
    title: "Doubt keeps a case open",
    body: "A post that looks recycled is kept for review with its reason, never thrown away.",
  },
  {
    icon: "alert",
    title: "Second opinions only go up",
    body: "The Swarm can raise a priority, never lower it. A missed P1 costs more than a false alarm.",
  },
  {
    icon: "message",
    title: "The resident's words stay",
    body: "Every English summary sits beside the original message, in the language it was sent.",
  },
];

const SCREENS = [
  {
    src: "/assets/landing/dashboard.webp",
    width: 1600,
    height: 900,
    title: "The queue",
    body: "Cases sorted by priority, each with its reason and verification.",
  },
  {
    src: "/assets/landing/agent-trace.webp",
    width: 1600,
    height: 900,
    title: "The agent trace",
    body: "Every step an agent took on a message, and what it decided.",
  },
  {
    src: "/assets/landing/resident-phones.webp",
    width: 1600,
    height: 900,
    title: "Where pleas come from",
    body: "Telegram and Messenger chats, answered with a case number.",
  },
];

const SERVICES = [
  "Strands Agents",
  "Amazon Bedrock",
  "Bedrock AgentCore Memory",
  "AWS Lambda",
  "Amazon SQS",
  "Amazon DynamoDB",
  "Amazon API Gateway",
  "Amazon Cognito",
  "Amazon CloudFront",
  "Amazon S3",
  "Amazon ECR",
  "Amazon CloudWatch",
];

/** The public front page: what Saklolo is, how it works, and where to go next. */
export function Landing() {
  return (
    <div className="sk-landing">
      <header data-testid="landing-header" className="sk-landing-nav">
        <div className="sk-brand">
          <Image src="/assets/logo-mark.svg" width={32} height={32} alt="" unoptimized />
          <Text variant="title-m">Saklolo</Text>
        </div>
        <nav aria-label="Main" className="sk-landing-nav-links">
          <LinkButton href="/dispatch" variant="secondary" size="sm" testId="nav-dispatch">
            Dispatcher sign-in
          </LinkButton>
        </nav>
      </header>

      <main>
        <section data-testid="landing-hero" className="sk-landing-hero">
          <picture className="sk-landing-hero-backdrop">
            <source srcSet="/assets/scene-boot.webp" media="(prefers-reduced-motion: reduce)" />
            {/* Not next/image: its optimizer can flatten animation. */}
            <img src="/assets/scene-boot-animated.webp" width={480} height={360} alt="" />
          </picture>
          <div className="sk-landing-hero-copy">
            <Badge tone="none">Typhoon rescue triage · Marikina City</Badge>
            <Text as="h1" variant="display">
              When the river rises, every plea reaches the right rescuer first.
            </Text>
            <Text as="p" tone="muted">
              Saklolo reads rescue requests sent by chat in Filipino, English and Taglish. Strands
              agents find who needs help, where they are and how urgent it is, then hand a ranked
              queue to a human dispatcher.
            </Text>
            <div className="sk-landing-actions">
              <LinkButton href="/dispatch" testId="cta-dispatch">
                Open the dashboard
              </LinkButton>
              {DEMO_MODE && (
                <LinkButton href="/resident" variant="secondary" testId="cta-resident">
                  Send a plea
                </LinkButton>
              )}
            </div>
          </div>

          <figure className="sk-landing-plea" aria-label="A plea becomes a case">
            <DemoVideo />
            <div className="sk-landing-chat">
              <Bubble direction="out" skin="telegram" time="1:32 AM" delivered lang="fil">
                Tulong po! Hanggang leeg na baha dito sa Tumana, malapit sa kapilya. 5 kami, may
                lola na bedridden.
              </Bubble>
            </div>
            <Icon name="chevron-right" size="md" />
            <div data-testid="landing-case" className="sk-landing-case">
              <div className="sk-landing-case-head">
                <PriorityBadge priority="P1" />
                <Text variant="caption" tone="faint">
                  Case 0142 · Tumana
                </Text>
              </div>
              <Text as="p" variant="body-bold">
                Neck-deep flood, 5 people, 1 bedridden elder
              </Text>
              <Text as="p" variant="caption" tone="muted">
                Tumana, near the chapel · Why: water at neck height with a person who can&apos;t
                walk.
              </Text>
            </div>
          </figure>
        </section>

        <section aria-labelledby="problem" className="sk-landing-section">
          <Text as="h2" variant="title-l">
            <span id="problem">
              The problem isn&apos;t too few rescuers. It&apos;s too many unread messages.
            </span>
          </Text>
          <div className="sk-landing-grid-3">
            {PROBLEM.map((item) => (
              <div key={item.figure} className="sk-landing-card">
                <Text variant="display">{item.figure}</Text>
                <Text as="p">{item.label}</Text>
                {item.href ? (
                  <a href={item.href} target="_blank" rel="noreferrer">
                    <Text variant="caption" tone="faint">
                      Source: {item.source}
                    </Text>
                  </a>
                ) : (
                  <Text variant="caption" tone="faint">
                    {item.source}
                  </Text>
                )}
              </div>
            ))}
          </div>
        </section>

        <section aria-labelledby="pipeline" className="sk-landing-section">
          <Text as="h2" variant="title-l">
            <span id="pipeline">Eight steps from a chat message to a ranked case</span>
          </Text>
          <Text as="p" tone="muted">
            A Strands Graph runs each message through these steps. Three are plain rules with no
            model call. Only Extract and Triage ask a model, and only unsure cases reach the Swarm.
          </Text>
          <ol data-testid="landing-steps" className="sk-landing-steps">
            {STEPS.map((step, index) => (
              <li key={step.name} className="sk-landing-step">
                <div className="sk-landing-case-head">
                  <Text variant="caption-bold" tone="faint">
                    {String(index + 1).padStart(2, "0")}
                  </Text>
                  <Badge tone="none">{step.kind}</Badge>
                </div>
                <Text as="h3" variant="title-m">
                  {step.name}
                </Text>
                <Text as="p" variant="caption" tone="muted">
                  {step.does}
                </Text>
              </li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="promises" className="sk-landing-section">
          <Text as="h2" variant="title-l">
            <span id="promises">Built to be trusted on the worst night of the year</span>
          </Text>
          <div className="sk-landing-grid-4">
            {PROMISES.map((promise) => (
              <div key={promise.title} className="sk-landing-card">
                <Icon name={promise.icon} size="md" />
                <Text as="h3" variant="body-bold">
                  {promise.title}
                </Text>
                <Text as="p" variant="caption" tone="muted">
                  {promise.body}
                </Text>
              </div>
            ))}
          </div>
        </section>

        <section aria-labelledby="screens" className="sk-landing-section">
          <Text as="h2" variant="title-l">
            <span id="screens">What the dispatcher sees</span>
          </Text>
          <div className="sk-landing-grid-3">
            {SCREENS.map((screen) => (
              <figure key={screen.src} className="sk-landing-card">
                <Image
                  src={screen.src}
                  width={screen.width}
                  height={screen.height}
                  alt={screen.title}
                  className="sk-landing-shot"
                  unoptimized
                />
                <Text as="h3" variant="body-bold">
                  {screen.title}
                </Text>
                <Text as="p" variant="caption" tone="muted">
                  {screen.body}
                </Text>
              </figure>
            ))}
          </div>
        </section>

        <section aria-labelledby="aws" className="sk-landing-section">
          <Text as="h2" variant="title-l">
            <span id="aws">Serverless on AWS, quiet until the storm</span>
          </Text>
          <Text as="p" tone="muted">
            Messages queue in SQS FIFO so none are lost when a hundred arrive at once. Lambda scales
            the agents up during a typhoon and back to zero after it.
          </Text>
          <Image
            src="/assets/landing/architecture.webp"
            width={1600}
            height={900}
            alt="Architecture: residents message Telegram or Messenger, API Gateway and Lambda queue each message in SQS, a worker Lambda runs the Strands agents on Bedrock, cases are stored in DynamoDB, and dispatchers sign in with Cognito to a dashboard served by CloudFront."
            className="sk-landing-shot"
            unoptimized
          />
          <ul aria-label="AWS services used" className="sk-landing-services">
            {SERVICES.map((service) => (
              <li key={service}>
                <Badge tone="none">{service}</Badge>
              </li>
            ))}
          </ul>
        </section>

        <section className="sk-landing-section sk-landing-closing">
          <Text as="h2" variant="title-l">
            See a plea become a case in seconds.
          </Text>
          <div className="sk-landing-actions">
            <LinkButton href="/dispatch" testId="cta-dispatch-bottom">
              Open the dashboard
            </LinkButton>
          </div>
        </section>
      </main>

      <footer data-testid="landing-footer" className="sk-landing-footer">
        <Text as="p" variant="caption" tone="faint">
          Map data © OpenStreetMap contributors (ODbL). Flood hazard data from UP NOAH.
        </Text>
      </footer>
    </div>
  );
}

/** The demo video, or a still of the storm until the video is published. */
function DemoVideo() {
  if (DEMO_VIDEO_ID) {
    return (
      <iframe
        data-testid="demo-video"
        className="sk-landing-video"
        src={`https://www.youtube-nocookie.com/embed/${DEMO_VIDEO_ID}`}
        title="Saklolo demo video"
        allow="encrypted-media; picture-in-picture"
        allowFullScreen
        loading="lazy"
      />
    );
  }
  return (
    <div data-testid="demo-video" className="sk-landing-video">
      <Image src="/assets/scene-boot.webp" width={480} height={360} alt="" unoptimized />
      <span className="sk-landing-video-label">
        <Icon name="play" size="md" />
        <Text variant="body-bold">Demo video coming soon</Text>
      </span>
    </div>
  );
}
