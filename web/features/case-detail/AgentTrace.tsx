import { Badge, Icon, Text } from "@/components/ui";
import type { TraceStep } from "@/lib/api/types";

// Plain words for each Strands Graph node; the node id is shown beside it.
const STEP_LABEL: Record<string, string> = {
  normalize: "Clean up the text",
  prefilter: "Spam filter",
  extract: "Read the message",
  geolocate: "Find the place",
  dedupe: "Match to a case",
  verify: "Check for old posts",
  triage: "Set the priority",
  escalate: "Second opinion (Swarm)",
  resume: "Resume after asking",
};

const seconds = (ms: number) => (ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`);

interface AgentTraceProps {
  trace: TraceStep[];
  /** Folded by default: it's the longest part of a case, one click away. */
  open?: boolean;
}

/** What each agent step did with one message, as recorded while the graph ran. */
export function AgentTrace({ trace, open = false }: AgentTraceProps) {
  if (trace.length === 0) return null;
  const ran = trace.filter((step) => step.status === "ran");
  const total = ran.reduce((sum, step) => sum + step.duration_ms, 0);
  const modelCalls = ran.filter((step) => step.service?.includes("Bedrock")).length;
  return (
    <details data-testid="agent-trace" open={open} className="group/trace sk-agent-trace">
      <summary className="flex min-h-(--sk-space-10) cursor-pointer list-none items-center gap-(--sk-space-2) rounded-(--sk-radius-tile) px-(--sk-space-2) py-(--sk-space-1) hover:bg-(--sk-color-canvas) focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-(--sk-color-accent)">
        <span className="shrink-0 transition-transform duration-(--sk-motion-fast) group-open/trace:rotate-90 motion-reduce:transition-none">
          <Icon name="chevron-right" />
        </span>
        <span className="flex min-w-0 flex-1 flex-wrap items-center gap-x-(--sk-space-1)">
          <Text variant="caption-bold">How the agents decided</Text>
          <Text variant="caption" tone="muted">
            · {ran.length} of {trace.length} steps · {modelCalls} model{" "}
            {modelCalls === 1 ? "call" : "calls"} · {seconds(total)}
          </Text>
        </span>
      </summary>
      <ol className="mt-2 space-y-1">
        {trace.map((step) => (
          <li
            key={step.step}
            data-testid="trace-step"
            data-step={step.step}
            data-status={step.status}
            className="flex items-start gap-2"
          >
            <Icon name={step.status === "ran" ? "check" : "x"} />
            <span className="flex w-1/4 shrink-0 flex-col">
              <Text variant="caption-bold" tone={step.status === "ran" ? "ink" : "faint"}>
                {STEP_LABEL[step.step] ?? step.step}
              </Text>
              <Text variant="caption" tone="faint">
                {step.step}
              </Text>
            </span>
            <span className="w-1/12 shrink-0">
              <Text variant="caption" tone="faint">
                {step.status === "ran" ? seconds(step.duration_ms) : "–"}
              </Text>
            </span>
            <span className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
              <Text variant="caption" tone={step.status === "ran" ? "ink" : "faint"}>
                {step.detail}
              </Text>
              {step.service && <Badge tone="none">{step.service}</Badge>}
            </span>
          </li>
        ))}
      </ol>
    </details>
  );
}
