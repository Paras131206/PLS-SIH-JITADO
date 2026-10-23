import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../api/types';
import { mockUsers } from '../mocks/handlers';
import { apiFetch, setAuthToken, clearAuthToken, getAuthToken } from '../api/client';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole;
  theme: 'light' | 'dark';
  isAuthenticated: boolean;
  toggleTheme: () => void;
  switchRole: (newRole: UserRole) => void;
  login: (email: string, password?: string, requestedRole?: UserRole) => Promise<UserProfile>;
  logout: () => void;
  getRoleHomePath: (targetRole?: UserRole) => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('apaar-theme') as 'light' | 'dark') || 'light';
  });

  // User profile state (safe metadata only, token is stored strictly in memory via setAuthToken)
  const [user, setUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('apaar-user-profile');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Fall through
      }
    }
    return mockUsers['institution_admin@aicte.gov.in'];
  });

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  // Initialize in-memory token on bootstrap
  useEffect(() => {
    setAuthToken('in-memory-jwt-' + btoa(user.email));
  }, [user.email]);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('apaar-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const getRoleHomePath = (targetRole?: UserRole): string => {
    const activeRole = targetRole || user.role;
    switch (activeRole) {
      case 'AICTE_ADMIN':
      case 'AICTE_ANALYST':
        return '/aicte';
      case 'VERIFIER':
        return '/verifier';
      case 'STUDENT':
        return '/student';
      case 'INSTITUTION_ADMIN':
      case 'INSTITUTION_STAFF':
      default:
        return '/institution';
    }
  };

  const switchRole = (newRole: UserRole) => {
    const matchedEmail = Object.keys(mockUsers).find(
      email => mockUsers[email].role === newRole
    );
    if (matchedEmail) {
      const newUser = mockUsers[matchedEmail];
      setUser(newUser);
      setAuthToken('in-memory-jwt-' + btoa(newUser.email));
      localStorage.setItem('apaar-user-profile', JSON.stringify(newUser));
    } else {
      const fallbackUser: UserProfile = {
        id: `usr-${newRole.toLowerCase()}`,
        email: `${newRole.toLowerCase()}@aicte.gov.in`,
        full_name: `${newRole.replace('_', ' ')} Demo User`,
        role: newRole,
      };
      setUser(fallbackUser);
      setAuthToken('in-memory-jwt-' + btoa(fallbackUser.email));
      localStorage.setItem('apaar-user-profile', JSON.stringify(fallbackUser));
    }
  };

  const login = async (email: string, password = 'password123', requestedRole?: UserRole): Promise<UserProfile> => {
    try {
      const data = await apiFetch<{
        access_token: string;
        token_type: string;
        user: UserProfile;
      }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, role: requestedRole }),
      });

      // Store JWT strictly in memory (NEVER in localStorage/sessionStorage)
      setAuthToken(data.access_token);
      setUser(data.user);
      setIsAuthenticated(true);
      localStorage.setItem('apaar-user-profile', JSON.stringify(data.user));
      return data.user;
    } catch {
      // Fallback to mock user
      const fallbackUser = mockUsers[email] || {
        id: 'usr-dynamic',
        email,
        full_name: 'Authorized Institution User',
        role: requestedRole || 'INSTITUTION_ADMIN',
      };
      setAuthToken('in-memory-jwt-' + btoa(fallbackUser.email));
      setUser(fallbackUser);
      setIsAuthenticated(true);
      localStorage.setItem('apaar-user-profile', JSON.stringify(fallbackUser));
      return fallbackUser;
    }
  };

  const logout = () => {
    clearAuthToken();
    localStorage.removeItem('apaar-user-profile');
    setIsAuthenticated(false);
    setUser(mockUsers['institution_admin@aicte.gov.in']);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || 'INSTITUTION_ADMIN',
        theme,
        isAuthenticated,
        toggleTheme,
        switchRole,
        login,
        logout,
        getRoleHomePath,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
