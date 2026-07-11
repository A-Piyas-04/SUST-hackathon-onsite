"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Card({
  children,
  className,
  topStripe,
  onClick,
}: {
  children: ReactNode;
  className?: string;
  topStripe?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cn(
        "rounded-[12px] border border-border bg-surface p-5",
        onClick && "cursor-pointer",
        className,
      )}
      style={topStripe ? { borderTopWidth: 3, borderTopColor: topStripe, borderTopStyle: "solid" } : undefined}
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
  variant?: "default" | "primary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md";
  type?: "button" | "submit";
  className?: string;
}) {
  const base =
    "inline-flex items-center justify-center rounded-md font-semibold transition disabled:cursor-not-allowed disabled:opacity-50";
  const sizes = size === "sm" ? "px-3 py-1.5 text-[13px]" : "px-4 py-2 text-sm";
  const variants = {
    default: "border border-border bg-surface text-foreground hover:bg-surface-raised",
    primary: "bg-maroon text-white hover:opacity-90",
    ghost: "text-secondary hover:bg-surface-raised hover:text-foreground",
    danger: "border border-danger/30 text-danger hover:bg-danger-bg",
    outline:
      "border border-border bg-surface text-foreground hover:border-maroon-border hover:text-maroon",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={cn(base, sizes, variants[variant], className)}>
      {children}
    </button>
  );
}

export function Badge({
  children,
  tone = "default",
  pill,
}: {
  children: ReactNode;
  tone?: "default" | "success" | "warning" | "danger" | "info";
  pill?: boolean;
}) {
  const tones = {
    default: "bg-surface-raised text-secondary border border-border",
    success: "bg-[var(--success-bg)] text-success border border-[rgba(22,101,52,0.2)]",
    warning: "bg-[var(--warning-bg)] text-warning border border-[rgba(146,64,14,0.2)]",
    danger: "bg-[var(--danger-bg)] text-danger border border-[rgba(153,27,27,0.2)]",
    info: "bg-[var(--info-bg)] text-info border border-[rgba(30,64,175,0.2)]",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide",
        pill ? "rounded-full" : "rounded",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton h-4 w-full", className)} />;
}

export function EmptyState({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center text-[13px] text-[var(--text-faint)]">
      <p>{children}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-[12px] border border-border bg-surface p-4 text-sm text-secondary">
      <p>{message}</p>
      {onRetry && (
        <Button size="sm" variant="primary" className="mt-2" onClick={onRetry}>
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div
        className="w-full max-w-md rounded-[12px] border border-border bg-surface"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="text-sm font-semibold">{title}</h3>
          <button type="button" onClick={onClose} className="text-secondary hover:text-foreground">
            ×
          </button>
        </div>
        <div className="p-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-border px-4 py-3">{footer}</div>}
      </div>
    </div>
  );
}

export function Textarea({
  value,
  onChange,
  placeholder,
  rows = 3,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-maroon-border"
    />
  );
}

export function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-border bg-surface px-2 py-1.5 text-sm outline-none focus:border-maroon-border"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function FilterChip({
  active,
  children,
  onClick,
}: {
  active?: boolean;
  children: ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-[13px] font-medium transition",
        active
          ? "border-maroon-border bg-maroon-light text-maroon"
          : "border-border bg-surface text-body hover:bg-surface-raised",
      )}
    >
      {children}
    </button>
  );
}

export function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-6 w-11 shrink-0 rounded-full transition disabled:cursor-not-allowed disabled:opacity-50",
        checked ? "bg-maroon" : "bg-[var(--border)]",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 h-5 w-5 rounded-full bg-white transition",
          checked ? "left-[22px]" : "left-0.5",
        )}
      />
    </button>
  );
}
