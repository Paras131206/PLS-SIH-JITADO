import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

describe('APAAR-SDMS App Shell', () => {
  it('renders the portal title and navigation layout', () => {
    render(<App />);
    const headings = screen.getAllByText(/APAAR-SDMS/i);
    expect(headings.length).toBeGreaterThan(0);
    expect(screen.getByText(/AICTE • Ministry of Education/i)).toBeInTheDocument();
  });

  it('renders role switcher and allows changing roles', () => {
    render(<App />);
    const roleSelect = screen.getByLabelText(/Switch User Role/i) as HTMLSelectElement;
    expect(roleSelect).toBeInTheDocument();
    expect(roleSelect.value).toBe('INSTITUTION_ADMIN');

    // Switch to AICTE_ADMIN
    fireEvent.change(roleSelect, { target: { value: 'AICTE_ADMIN' } });
    expect(roleSelect.value).toBe('AICTE_ADMIN');
  });

  it('renders research literature review link', () => {
    render(<App />);
    const litReviewLinks = screen.getAllByText(/Lit Review/i);
    expect(litReviewLinks.length).toBeGreaterThan(0);
  });
});
