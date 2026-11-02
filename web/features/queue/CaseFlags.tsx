import { Icon, type IconName, StatusFlag, StatusFlagList } from "@/components/ui";
import type { Badge } from "@/lib/api/types";
import { BADGE_LABEL } from "@/lib/format";

const ICON: Record<Badge, IconName> = {
  corroborated: "check",
  suspicious: "alert",
  reported_safe: "shield",
  awaiting_location: "map-pin",
  needs_review: "flag",
  overridden: "refresh",
};

export function CaseFlags({ badges }: { badges: Badge[] }) {
  if (badges.length === 0) return null;
  return (
    <StatusFlagList>
      {badges.map((badge) => (
        <StatusFlag key={badge} flag={badge} icon={<Icon name={ICON[badge]} />}>
          {BADGE_LABEL[badge]}
        </StatusFlag>
      ))}
    </StatusFlagList>
  );
}
