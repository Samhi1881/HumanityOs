import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, SystemStatus } from '../services/api';

type ActiveTab = 'dashboard' | 'canvas' | 'map';

interface AppContextType {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  systemStatus: SystemStatus | null;
  loadingStatus: boolean;
  refreshStatus: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  const refreshStatus = async () => {
    setLoadingStatus(true);
    try {
      const status = await api.getStatus();
      setSystemStatus(status);
    } catch (err) {
      console.error('Failed to retrieve system status:', err);
      setSystemStatus({
        status: 'error',
        database: 'disconnected',
        cache: 'offline'
      });
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    refreshStatus();
  }, []);

  return (
    <AppContext.Provider value={{
      activeTab,
      setActiveTab,
      systemStatus,
      loadingStatus,
      refreshStatus
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
