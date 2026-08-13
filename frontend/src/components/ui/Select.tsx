import React from "react";
import { cn } from "../../lib/utils";

export function Select({
  children,
  value,
  onValueChange,
  disabled,
  className
}: {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  className?: string;
}) {
  const options: { value: string; label: string }[] = [];
  let placeholder = "Select...";

  React.Children.forEach(children, (child) => {
    if (React.isValidElement(child)) {
      const childElement = child as any;
      if (childElement.type === SelectItem) {
        options.push({
          value: childElement.props.value,
          label: String(childElement.props.children)
        });
      } else if (childElement.type === SelectValue) {
        placeholder = childElement.props.placeholder || placeholder;
      } else if (childElement.props.children) {
        React.Children.forEach(childElement.props.children, (nestedChild) => {
          if (React.isValidElement(nestedChild)) {
            const nestedChildElement = nestedChild as any;
            if (nestedChildElement.type === SelectItem) {
              options.push({
                value: nestedChildElement.props.value,
                label: String(nestedChildElement.props.children)
              });
            }
          }
        });
      }
    }
  });

  return (
    <select
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
      disabled={disabled}
      className={cn(
        "flex h-10 w-full rounded-md border border-glass-border bg-neutral-900 px-3 py-2 text-sm text-text-primary focus:outline-none disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
    >
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value} className="bg-neutral-900 text-text-primary">
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function SelectTrigger({ children }: any) {
  return <>{children}</>;
}

export function SelectValue({ placeholder }: any) {
  return null;
}

export function SelectContent({ children }: any) {
  return <>{children}</>;
}

export function SelectItem({ value, children }: any) {
  return null;
}
