import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/common/Button';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/dashboard')}
          className="mb-6 inline-flex items-center"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <h1 className="text-3xl font-bold text-white">Settings</h1>

        <div className="mt-8 space-y-6">
          {/* Profile Section */}
          <div className="rounded-lg bg-gray-900 p-6 shadow border border-gray-800">
            <h2 className="text-lg font-semibold text-white">
              Profile Information
            </h2>
            <div className="mt-4 space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-400">Name</label>
                <p className="mt-1 text-gray-200">{user?.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-400">Email</label>
                <p className="mt-1 text-gray-200">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Security Settings - Placeholder */}
          <div className="rounded-lg bg-gray-900 p-6 shadow border border-gray-800">
            <h2 className="text-lg font-semibold text-white">
              Security Settings
            </h2>
            <p className="mt-2 text-sm text-gray-400">
              Manage your MFA methods, trusted devices, and security preferences
            </p>
            <Button variant="primary" className="mt-4">
              Configure MFA
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;