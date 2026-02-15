import { useState, useEffect } from 'react';
import { sessionService } from '@/services/api/sessionService';
import { Session } from '@/types/session.types';

export const useSession = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await sessionService.getSessions();
      setSessions(data);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to load sessions';
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const terminateSession = async (sessionId: string): Promise<boolean> => {
    setError(null);
    try {
      await sessionService.terminateSession(sessionId);
      setSessions(sessions.filter(s => s.session_id !== sessionId));
      return true;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to terminate session';
      setError(errorMsg);
      return false;
    }
  };

  const terminateAllOtherSessions = async (): Promise<boolean> => {
    setError(null);
    try {
      await sessionService.terminateAllOtherSessions();
      setSessions(sessions.filter(s => s.is_current));
      return true;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to terminate sessions';
      setError(errorMsg);
      return false;
    }
  };

  const refreshSessions = () => {
    loadSessions();
  };

  useEffect(() => {
    loadSessions();
  }, []);

  return {
    sessions,
    isLoading,
    error,
    loadSessions,
    terminateSession,
    terminateAllOtherSessions,
    refreshSessions,
  };
};