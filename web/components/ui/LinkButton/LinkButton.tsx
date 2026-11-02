import Link from "next/link";
import type { ReactNode } from "react";

import { buttonClasses } from "../Button/Button";

interface LinkButtonProps {
  href: string;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  /** Opens outside the app, in a new tab. */
  external?: boolean;
  testId?: string;
  children: ReactNode;
}

/** A link that looks like a Button: for navigation, never for actions. */
export function LinkButton({ href, variant = "primary", size = "md", external, testId, children }: LinkButtonProps) {
  const className = buttonClasses(variant, size);
  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer" data-testid={testId} className={className}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} data-testid={testId} className={className}>
      {children}
    </Link>
  );
}
