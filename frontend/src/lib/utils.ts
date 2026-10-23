import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function maskApaar(apaar: string): string {
  if (!apaar) return '----****----';
  const clean = apaar.replace(/\s+/g, '');
  if (clean.length === 12) {
    return `${clean.slice(0, 4)}****${clean.slice(8)}`;
  }
  if (clean.includes('****')) {
    return clean;
  }
  return clean.length >= 8 ? `${clean.slice(0, 2)}****${clean.slice(-2)}` : '****';
}

export function formatDateTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}
