const ICONS = {
  alert: "M12 4 3 20h18L12 4zM12 10v5M12 17.5v.01",
  check: "M5 12.5l4.5 4.5L19 7",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3.5 2",
  "map-pin":
    "M12 21s7-6.4 7-12a7 7 0 0 0-14 0c0 5.6 7 12 7 12zM12 6.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",
  users:
    "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 4.5a3.5 3.5 0 0 1 0 6.5M17.5 14.5c2 .7 3.5 2.9 3.5 5.5",
  phone:
    "M8.5 3H6a2 2 0 0 0-2 2.2C4.8 13 11 19.2 18.8 20a2 2 0 0 0 2.2-2v-2.5l-4.5-2-2 2c-2.5-1.2-4.3-3-5.5-5.5l2-2-2.5-4.5z",
  message: "M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H10l-5 4v-4H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z",
  send: "M4 12 20 4l-6 16-3-7-7-1zM11 13l9-9",
  shield: "M12 3l7.5 3v5.5c0 4.5-3 7.8-7.5 9.5-4.5-1.700-7.5-5-7.5-9.5V6L12 3z",
  flag: "M6 21V4M6 4c4-2.5 8 2 12 0v10c-4 2-8-2.5-12 0",
  radio:
    "M12 13v8M12 9.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM8 15a6 6 0 0 1 0-6M16 9a6 6 0 0 1 0 6M5 18A10 10 0 0 1 5 6M19 6a10 10 0 0 1 0 12",
  droplet: "M12 3s6.5 6.5 6.5 11a6.5 6.5 0 0 1-13 0C5.5 9.5 12 3 12 3z",
  heart: "M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z",
  baby: "M12 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM9 10v.01M15 10v.01M9.5 14c1.5 1.300 3.5 1.300 5 0M12 3c-1.5 1-1.5 2.5 0 3",
  "chevron-right": "M9 5l7 7-7 7",
  x: "M6 6l12 12M18 6L6 18",
  play: "M7 4.5v15L19.5 12 7 4.5z",
  refresh: "M20 11a8 8 0 0 0-14.5-3.5L3 10M3 4v6h6M4 13a8 8 0 0 0 14.5 3.5L21 14M21 20v-6h-6",
  signal: "M4 20v-3M9 20v-7M14 20V9M19 20V4",
  wifi: "M2 9a15 15 0 0 1 20 0M5.5 12.5a10 10 0 0 1 13 0M9 16a5 5 0 0 1 6 0M12 19.5v.01",
  battery:
    "M3 8h15a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1zM22 11v2M6 11v2M9 11v2M12 11v2",
  video:
    "M3 7h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1zM16 10.5l6-3.5v10l-6-3.5",
  more: "M12 5v.01M12 12v.01M12 19v.01",
  plus: "M12 5v14M5 12h14",
  camera:
    "M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1zM12 10.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z",
  "check-double": "M2 12.5l4.5 4.5L16 7M10 16.5l.5.5L20 7",
  "chevron-left": "M15 5l-7 7 7 7",
};

export type IconName = keyof typeof ICONS;

const SIZE = {
  sm: "size-(--sk-space-4)",
  md: "size-(--sk-space-6)",
};

interface IconProps {
  name: IconName;
  /** Accessible name. Leave out when text beside the icon already says it. */
  label?: string;
  size?: keyof typeof SIZE;
}

/** A line icon that takes the color of the text around it. */
export function Icon({ name, label, size = "sm" }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className={`shrink-0 ${SIZE[size]}`}
    >
      <path d={ICONS[name]} />
    </svg>
  );
}
