"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "../Button/Button";
import { Text } from "../Text/Text";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  /** `danger` for actions that end something, such as signing out mid-shift. */
  tone?: "primary" | "danger";
  onConfirm: () => Promise<void> | void;
  onCancel: () => void;
  testId?: string;
}

/** Asks once before an action that's hard to undo. Native <dialog>: Escape and focus work. */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  tone = "primary",
  onConfirm,
  onCancel,
  testId,
}: ConfirmDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  return (
    <dialog
      ref={dialog}
      data-testid={testId}
      aria-labelledby={testId ? `${testId}-title` : undefined}
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onCancel();
      }}
      className="sk-enter m-auto flex-col gap-(--sk-space-3) rounded-(--sk-radius-card) bg-(--sk-color-canvas) p-(--sk-space-6) text-(--sk-color-ink) open:flex backdrop:bg-(--sk-color-inverse)/40"
    >
      <Text as="h2" variant="title-m">
        <span id={testId ? `${testId}-title` : undefined}>{title}</span>
      </Text>
      <Text as="p" tone="muted">
        {body}
      </Text>
      <div className="mt-(--sk-space-2) flex justify-end gap-(--sk-space-2)">
        <Button
          variant="secondary"
          disabled={pending}
          onClick={onCancel}
          testId={testId && `${testId}-cancel`}
        >
          Cancel
        </Button>
        <Button
          variant={tone}
          loading={pending}
          testId={testId && `${testId}-confirm`}
          onClick={async () => {
            setPending(true);
            try {
              await onConfirm();
            } finally {
              setPending(false);
            }
          }}
        >
          {confirmLabel}
        </Button>
      </div>
    </dialog>
  );
}
