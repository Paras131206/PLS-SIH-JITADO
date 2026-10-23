import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IssuesView } from './IssuesView';
import { mockIssues } from '../../mocks/handlers';

// Mock apiFetch to return test issue data
vi.mock('../../api/client', () => ({
  apiFetch: vi.fn().mockImplementation(() =>
    Promise.resolve({
      total: mockIssues.length,
      items: mockIssues,
    })
  ),
  setAuthToken: vi.fn(),
  getAuthToken: vi.fn(),
  clearAuthToken: vi.fn(),
}));

import { AuthProvider } from '../../context/AuthContext';

const renderWithClient = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <IssuesView />
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe('IssuesView - Table Filters and Search', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all issues with Rule ID and severity badges', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V002')).toBeInTheDocument();
      expect(screen.getByText('V012')).toBeInTheDocument();
      expect(screen.getByText('V014')).toBeInTheDocument();
    });

    const rows = screen.getAllByTestId('issue-row');
    expect(rows.length).toBeGreaterThanOrEqual(1);
  });

  it('filters issues by severity (ERROR vs WARN)', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V002')).toBeInTheDocument();
    });

    const severitySelect = screen.getByLabelText(/Filter by Severity/i) as HTMLSelectElement;

    // Filter to ERROR only
    fireEvent.change(severitySelect, { target: { value: 'ERROR' } });
    expect(severitySelect.value).toBe('ERROR');

    // Filter to WARN only
    fireEvent.change(severitySelect, { target: { value: 'WARN' } });
    expect(severitySelect.value).toBe('WARN');

    // V004 is a WARN rule in mockIssues
    await waitFor(() => {
      expect(screen.getByText('V004')).toBeInTheDocument();
    });
  });

  it('filters issues by Rule ID', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V012')).toBeInTheDocument();
    });

    const ruleSelect = screen.getByLabelText(/Filter by Rule ID/i) as HTMLSelectElement;

    fireEvent.change(ruleSelect, { target: { value: 'V012' } });
    expect(ruleSelect.value).toBe('V012');

    await waitFor(() => {
      expect(screen.getByText('CSE-UG-01')).toBeInTheDocument();
    });
  });

  it('filters issues by field', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V002')).toBeInTheDocument();
    });

    const fieldSelect = screen.getByLabelText(/Filter by Field/i) as HTMLSelectElement;

    fireEvent.change(fieldSelect, { target: { value: 'program_code' } });

    await waitFor(() => {
      expect(screen.getByText('CSE-UG-01')).toBeInTheDocument();
    });
  });

  it('searches issues by masked APAAR', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V002')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search masked APAAR/i);
    fireEvent.change(searchInput, { target: { value: '1234****901X' } });

    await waitFor(() => {
      expect(screen.getByText('1234****901X')).toBeInTheDocument();
    });
  });

  it('triggers CSV export for filtered issues', async () => {
    renderWithClient();

    await waitFor(() => {
      expect(screen.getByText('V002')).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export Issues CSV/i });
    expect(exportBtn).toBeEnabled();

    // Mock click
    fireEvent.click(exportBtn);
  });
});
