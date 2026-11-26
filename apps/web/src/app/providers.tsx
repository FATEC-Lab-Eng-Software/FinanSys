"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useRef, useState } from "react";

type AuthSessionContextValue = {
  userId: string | null;
  setUserId: (userId: string | null) => void;
};

const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

export function useAuthSession() {
  const context = useContext(AuthSessionContext);
  if (!context) throw new Error("useAuthSession precisa estar dentro de Providers");
  return context;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const [userId, setUserIdState] = useState<string | null>(null);
  const currentUserId = useRef<string | null>(null);
  const setUserId = useCallback((nextUserId: string | null) => {
    const previousUserId = currentUserId.current;
    if (previousUserId && previousUserId !== nextUserId) {
      queryClient.removeQueries({ queryKey: ["notifications", previousUserId], exact: true });
    }
    currentUserId.current = nextUserId;
    setUserIdState(nextUserId);
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthSessionContext.Provider value={{ userId, setUserId }}>
        {children}
      </AuthSessionContext.Provider>
    </QueryClientProvider>
  );
}
