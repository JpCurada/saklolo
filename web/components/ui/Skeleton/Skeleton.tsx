const WIDTH = ["w-full", "w-5/6", "w-2/3"];

/** Placeholder lines while content loads. Hidden from screen readers. */
export function Skeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div
      aria-hidden
      data-testid="skeleton"
      className="flex flex-col gap-(--sk-space-2) p-(--sk-space-4)"
    >
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={index}
          className={`sk-skeleton h-(--sk-space-3) rounded-(--sk-radius-pill) ${WIDTH[index % WIDTH.length]}`}
        />
      ))}
    </div>
  );
}
