import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { QRCodeSVG } from 'qrcode.react';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Alert } from '@/components/common/Alert';
import { ROUTES } from '@/utils/constants';
import { Shield, Download, Copy, Check } from 'lucide-react';
import api from '@/services/axios/axiosConfig';
import { downloadTextFile, copyToClipboard } from '@/utils/helpers';

interface User {
  email: string;
  fullName?: string;
  [key: string]: any;
}

interface MFASetupData {
  qr_code_uri: string;
  backup_codes: string[];
  setup_token: string;
  user: User;
}

type Step = 'qr' | 'backup' | 'verify';

const MFASetup: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const setupData = location.state as MFASetupData | undefined;

  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);
  const [step, setStep] = useState<Step>('qr');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ code: string }>();

  useEffect(() => {
    if (!setupData || !setupData.qr_code_uri) {
      navigate(ROUTES.REGISTER);
    }
  }, [setupData, navigate]);

  if (!setupData) return null;

  const onVerifyCode = async (data: { code: string }) => {
    setIsVerifying(true);
    setError('');

    try {
      await api.post('/auth/confirm-mfa-setup', {
        setup_token: setupData.setup_token,
        code: data.code,
      });

      setSuccess('MFA setup completed successfully!');
      setTimeout(() => navigate(ROUTES.LOGIN), 2000);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Invalid code. Please try again.'
      );
    } finally {
      setIsVerifying(false);
    }
  };

  const handleCopyBackupCodes = async () => {
    const codesText = setupData.backup_codes.join('\n');
    const success = await copyToClipboard(codesText);
    if (success) {
      setCopiedCodes(true);
      setTimeout(() => setCopiedCodes(false), 2000);
    }
  };

  const handleDownloadBackupCodes = () => {
    const codesText = `Adaptive MFA Backup Codes\n\nEmail: ${setupData.user?.email}\nGenerated: ${new Date().toISOString()}\n\n${setupData.backup_codes.join(
      '\n'
    )}\n\nKeep these codes safe and secure. Each code can only be used once.`;
    downloadTextFile(codesText, 'mfa-backup-codes.txt');
  };

  const secret =
    setupData.qr_code_uri.split('secret=')[1]?.split('&')[0] || 'N/A';

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950 px-4 py-12">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 mb-4">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">
            Set Up Two-Factor Authentication
          </h1>
          <p className="mt-2 text-gray-400">
            Protect your account with an extra layer of security
          </p>
        </div>

        {/* Steps */}
        <div className="mb-8 flex items-center justify-center space-x-4">
          {(['qr', 'backup', 'verify'] as Step[]).map((s, idx) => (
            <React.Fragment key={s}>
              <div
                className={`flex items-center ${
                  step === s ? 'text-blue-400' : 'text-gray-600'
                }`}
              >
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full ${
                    step === s ? 'bg-blue-600 text-white' : 'bg-gray-700'
                  }`}
                >
                  {idx + 1}
                </div>
                <span className="ml-2 hidden sm:inline">
                  {s === 'qr'
                    ? 'Scan QR'
                    : s === 'backup'
                    ? 'Backup Codes'
                    : 'Verify'}
                </span>
              </div>
              {idx < 2 && <div className="h-px w-16 bg-gray-700"></div>}
            </React.Fragment>
          ))}
        </div>

        {/* Main Card */}
        <div className="rounded-lg bg-gray-900 p-8 shadow-md border border-gray-800">
          {error && (
            <Alert
              type="error"
              message={error}
              onClose={() => setError('')}
              className="mb-6"
            />
          )}
          {success && <Alert type="success" message={success} className="mb-6" />}

          {/* Step 1: QR */}
          {step === 'qr' && (
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-4 text-white">
                Scan this QR code with your authenticator app
              </h2>
              <p className="text-sm text-gray-400 mb-6">
                Use Google Authenticator, Authy, or any TOTP-compatible app
              </p>

              <div className="inline-block rounded-lg bg-white p-4 shadow-sm">
                <QRCodeSVG value={setupData.qr_code_uri} size={256} />
              </div>

              <div className="mt-6">
                <p className="text-sm text-gray-400 mb-2">
                  Can't scan? Enter this code manually:
                </p>
                <div className="inline-block rounded bg-gray-800 px-4 py-2 font-mono text-sm text-gray-300 border border-gray-700">
                  {secret}
                </div>
              </div>

              <Button
                onClick={() => setStep('backup')}
                className="mt-8 w-full"
                variant="primary"
              >
                Continue
              </Button>
            </div>
          )}

          {/* Step 2: Backup Codes */}
          {step === 'backup' && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-white">Save Your Backup Codes</h2>
              <Alert
                type="warning"
                message="Store these codes securely. You can use them to access your account if you lose your phone."
                className="mb-6"
              />

              <div className="rounded-lg bg-gray-800 p-4 mb-6 border border-gray-700">
                <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                  {setupData.backup_codes.map((code, index) => (
                    <div
                      key={index}
                      className="rounded bg-gray-900 px-3 py-2 text-center text-gray-300 border border-gray-700"
                    >
                      {code}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 mb-6">
                <Button
                  onClick={handleCopyBackupCodes}
                  variant="secondary"
                  className="flex-1"
                >
                  {copiedCodes ? (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="mr-2 h-4 w-4" />
                      Copy Codes
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleDownloadBackupCodes}
                  variant="secondary"
                  className="flex-1"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>

              <Button
                onClick={() => setStep('verify')}
                className="w-full"
                variant="primary"
              >
                I've Saved My Codes
              </Button>
            </div>
          )}

          {/* Step 3: Verify */}
          {step === 'verify' && (
            <div>
              <h2 className="text-xl font-semibold mb-4 text-white">Verify Your Setup</h2>
              <p className="text-sm text-gray-400 mb-6">
                Enter the 6-digit code from your authenticator app to complete setup
              </p>

              <form onSubmit={handleSubmit(onVerifyCode)} className="space-y-6">
                <Input
                  label="Verification Code"
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  error={errors.code?.message}
                  {...register('code', {
                    required: 'Code is required',
                    pattern: {
                      value: /^\d{6}$/,
                      message: 'Code must be 6 digits',
                    },
                  })}
                  className="text-center text-2xl tracking-widest"
                  disabled={isVerifying}
                />

                <Button
                  type="submit"
                  className="w-full"
                  variant="primary"
                  isLoading={isVerifying}
                >
                  Complete Setup
                </Button>
              </form>

              <button
                onClick={() => setStep('qr')}
                className="mt-4 w-full text-center text-sm text-blue-400 hover:text-blue-300"
              >
                Go back to QR code
              </button>
            </div>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-gray-600">
          Having trouble? Contact support for assistance
        </p>
      </div>
    </div>
  );
};

export default MFASetup;