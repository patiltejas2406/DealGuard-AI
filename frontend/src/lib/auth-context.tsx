'use client';

/**
 * Authentication Context and Session State Provider
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, ApiError, tokenStore } from '@/lib/api';
import { CurrentUserProfile, OrganizationBrief, User } from '@/types';

interface AuthContextType {
  user: User | null;
  organization: OrganizationBrief | null;
  role: string | null;
  permissions: string[];
  accessibleOrganizations: OrganizationBrief[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, organizationId?: string) => Promise<void>;
  logout: () => Promise<void>;
  switchOrganization: (orgId: string) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (roleName: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<OrganizationBrief | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [accessibleOrganizations, setAccessibleOrganizations] = useState<OrganizationBrief[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    tokenStore.init();
    const token = tokenStore.getAccessToken();
    if (token) {
      loadUserProfile();
    } else {
      setIsLoading(false);
    }
  }, []);

  const loadUserProfile = async () => {
    try {
      setIsLoading(true);
      const profile: CurrentUserProfile = await api.getMe();
      setUser(profile.user);
      setOrganization(profile.organization);
      setRole(profile.role);
      setPermissions(profile.permissions);
      setAccessibleOrganizations(profile.accessible_organizations);
      if (profile.organization?.id) {
        tokenStore.setOrgId(profile.organization.id);
      }
    } catch (err) {
      console.warn('Failed to fetch user profile:', err);
      if (err instanceof ApiError && err.status === 401) {
        tokenStore.setAccessToken(null);
        tokenStore.setOrgId(null);
        setUser(null);
        setOrganization(null);
        setRole(null);
        setPermissions([]);
        setAccessibleOrganizations([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string, organizationId?: string) => {
    setIsLoading(true);
    try {
      const res = await api.login(email, password, organizationId);
      tokenStore.setAccessToken(res.access_token);
      tokenStore.setOrgId(res.organization.id);
      setUser(res.user);
      setOrganization(res.organization);
      setRole(res.role);
      setPermissions(res.permissions);
      if (typeof window !== 'undefined') {
        localStorage.setItem('dealguard_refresh_token_fallback', res.refresh_token);
      }
      await loadUserProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      const fallbackRefresh = typeof window !== 'undefined' ? localStorage.getItem('dealguard_refresh_token_fallback') : '';
      if (fallbackRefresh) {
        await api.logout(fallbackRefresh).catch(() => {});
      }
    } finally {
      tokenStore.setAccessToken(null);
      tokenStore.setOrgId(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('dealguard_refresh_token_fallback');
      }
      setUser(null);
      setOrganization(null);
      setRole(null);
      setPermissions([]);
      setAccessibleOrganizations([]);
      setIsLoading(false);
    }
  };

  const switchOrganization = async (orgId: string) => {
    tokenStore.setOrgId(orgId);
    await loadUserProfile();
  };

  const hasPermission = (permission: string): boolean => {
    if (user?.is_superuser || permissions.includes('*')) return true;
    return permissions.includes(permission);
  };

  const hasRole = (roleName: string): boolean => {
    if (user?.is_superuser) return true;
    return role?.toUpperCase() === roleName.toUpperCase();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        role,
        permissions,
        accessibleOrganizations,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        switchOrganization,
        hasPermission,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
