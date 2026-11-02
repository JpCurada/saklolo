"use client";

import { useState } from "react";

import { Button, Icon, Input, Text } from "@/components/ui";

interface DispatcherPickerProps {
  name: string | undefined;
  onChange: (name: string | undefined) => void;
}

/** Who is on duty. Decisions are blocked until a name is set. */
export function DispatcherPicker({ name, onChange }: DispatcherPickerProps) {
  const [draft, setDraft] = useState("");

  if (name) {
    return (
      <div data-testid="dispatcher-on-duty" className="flex items-center gap-2">
        <Icon name="users" />
        <Text variant="caption" tone="muted">
          On duty:
        </Text>
        <span data-testid="dispatcher-name">
          <Text variant="body-bold">{name}</Text>
        </span>
        <Button
          variant="ghost"
          size="sm"
          testId="dispatcher-change"
          onClick={() => {
            setDraft(name);
            onChange(undefined);
          }}
        >
          Change
        </Button>
      </div>
    );
  }

  return (
    <form
      data-testid="dispatcher-picker"
      className="flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        if (draft.trim()) onChange(draft);
      }}
    >
      <label className="sr-only" htmlFor="dispatcher-input">
        Your name
      </label>
      <Input
        id="dispatcher-input"
        testId="dispatcher-input"
        placeholder="Your name, to start your shift"
        maxLength={80}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <Button type="submit" size="sm" testId="dispatcher-start" disabled={!draft.trim()}>
        Start shift
      </Button>
    </form>
  );
}
