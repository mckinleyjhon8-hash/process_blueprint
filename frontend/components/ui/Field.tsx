import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import { useId } from "react";

/** Label + control + helper wrapper: consistent form anatomy everywhere. */
export function Field({
  label,
  helper,
  children,
  htmlFor,
  className = "",
}: {
  label: string;
  helper?: ReactNode;
  children: ReactNode;
  htmlFor?: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <label htmlFor={htmlFor} className="mb-1.5 block text-xs font-semibold text-fg-2">
        {label}
      </label>
      {children}
      {helper && <p className="mt-1.5 text-2xs leading-relaxed text-muted">{helper}</p>}
    </div>
  );
}

const CONTROL =
  "w-full rounded-xl border border-line bg-bg-elev/60 px-3 py-2 text-sm text-fg placeholder:text-muted " +
  "transition-colors duration-[var(--duration-fast)] hover:border-[#c9cede] focus:border-primary/60";

export function Input({ className = "", ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`${CONTROL} ${className}`} {...rest} />;
}

export function Select({
  className = "",
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={`${CONTROL} cursor-pointer appearance-none ${className}`} {...rest}>
      {children}
    </select>
  );
}

/** Convenience: labelled select in one call (accessible pairing via useId). */
export function LabeledSelect({
  label,
  helper,
  className = "",
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string; helper?: ReactNode }) {
  const id = useId();
  return (
    <Field label={label} helper={helper} htmlFor={id} className={className}>
      <Select id={id} {...rest}>
        {children}
      </Select>
    </Field>
  );
}
