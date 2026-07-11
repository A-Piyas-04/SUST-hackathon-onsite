"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Card({
  children,
  className,
  stripe,
  onClick,
}: {
  children: ReactNode;
  className?: string;
  stripe?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn("rounded-lg border border-border bg-surface p-4 shadow-[var(--shadow-card)]", onClick && "cursor-pointer", className)}
      style={stripe ? { borderLeftWidth: 3, borderLeftColor: stripe } : undefined}
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  disabled,
  variant = "default",
  size = "md",
  type = "button",
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "primary" | "ghost" | "danger";
  size?: "sm" | "md";
  type?: "button" | "submit";
  className?: string;
}) {
  const base = "inline-flex items-center justify-center rounded-md font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const sizes = size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm";
  const variants = {
    default: "border border-border bg-elevated text-foreground hover:bg-subtle",
    primary: "bg-accent text-white hover:opacity-90",
    ghost: "text-secondary hover:bg-subtle hover:text-foreground",
    danger: "border border-danger/30 text-danger hover:bg-danger/5",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={cn(base, sizes, variants[variant], className)}>
      {children}
    </button>
  );
}

export function Badge({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "success" | "warning" | "danger" | "info" }) {
  const tones = {
    default: "bg-subtle text-secondary",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    danger: "bg-danger/10 text-danger",
    info: "bg-info/10 text-info",
  };
  return <span className={cn("inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-4 w-full", className)} />;
}

export function EmptyState({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center text-sm text-secondary">
      <p>{children}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 text-sm text-secondary">
      <p>{message}</p>
      {onRetry && (
        <Button size="sm" className="mt-2" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function Modal({
  open,
  title,
  children,
  onClose,
  footer,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  footer?: ReactNode;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-lg border border-border bg-elevated shadow-[var(--shadow-elevated)]" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="text-sm font-semibold">{title}</h3>
          <button type="button" onClick={onClose} className="text-secondary hover:text-foreground">×</button>
        </div>
        <div className="p-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-border px-4 py-3">{footer}</div>}
      </div>
    </div>
  );
}

export function Textarea({ value, onChange, placeholder, rows = 3 }: { value: string; onChange: (v: string) => void; placeholder?: string; rows?: number }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="w-full rounded-md border border-border bg-elevated px-3 py-2 text-sm outline-none focus:border-accent"
    />
  );
}

export function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-border bg-elevated px-2 py-1.5 text-sm outline-none focus:border-accent"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}
