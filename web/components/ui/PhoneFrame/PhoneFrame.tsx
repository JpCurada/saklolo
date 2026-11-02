import type { ReactNode } from "react";

import type { PhoneSkin } from "../Bubble/Bubble";
import { Icon, type IconName } from "../Icon/Icon";

const SKIN: Record<
  PhoneSkin,
  { bar: string; meta: string; bg: string; avatar: string; composer: string; actions: IconName[] }
> = {
  sms: {
    bar: "bg-(--sk-color-phone-sms-bar) text-(--sk-color-phone-sms-bar-fg)",
    meta: "text-(--sk-color-phone-sms-bar-meta)",
    bg: "bg-(--sk-color-phone-sms-bg)",
    avatar: "bg-(--sk-color-phone-sms-accent) text-(--sk-color-phone-messenger-out-fg)",
    composer: "bg-(--sk-color-phone-sms-in)",
    actions: ["phone", "more"],
  },
  telegram: {
    bar: "bg-(--sk-color-phone-telegram-bar) text-(--sk-color-phone-telegram-bar-fg)",
    meta: "text-(--sk-color-phone-telegram-bar-meta)",
    bg: "bg-(--sk-color-phone-telegram-bg)",
    avatar: "bg-(--sk-color-phone-telegram-bar-fg) text-(--sk-color-phone-telegram-bar)",
    composer: "bg-(--sk-color-phone-telegram-in)",
    actions: ["more"],
  },
  messenger: {
    bar: "bg-(--sk-color-phone-messenger-bar) text-(--sk-color-phone-messenger-bar-fg)",
    meta: "text-(--sk-color-phone-messenger-bar-meta)",
    bg: "bg-(--sk-color-phone-messenger-bg)",
    avatar: "bg-(--sk-color-phone-messenger-accent) text-(--sk-color-phone-messenger-out-fg)",
    composer: "bg-(--sk-color-phone-messenger-in)",
    actions: ["phone", "video"],
  },
};

interface PhoneFrameProps {
  skin: PhoneSkin;
  /** Who the resident is talking to, as the chat app would show it. */
  contact: string;
  /** Under the contact name: "bot", "Active now", a number. */
  status: string;
  /** Read by screen readers. */
  label: string;
  testId: string;
  thread: ReactNode;
  composer: ReactNode;
  children?: ReactNode;
}

/** A resident phone in the look of one chat app (R23). Never shows app logos. */
export function PhoneFrame({
  skin,
  contact,
  status,
  label,
  testId,
  thread,
  composer,
  children,
}: PhoneFrameProps) {
  const style = SKIN[skin];
  return (
    <section
      data-testid={testId}
      data-skin={skin}
      aria-label={label}
      className="flex min-h-0 flex-col items-center gap-(--sk-space-2)"
    >
      <div className="flex min-h-0 w-full max-w-(--sk-phone-width) flex-1 flex-col overflow-hidden rounded-(--sk-radius-sheet) border-(length:--sk-space-2) border-(--sk-color-inverse) bg-(--sk-color-inverse)">
        <div
          className={`relative flex items-center justify-between px-(--sk-space-5) pt-(--sk-space-2) pb-(--sk-space-1) text-(length:--sk-text-caption-size) font-(weight:--sk-text-body-bold-weight) ${style.bar}`}
        >
          <span>9:30</span>
          <span
            aria-hidden
            className="absolute left-1/2 top-(--sk-space-2) h-(--sk-space-5) w-(--sk-space-16) -translate-x-1/2 rounded-(--sk-radius-pill) bg-(--sk-color-inverse)"
          />
          <span aria-hidden className="flex items-center gap-(--sk-space-1)">
            <Icon name="signal" size="sm" />
            <Icon name="wifi" size="sm" />
            <Icon name="battery" size="sm" />
          </span>
        </div>
        <header
          className={`flex items-center gap-(--sk-space-3) px-(--sk-space-4) py-(--sk-space-2) ${style.bar}`}
        >
          <span aria-hidden>
            <Icon name="chevron-left" size="md" />
          </span>
          <span
            aria-hidden
            className={`flex size-(--sk-space-10) items-center justify-center rounded-(--sk-radius-pill) text-(length:--sk-text-body-size) font-(weight:--sk-text-body-bold-weight) ${style.avatar}`}
          >
            S
          </span>
          <span className="flex flex-col">
            <span className="text-(length:--sk-text-body-bold-size) font-(weight:--sk-text-body-bold-weight)">
              {contact}
            </span>
            <span className={`text-(length:--sk-text-caption-size) ${style.meta}`}>{status}</span>
          </span>
          <span aria-hidden className="ml-auto flex items-center gap-(--sk-space-4)">
            {style.actions.map((action) => (
              <Icon key={action} name={action} size="md" />
            ))}
          </span>
        </header>
        <div className={`flex min-h-0 flex-1 flex-col ${style.bg}`}>{thread}</div>
        <div className={style.composer}>
          {composer}
          <div aria-hidden className="flex justify-center pt-(--sk-space-1) pb-(--sk-space-2)">
            <span className="h-(--sk-space-1) w-1/3 rounded-(--sk-radius-pill) bg-(--sk-color-inverse)" />
          </div>
        </div>
      </div>
      {children}
    </section>
  );
}
