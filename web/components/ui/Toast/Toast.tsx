export interface ToastItem {
  id: string;
  message: string;
}

interface ToastProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

/** A stack of short confirmations. The feature owns the list and its timing. */
export function Toast({ toasts, onDismiss }: ToastProps) {
  return (
    <div
      aria-live="polite"
      data-testid="toasts"
      className="fixed right-(--sk-space-4) bottom-(--sk-space-4) z-50 flex flex-col gap-(--sk-space-2)"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          data-testid="toast"
          className="sk-enter flex items-center gap-(--sk-space-3) rounded-(--sk-radius-pill) bg-(--sk-color-inverse) px-(--sk-space-4) py-(--sk-space-2) text-(length:--sk-text-body-size) text-(--sk-color-ink-on-inverse)"
        >
          {toast.message}
          <button
            type="button"
            aria-label={`Dismiss: ${toast.message}`}
            onClick={() => onDismiss(toast.id)}
            className="focus-visible:outline-(length:--sk-stroke-2) focus-visible:outline-offset-(--sk-stroke-2) focus-visible:outline-(--sk-color-accent)"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
