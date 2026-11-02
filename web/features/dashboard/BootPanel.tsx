import { EmptyState, Panel } from "@/components/ui";

/** Shown until the first response arrives. There's no minimum time on screen. */
export function BootPanel() {
  return (
    <div role="status" className="col-span-2 grid min-h-0">
      <Panel title="Dispatch connection" testId="boot-screen">
        <EmptyState
          image="/assets/scene-boot.webp"
          animated="/assets/scene-boot-animated.webp"
          alt=""
          title="Connecting to dispatch"
          size="lg"
        />
      </Panel>
    </div>
  );
}
