import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../api/types';
import { mockUsers } from '../mocks/handlers';

interface AuthContextType {
  user: UserProfile | null;
  role: UserRole;
  token: string | null;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  switchRole: (newRole: UserRole) => void;
  login: (email: string, role?: UserRole) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('apaar-theme') as 'light' | 'dark') || 'light';
  });

  const [user, setUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('apaar-current-user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Fall through
      }
    }
    return mockUsers['institution_admin@aicte.gov.in'];
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('apaar-auth-token') || 'mock-initial-token';
  });

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

  const switchRole = (newRole: UserRole) => {
    const matchedEmail = Object.keys(mockUsers).find(
      email => mockUsers[email].role === newRole
    );
    if (matchedEmail) {
      const newUser = mockUsers[matchedEmail];
      setUser(newUser);
      localStorage.setItem('apaar-current-user', JSON.stringify(newUser));
    } else {
      const fallbackUser: UserProfile = {
        id: `usr-${newRole.toLowerCase()}`,
        email: `${newRole.toLowerCase()}@aicte.gov.in`,
        full_name: `${newRole.replace('_', ' ')} Demo User`,
        role: newRole,
      };
      setUser(fallbackUser);
      localStorage.setItem('apaar-current-user', JSON.stringify(fallbackUser));
    }
  };

  const login = async (email: string, requestedRole?: UserRole) => {
    try {
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role: requestedRole }),
      });
      const data = await res.json();
      setUser(data.user);
      setToken(data.access_token);
      localStorage.setItem('apaar-current-user', JSON.stringify(data.user));
      localStorage.setItem('apaar-auth-token', data.access_token);
    } catch {
      if (mockUsers[email]) {
        setUser(mockUsers[email]);
        localStorage.setItem('apaar-current-user', JSON.stringify(mockUsers[email]));
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('apaar-current-user');
    localStorage.removeItem('apaar-auth-token');
    setUser(mockUsers['institution_admin@aicte.gov.in']);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || 'INSTITUTION_ADMIN',
        token,
        theme,
        toggleTheme,
        switchRole,
        login,
        logout,
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
