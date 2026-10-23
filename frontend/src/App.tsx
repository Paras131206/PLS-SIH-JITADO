import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { MainLayout } from './components/layout/MainLayout';

// Views
import { LoginView } from './views/auth/LoginView';
import { InstitutionView } from './views/institution/InstitutionView';
import { UploadBatchView } from './views/institution/UploadBatchView';
import { IssuesView } from './views/institution/IssuesView';
import { AicteConsoleView } from './views/aicte/AicteConsoleView';
import { DuplicatesView } from './views/aicte/DuplicatesView';
import { AnomaliesView } from './views/aicte/AnomaliesView';
import { AuditChainView } from './views/aicte/AuditChainView';
import { VerifierView } from './views/verifier/VerifierView';
import { StudentView } from './views/student/StudentView';
import { LiteratureReviewView } from './views/docs/LiteratureReviewView';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 60000,
    },
  },
});

// Role-based Root Redirector
const RootRedirect: React.FC = () => {
  const { role } = useAuth();
  if (role === 'AICTE_ADMIN' || role === 'AICTE_ANALYST') {
    return <Navigate to="/aicte" replace />;
  }
  if (role === 'VERIFIER') {
    return <Navigate to="/verifier" replace />;
  }
  if (role === 'STUDENT') {
    return <Navigate to="/student" replace />;
  }
  return <Navigate to="/institution" replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginView />} />

            <Route path="/" element={<MainLayout />}>
              <Route index element={<RootRedirect />} />

              {/* Institution Routes */}
              <Route path="institution" element={<InstitutionView />} />
              <Route path="institution/upload" element={<UploadBatchView />} />
              <Route path="institution/issues" element={<IssuesView />} />
              <Route path="institution/intake" element={<InstitutionView />} />

              {/* AICTE Routes */}
              <Route path="aicte" element={<AicteConsoleView />} />
              <Route path="aicte/batches" element={<InstitutionView />} />
              <Route path="aicte/duplicates" element={<DuplicatesView />} />
              <Route path="aicte/anomalies" element={<AnomaliesView />} />
              <Route path="aicte/audit" element={<AuditChainView />} />

              {/* Verifier Routes */}
              <Route path="verifier" element={<VerifierView />} />
              <Route path="verifier/history" element={<VerifierView />} />

              {/* Student Routes */}
              <Route path="student" element={<StudentView />} />
              <Route path="student/consent" element={<StudentView />} />
              <Route path="student/share" element={<StudentView />} />

              {/* Research & Specs */}
              <Route path="literature-review" element={<LiteratureReviewView />} />

              {/* Catch-all */}
              <Route path="*" element={<RootRedirect />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
