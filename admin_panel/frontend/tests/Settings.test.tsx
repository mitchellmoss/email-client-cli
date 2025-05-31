import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Settings from '../src/pages/Settings';
import { AuthContext } from '../src/contexts/AuthContext';
import * as api from '../src/api/client';
import { toast } from '../src/components/ui/use-toast';

// Mock the API client
vi.mock('../src/api/client');

// Mock toast notifications
vi.mock('../src/components/ui/use-toast', () => ({
  toast: vi.fn(),
  useToast: () => ({ toast: vi.fn() }),
}));

const mockAuthContext = {
  user: { id: 1, email: 'test@example.com', username: 'testuser', is_superuser: true },
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
};

const renderSettings = (isAdmin = true) => {
  const context = isAdmin
    ? mockAuthContext
    : { ...mockAuthContext, user: { ...mockAuthContext.user, is_superuser: false } };
  
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={context}>
        <Settings />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders settings page with all tabs for admin', () => {
    renderSettings();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /email configuration/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /api settings/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /backup & restore/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /system info/i })).toBeInTheDocument();
  });

  it('shows limited tabs for non-admin users', () => {
    renderSettings(false);
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /email configuration/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /api settings/i })).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /system info/i })).toBeInTheDocument();
  });

  describe('Email Configuration Tab', () => {
    it('displays email settings', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: {
          imap: {
            server: 'imap.gmail.com',
            port: 993,
            email: 'monitor@example.com',
            use_ssl: true,
          },
          smtp: {
            server: 'smtp.gmail.com',
            port: 587,
            email: 'sender@example.com',
            use_tls: true,
          },
          processing: {
            check_interval_minutes: 5,
            cs_email: 'cs@example.com',
            laticrete_cs_email: 'lat-cs@example.com',
          },
        },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('imap.gmail.com')).toBeInTheDocument();
        expect(screen.getByDisplayValue('993')).toBeInTheDocument();
        expect(screen.getByDisplayValue('monitor@example.com')).toBeInTheDocument();
      });
    });

    it('updates email settings', async () => {
      const user = userEvent.setup();
      
      vi.mocked(api.get).mockResolvedValue({
        data: {
          imap: { server: 'imap.gmail.com', port: 993, email: 'old@example.com' },
          smtp: { server: 'smtp.gmail.com', port: 587 },
          processing: { check_interval_minutes: 5 },
        },
      });

      vi.mocked(api.put).mockResolvedValue({
        data: { message: 'Settings updated successfully' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('old@example.com')).toBeInTheDocument();
      });

      const emailInput = screen.getByDisplayValue('old@example.com');
      await user.clear(emailInput);
      await user.type(emailInput, 'new@example.com');

      const saveButton = screen.getByRole('button', { name: /save email settings/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(vi.mocked(api.put)).toHaveBeenCalledWith(
          '/settings/email',
          expect.objectContaining({
            imap: expect.objectContaining({ email: 'new@example.com' }),
          })
        );
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Success',
            description: 'Email settings updated successfully',
          })
        );
      });
    });

    it('tests email connections', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: {
          imap: { server: 'imap.gmail.com', port: 993 },
          smtp: { server: 'smtp.gmail.com', port: 587 },
          processing: {},
        },
      });

      vi.mocked(api.post).mockResolvedValue({
        data: {
          imap: { success: true, message: 'IMAP connection successful' },
          smtp: { success: true, message: 'SMTP connection successful' },
        },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /test connections/i })).toBeInTheDocument();
      });

      const testButton = screen.getByRole('button', { name: /test connections/i });
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(vi.mocked(api.post)).toHaveBeenCalledWith('/settings/email/test');
        expect(screen.getByText(/imap connection successful/i)).toBeInTheDocument();
        expect(screen.getByText(/smtp connection successful/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Settings Tab', () => {
    it('displays API settings', async () => {
      vi.mocked(api.get).mockImplementation((url) => {
        if (url.includes('/settings/api')) {
          return Promise.resolve({
            data: {
              anthropic: {
                api_key_set: true,
                model: 'claude-3-haiku-20240307',
                temperature: 0.1,
                max_tokens: 1000,
              },
              rate_limits: {
                requests_per_minute: 60,
                tokens_per_minute: 100000,
              },
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      renderSettings();

      // Switch to API settings tab
      const apiTab = screen.getByRole('tab', { name: /api settings/i });
      fireEvent.click(apiTab);

      await waitFor(() => {
        expect(screen.getByText(/api key is set/i)).toBeInTheDocument();
        expect(screen.getByDisplayValue('claude-3-haiku-20240307')).toBeInTheDocument();
        expect(screen.getByDisplayValue('0.1')).toBeInTheDocument();
      });
    });

    it('updates API key', async () => {
      const user = userEvent.setup();
      
      vi.mocked(api.get).mockResolvedValue({
        data: {
          anthropic: { api_key_set: false, model: 'claude-3-haiku-20240307' },
          rate_limits: {},
        },
      });

      vi.mocked(api.put).mockResolvedValue({
        data: { message: 'API settings updated successfully' },
      });

      renderSettings();

      const apiTab = screen.getByRole('tab', { name: /api settings/i });
      fireEvent.click(apiTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/anthropic api key/i)).toBeInTheDocument();
      });

      const apiKeyInput = screen.getByLabelText(/anthropic api key/i);
      await user.type(apiKeyInput, 'sk-ant-api03-new-key');

      const saveButton = screen.getByRole('button', { name: /save api settings/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(vi.mocked(api.put)).toHaveBeenCalledWith(
          '/settings/api',
          expect.objectContaining({
            anthropic: expect.objectContaining({ api_key: 'sk-ant-api03-new-key' }),
          })
        );
      });
    });
  });

  describe('Notifications Tab', () => {
    it('displays notification settings', async () => {
      vi.mocked(api.get).mockImplementation((url) => {
        if (url.includes('/settings/notifications')) {
          return Promise.resolve({
            data: {
              email_notifications: {
                enabled: true,
                recipients: ['admin@example.com', 'backup@example.com'],
                events: ['order_failed', 'system_error', 'daily_summary'],
              },
              webhook_notifications: {
                enabled: false,
                url: '',
                events: [],
              },
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      renderSettings();

      const notifTab = screen.getByRole('tab', { name: /notifications/i });
      fireEvent.click(notifTab);

      await waitFor(() => {
        expect(screen.getByLabelText(/enable email notifications/i)).toBeChecked();
        expect(screen.getByDisplayValue('admin@example.com')).toBeInTheDocument();
        expect(screen.getByLabelText(/order failed/i)).toBeChecked();
        expect(screen.getByLabelText(/system error/i)).toBeChecked();
      });
    });

    it('adds notification recipient', async () => {
      const user = userEvent.setup();
      
      vi.mocked(api.get).mockResolvedValue({
        data: {
          email_notifications: {
            enabled: true,
            recipients: ['admin@example.com'],
            events: ['order_failed'],
          },
          webhook_notifications: { enabled: false },
        },
      });

      vi.mocked(api.put).mockResolvedValue({
        data: { message: 'Notification settings updated successfully' },
      });

      renderSettings();

      const notifTab = screen.getByRole('tab', { name: /notifications/i });
      fireEvent.click(notifTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add recipient/i })).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /add recipient/i });
      fireEvent.click(addButton);

      const newEmailInput = screen.getByPlaceholderText(/enter email address/i);
      await user.type(newEmailInput, 'new@example.com');
      
      const confirmButton = screen.getByRole('button', { name: /add/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(vi.mocked(api.put)).toHaveBeenCalledWith(
          '/settings/notifications',
          expect.objectContaining({
            email_notifications: expect.objectContaining({
              recipients: ['admin@example.com', 'new@example.com'],
            }),
          })
        );
      });
    });
  });

  describe('Backup & Restore Tab', () => {
    it('displays backup settings', async () => {
      vi.mocked(api.get).mockImplementation((url) => {
        if (url.includes('/settings/backup')) {
          return Promise.resolve({
            data: {
              enabled: true,
              schedule: 'daily',
              time: '02:00',
              retention_days: 30,
              last_backup: '2024-01-14T02:00:00',
              backup_location: '/backups/',
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      renderSettings();

      const backupTab = screen.getByRole('tab', { name: /backup & restore/i });
      fireEvent.click(backupTab);

      await waitFor(() => {
        expect(screen.getByText(/daily at 02:00/i)).toBeInTheDocument();
        expect(screen.getByText(/30 days retention/i)).toBeInTheDocument();
        expect(screen.getByText(/last backup.*jan.*14/i)).toBeInTheDocument();
      });
    });

    it('creates manual backup', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: {
          enabled: true,
          schedule: 'daily',
          last_backup: '2024-01-14T02:00:00',
        },
      });

      vi.mocked(api.post).mockResolvedValue({
        data: {
          backup_id: 'backup_20240115_103000',
          size: '15.2 MB',
          location: '/backups/backup_20240115_103000.tar.gz',
        },
      });

      renderSettings();

      const backupTab = screen.getByRole('tab', { name: /backup & restore/i });
      fireEvent.click(backupTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create backup now/i })).toBeInTheDocument();
      });

      const backupButton = screen.getByRole('button', { name: /create backup now/i });
      fireEvent.click(backupButton);

      await waitFor(() => {
        expect(vi.mocked(api.post)).toHaveBeenCalledWith('/settings/backup/create');
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Success',
            description: expect.stringContaining('Backup created successfully'),
          })
        );
      });
    });

    it('restores from backup', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: { enabled: true },
      });

      vi.mocked(api.post).mockResolvedValue({
        data: {
          success: true,
          restored_items: {
            orders: 1500,
            product_mappings: 200,
            settings: 15,
          },
        },
      });

      renderSettings();

      const backupTab = screen.getByRole('tab', { name: /backup & restore/i });
      fireEvent.click(backupTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /restore from backup/i })).toBeInTheDocument();
      });

      const restoreButton = screen.getByRole('button', { name: /restore from backup/i });
      fireEvent.click(restoreButton);

      // Select backup from list (mocked)
      const backupOption = screen.getByText(/backup_20240114_020000/i);
      fireEvent.click(backupOption);

      const confirmButton = screen.getByRole('button', { name: /confirm restore/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(vi.mocked(api.post)).toHaveBeenCalledWith(
          '/settings/backup/restore',
          expect.objectContaining({ backup_id: 'backup_20240114_020000' })
        );
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Success',
            description: expect.stringContaining('Restore completed successfully'),
          })
        );
      });
    });
  });

  describe('System Info Tab', () => {
    it('displays system information', async () => {
      vi.mocked(api.get).mockImplementation((url) => {
        if (url.includes('/settings/system/info')) {
          return Promise.resolve({
            data: {
              version: '1.0.0',
              python_version: '3.9.0',
              platform: 'Linux',
              uptime: '2 days, 3:45:00',
              database: {
                type: 'SQLite',
                size: '15.2 MB',
                order_count: 1523,
              },
              disk_usage: {
                total: '500 GB',
                used: '245 GB',
                free: '255 GB',
                percent: 49,
              },
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      renderSettings();

      const systemTab = screen.getByRole('tab', { name: /system info/i });
      fireEvent.click(systemTab);

      await waitFor(() => {
        expect(screen.getByText('Version: 1.0.0')).toBeInTheDocument();
        expect(screen.getByText('Python: 3.9.0')).toBeInTheDocument();
        expect(screen.getByText('Platform: Linux')).toBeInTheDocument();
        expect(screen.getByText('Uptime: 2 days, 3:45:00')).toBeInTheDocument();
        expect(screen.getByText('1523 orders')).toBeInTheDocument();
        expect(screen.getByText('49% used')).toBeInTheDocument();
      });
    });

    it('displays and filters system logs', async () => {
      vi.mocked(api.get).mockImplementation((url) => {
        if (url.includes('/settings/system/logs')) {
          return Promise.resolve({
            data: {
              logs: [
                {
                  timestamp: '2024-01-15T10:00:00',
                  level: 'INFO',
                  message: 'Email processing started',
                },
                {
                  timestamp: '2024-01-15T10:05:00',
                  level: 'ERROR',
                  message: 'Failed to connect to SMTP',
                },
              ],
              total: 150,
              filtered: 2,
            },
          });
        }
        return Promise.resolve({ data: {} });
      });

      renderSettings();

      const systemTab = screen.getByRole('tab', { name: /system info/i });
      fireEvent.click(systemTab);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /view logs/i })).toBeInTheDocument();
      });

      const viewLogsButton = screen.getByRole('button', { name: /view logs/i });
      fireEvent.click(viewLogsButton);

      await waitFor(() => {
        expect(screen.getByText('Email processing started')).toBeInTheDocument();
        expect(screen.getByText('Failed to connect to SMTP')).toBeInTheDocument();
      });

      // Filter logs
      const filterSelect = screen.getByRole('combobox', { name: /filter by level/i });
      const user = userEvent.setup();
      await user.selectOptions(filterSelect, 'ERROR');

      await waitFor(() => {
        expect(vi.mocked(api.get)).toHaveBeenCalledWith(
          expect.stringContaining('level=ERROR')
        );
      });
    });
  });

  it('exports all settings', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        email: { imap: {}, smtp: {} },
        api: { anthropic: {} },
        notifications: {},
        backup: {},
        export_date: '2024-01-15T10:30:00',
      },
    });

    // Mock window.open
    const mockOpen = vi.fn();
    window.open = mockOpen;

    renderSettings();

    const exportButton = screen.getByRole('button', { name: /export all settings/i });
    fireEvent.click(exportButton);

    await waitFor(() => {
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('/settings/export'),
        '_blank'
      );
    });
  });

  it('imports settings from file', async () => {
    const file = new File(
      [JSON.stringify({ email: { imap: { server: 'new.server.com' } } })],
      'settings.json',
      { type: 'application/json' }
    );

    vi.mocked(api.post).mockResolvedValue({
      data: {
        imported: ['email'],
        skipped: ['api'],
        errors: [],
      },
    });

    renderSettings();

    const importButton = screen.getByRole('button', { name: /import settings/i });
    fireEvent.click(importButton);

    const fileInput = screen.getByLabelText(/choose settings file/i);
    const user = userEvent.setup();
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/settings/import',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      );
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Settings imported successfully',
        })
      );
    });
  });
});