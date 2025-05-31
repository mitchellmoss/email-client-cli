import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Loader2, Save, TestTube, Play, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { Textarea } from '@/components/ui/textarea';

export default function Settings() {
  const { toast } = useToast();
  const [emailConfig, setEmailConfig] = useState({
    imap: {
      server: '',
      port: 993,
      email_address: '',
      password: '',
      has_password: false
    },
    smtp: {
      server: '',
      port: 587,
      username: '',
      password: '',
      has_password: false
    },
    recipients: {
      cs_email: '',
      laticrete_cs_email: ''
    },
    processing: {
      check_interval_minutes: 5,
      log_level: 'INFO'
    }
  });

  const [emailTemplate, setEmailTemplate] = useState({
    subject: 'Order #{order_id} - {customer_name}',
    body: ''
  });

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['emailConfig'],
    queryFn: () => api.get('/email-config').then(res => res.data)
  });

  // Update emailConfig state when data is received
  useEffect(() => {
    if (config) {
      setEmailConfig({
        imap: {
          server: config.imap?.server || '',
          port: config.imap?.port || 993,
          email_address: config.imap?.email_address || '',
          password: '',
          has_password: config.imap?.has_password || false
        },
        smtp: {
          server: config.smtp?.server || '',
          port: config.smtp?.port || 587,
          username: config.smtp?.username || '',
          password: '',
          has_password: config.smtp?.has_password || false
        },
        recipients: {
          cs_email: config.recipients?.cs_email || '',
          laticrete_cs_email: config.recipients?.laticrete_cs_email || ''
        },
        processing: {
          check_interval_minutes: config.processing?.check_interval_minutes || 5,
          log_level: config.processing?.log_level || 'INFO'
        }
      });
      
      // Also update email template if present
      if (config.templates) {
        setEmailTemplate({
          subject: config.templates.subject || 'Order #{order_id} - {customer_name}',
          body: config.templates.body || ''
        });
      }
    }
  }, [config]);

  const { data: systemStatus } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => api.get('/system/status').then(res => res.data),
    refetchInterval: 5000
  });

  const updateConfigMutation = useMutation({
    mutationFn: (data: any) => api.put('/email-config', data),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Email configuration updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update email configuration',
        variant: 'destructive',
      });
    }
  });

  const testConnectionMutation = useMutation({
    mutationFn: () => api.post('/email-config/test-connection'),
    onSuccess: (response) => {
      toast({
        title: 'Success',
        description: response.data.message || 'Connection test successful',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Connection test failed',
        variant: 'destructive',
      });
    }
  });

  const startSystemMutation = useMutation({
    mutationFn: () => api.post('/system/start'),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Email processor started',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to start email processor',
        variant: 'destructive',
      });
    }
  });

  const stopSystemMutation = useMutation({
    mutationFn: () => api.post('/system/stop'),
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'Email processor stopped',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to stop email processor',
        variant: 'destructive',
      });
    }
  });

  const handleSaveConfig = () => {
    updateConfigMutation.mutate({
      ...emailConfig,
      templates: emailTemplate
    });
  };

  if (configLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-700">
          Configure email processing and system settings
        </p>
      </div>

      <Tabs defaultValue="email" className="space-y-4">
        <TabsList>
          <TabsTrigger value="email">Email Configuration</TabsTrigger>
          <TabsTrigger value="templates">Email Templates</TabsTrigger>
          <TabsTrigger value="system">System Control</TabsTrigger>
        </TabsList>

        <TabsContent value="email" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>IMAP Settings</CardTitle>
              <CardDescription>
                Configure email reading settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="imap_server">IMAP Server</Label>
                  <Input
                    id="imap_server"
                    value={emailConfig.imap.server}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      imap: { ...emailConfig.imap, server: e.target.value }
                    })}
                    placeholder="imap.gmail.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="imap_port">IMAP Port</Label>
                  <Input
                    id="imap_port"
                    type="number"
                    value={emailConfig.imap.port}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      imap: { ...emailConfig.imap, port: parseInt(e.target.value) }
                    })}
                    placeholder="993"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email_address">Email Address</Label>
                  <Input
                    id="email_address"
                    type="email"
                    value={emailConfig.imap.email_address}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      imap: { ...emailConfig.imap, email_address: e.target.value }
                    })}
                    placeholder="monitor@gmail.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email_password">Email Password</Label>
                  <Input
                    id="email_password"
                    type="password"
                    value={emailConfig.imap.password}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      imap: { ...emailConfig.imap, password: e.target.value }
                    })}
                    placeholder={emailConfig.imap.has_password ? "Password is set (leave blank to keep current)" : "App password"}
                  />
                  {emailConfig.imap.has_password && (
                    <p className="text-xs text-green-600">✓ Password is currently set</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>SMTP Settings</CardTitle>
              <CardDescription>
                Configure email sending settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="smtp_server">SMTP Server</Label>
                  <Input
                    id="smtp_server"
                    value={emailConfig.smtp.server}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      smtp: { ...emailConfig.smtp, server: e.target.value }
                    })}
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_port">SMTP Port</Label>
                  <Input
                    id="smtp_port"
                    type="number"
                    value={emailConfig.smtp.port}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      smtp: { ...emailConfig.smtp, port: parseInt(e.target.value) }
                    })}
                    placeholder="587"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="smtp_username">SMTP Username</Label>
                  <Input
                    id="smtp_username"
                    value={emailConfig.smtp.username}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      smtp: { ...emailConfig.smtp, username: e.target.value }
                    })}
                    placeholder="sender@gmail.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_password">SMTP Password</Label>
                  <Input
                    id="smtp_password"
                    type="password"
                    value={emailConfig.smtp.password}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      smtp: { ...emailConfig.smtp, password: e.target.value }
                    })}
                    placeholder={emailConfig.smtp.has_password ? "Password is set (leave blank to keep current)" : "App password"}
                  />
                  {emailConfig.smtp.has_password && (
                    <p className="text-xs text-green-600">✓ Password is currently set</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Processing Settings</CardTitle>
              <CardDescription>
                Configure order processing settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cs_email">TileWare CS Email</Label>
                  <Input
                    id="cs_email"
                    type="email"
                    value={emailConfig.recipients.cs_email}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      recipients: { ...emailConfig.recipients, cs_email: e.target.value }
                    })}
                    placeholder="cs@company.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="laticrete_cs_email">Laticrete CS Email</Label>
                  <Input
                    id="laticrete_cs_email"
                    type="email"
                    value={emailConfig.recipients.laticrete_cs_email}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      recipients: { ...emailConfig.recipients, laticrete_cs_email: e.target.value }
                    })}
                    placeholder="lat-cs@company.com"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="check_interval">Check Interval (minutes)</Label>
                  <Input
                    id="check_interval"
                    type="number"
                    value={emailConfig.processing.check_interval_minutes}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      processing: { ...emailConfig.processing, check_interval_minutes: parseInt(e.target.value) }
                    })}
                    placeholder="5"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="log_level">Log Level</Label>
                  <select
                    id="log_level"
                    value={emailConfig.processing.log_level}
                    onChange={(e) => setEmailConfig({ 
                      ...emailConfig, 
                      processing: { ...emailConfig.processing, log_level: e.target.value }
                    })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => testConnectionMutation.mutate()}
              disabled={testConnectionMutation.isPending}
            >
              {testConnectionMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <TestTube className="w-4 h-4 mr-2" />
              )}
              Test Connection
            </Button>
            <Button
              onClick={handleSaveConfig}
              disabled={updateConfigMutation.isPending}
            >
              {updateConfigMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Save Configuration
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Email Templates</CardTitle>
              <CardDescription>
                Customize email templates for order notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email_subject">Subject Template</Label>
                <Input
                  id="email_subject"
                  value={emailTemplate.subject}
                  onChange={(e) => setEmailTemplate({ ...emailTemplate, subject: e.target.value })}
                  placeholder="Order #{order_id} - {customer_name}"
                />
                <p className="text-sm text-gray-500">
                  Available variables: {'{order_id}'}, {'{customer_name}'}, {'{order_date}'}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email_body">Body Template</Label>
                <Textarea
                  id="email_body"
                  value={emailTemplate.body}
                  onChange={(e) => setEmailTemplate({ ...emailTemplate, body: e.target.value })}
                  placeholder="Email body template..."
                  rows={10}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Status</CardTitle>
              <CardDescription>
                Monitor and control the email processing system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Status</p>
                  <p className="text-2xl font-bold">
                    {systemStatus?.is_running ? (
                      <span className="text-green-600">Running</span>
                    ) : (
                      <span className="text-red-600">Stopped</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Process ID</p>
                  <p className="text-2xl font-bold">
                    {systemStatus?.pid || 'N/A'}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Last Check</p>
                  <p className="text-sm">
                    {systemStatus?.last_check ? 
                      new Date(systemStatus.last_check).toLocaleString() : 
                      'Never'
                    }
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Uptime</p>
                  <p className="text-sm">
                    {systemStatus?.uptime || 'N/A'}
                  </p>
                </div>
              </div>
              <div className="flex space-x-2">
                {systemStatus?.is_running ? (
                  <Button
                    variant="destructive"
                    onClick={() => stopSystemMutation.mutate()}
                    disabled={stopSystemMutation.isPending}
                  >
                    {stopSystemMutation.isPending ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Square className="w-4 h-4 mr-2" />
                    )}
                    Stop System
                  </Button>
                ) : (
                  <Button
                    onClick={() => startSystemMutation.mutate()}
                    disabled={startSystemMutation.isPending}
                  >
                    {startSystemMutation.isPending ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 mr-2" />
                    )}
                    Start System
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>
                View recent system logs
              </CardDescription>
            </CardHeader>
            <CardContent>
              {systemStatus?.last_logs && systemStatus.last_logs.length > 0 ? (
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-xs font-mono">
                    {systemStatus.last_logs.join('')}
                  </pre>
                </div>
              ) : (
                <p className="text-gray-500">No logs available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}