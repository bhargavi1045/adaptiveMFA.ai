import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Input } from '@/components/common/Input';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { Card } from '@/components/common/Card';
import { ROUTES } from '@/utils/constants';
import {authService} from '@/services/api/authService';

const PasswordReset: React.FC = () => {
  const [email, setEmail] = useState(''); 
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);

  try {
    await authService.requestPasswordReset(email);
    setSent(true);
  } catch (err) {
    console.error('Password reset error:', err);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4">
      <Card className="w-full max-w-md p-6 bg-gray-900 border border-gray-800">
        <h1 className="mb-2 text-2xl font-semibold text-white">
          Reset password
        </h1>

        <p className="mb-6 text-sm text-gray-400">
          Enter your email and we'll send you a reset link.
        </p>

        {sent ? (
          <Alert
            type="success"
            title="Check your email"
            message="We sent you a password reset link."
          />
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Button
              type="submit"
              className="w-full"
              isLoading={loading}
              disabled={!email}
            >
              Send reset link
            </Button>
          </form>
        )}

        <div className="mt-6 text-center text-sm">
          <Link
            to={ROUTES.LOGIN}
            className="font-medium text-blue-400 hover:text-blue-300"
          >
            Back to login
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default PasswordReset;