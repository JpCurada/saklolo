import Image from "next/image";

import { Text } from "../Text/Text";

const SIZE = {
  md: { width: 240, height: 180, frame: "" },
  lg: { width: 480, height: 360, frame: "h-full justify-center" },
};

interface EmptyStateProps {
  /** A file in `public/`. Assets are already optimized. */
  image: string;
  /** An animated version of `image`. Reduced motion gets `image` instead (R19). */
  animated?: string;
  /** Empty when the image only decorates the text. */
  alt: string;
  title: string;
  body?: string;
  /** `lg` fills and centers in a whole panel. */
  size?: keyof typeof SIZE;
  testId?: string;
}

/** What a panel shows when it has nothing, and what to do next (R22). */
export function EmptyState({
  image,
  animated,
  alt,
  title,
  body,
  size = "md",
  testId,
}: EmptyStateProps) {
  const { width, height, frame } = SIZE[size];
  return (
    <div
      data-testid={testId}
      className={`sk-fade flex flex-col items-center gap-(--sk-space-2) p-(--sk-space-6) text-center ${frame}`}
    >
      {animated ? (
        <picture>
          <source srcSet={image} media="(prefers-reduced-motion: reduce)" />
          {/* Not next/image: its optimizer can flatten animation. */}
          <img src={animated} width={width} height={height} alt={alt} />
        </picture>
      ) : (
        <Image src={image} alt={alt} width={width} height={height} unoptimized />
      )}
      <Text as="p" variant="body-bold">
        {title}
      </Text>
      {body && (
        <Text as="p" variant="caption" tone="muted">
          {body}
        </Text>
      )}
    </div>
  );
}
