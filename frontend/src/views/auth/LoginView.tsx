import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { ShieldCheck, Lock, Mail, ArrowRight } from 'lucide-react';
import { mockUsers } from '../../mocks/handlers';

export const LoginView: React.FC = () => {
  const { login, getRoleHomePath } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('institution_admin@aicte.gov.in');
  const [password, setPassword] = useState('password123');
  const [isLoading, setIsLoading] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const loggedInUser = await login(email, password);
      setIsLoading(false);
      // Dynamic role-based redirect
      const destination = getRoleHomePath(loggedInUser.role);
      navigate(destination);
    } catch {
      setIsLoading(false);
    }
  };

  const selectQuickRole = (roleEmail: string) => {
    setEmail(roleEmail);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-muted/20">
      <div className="w-full max-w-md space-y-6">
        {/* Emblem & Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gov-navy text-white shadow-md dark:bg-blue-600">
            <ShieldCheck className="h-9 w-9 text-amber-400" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
            APAAR-SDMS Portal
          </h1>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
            AICTE • Ministry of Education (MoE) • Govt of India
          </p>
        </div>

        {/* Login Card */}
        <Card className="shadow-lg border">
          <CardHeader>
            <CardTitle className="text-lg">Portal Sign In</CardTitle>
            <CardDescription>
              JWT stored in memory • Secure role-based redirection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">
                  Official Email / APAAR ID
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    id="email-input"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    className="w-full pl-9 pr-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">
                  Security Password / Token
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    type="password"
                    id="password-input"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    className="w-full pl-9 pr-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="gov"
                id="login-submit-btn"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2"
              >
                {isLoading ? 'Authenticating...' : 'Sign In'}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>

            {/* Quick Demo Role Picker */}
            <div className="mt-6 pt-4 border-t space-y-2">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                Quick Role Demo Accounts:
              </span>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                {Object.keys(mockUsers).map(key => {
                  const u = mockUsers[key];
                  return (
                    <button
                      key={key}
                      type="button"
                      id={`quick-role-${u.role.toLowerCase()}`}
                      onClick={() => selectQuickRole(key)}
                      className={`p-2 rounded border text-left transition-colors ${
                        email === key
                          ? 'bg-primary/10 border-primary font-semibold text-primary dark:text-blue-300'
                          : 'bg-background hover:bg-muted text-muted-foreground'
                      }`}
                    >
                      <div className="truncate font-bold text-[11px] text-foreground">{u.role.replace('_', ' ')}</div>
                      <div className="truncate text-[10px] text-muted-foreground">{u.full_name}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </CardContent>
          <CardFooter className="bg-muted/30 border-t py-3 text-center justify-center text-[11px] text-muted-foreground">
            In-Memory Token Authentication • DPDP Act 2023 Compliant
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};
