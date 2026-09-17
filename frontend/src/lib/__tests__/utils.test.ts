import { describe, it, expect } from 'vitest';
import { cn } from '../utils';

describe('cn utility', () => {
  it('combines simple class names', () => {
    expect(cn('px-2', 'py-1')).toBe('px-2 py-1');
  });

  it('handles conditional class names', () => {
    const isTrue = true;
    const isFalse = false;
    expect(cn('btn', isTrue && 'active', isFalse && 'hidden')).toBe('btn active');
  });

  it('merges tailwind conflicts correctly', () => {
    expect(cn('p-4', 'p-8')).toBe('p-8');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
  });
});
