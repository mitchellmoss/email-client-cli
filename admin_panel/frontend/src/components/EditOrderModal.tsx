import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useToast } from '@/components/ui/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Save, Send } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Order {
  id: number;
  order_id: string;
  email_subject: string;
  sent_to: string;
  customer_name: string;
  order_total: string;
  formatted_content: string;
  tileware_products: any[];
  order_data: any;
  original_html: string;
  created_at: string;
  processed_at: string;
  sent_at: string;
}

interface EditOrderModalProps {
  order: Order | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditOrderModal({ order, open, onOpenChange }: EditOrderModalProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Partial<Order>>({});
  const [jsonErrors, setJsonErrors] = useState<{ tileware_products?: string; order_data?: string }>({});
  const [jsonStrings, setJsonStrings] = useState<{ tileware_products: string; order_data: string }>({
    tileware_products: '',
    order_data: ''
  });

  useEffect(() => {
    if (order) {
      setFormData({
        order_id: order.order_id,
        email_subject: order.email_subject,
        sent_to: order.sent_to,
        customer_name: order.customer_name,
        order_total: order.order_total,
        formatted_content: order.formatted_content,
        tileware_products: order.tileware_products,
        order_data: order.order_data,
        original_html: order.original_html,
      });
      setJsonStrings({
        tileware_products: formatJson(order.tileware_products),
        order_data: formatJson(order.order_data)
      });
      setJsonErrors({});
    }
  }, [order]);

  const updateMutation = useMutation({
    mutationFn: async (data: { orderId: string; updates: Partial<Order> }) => {
      return api.patch(`/orders/${data.orderId}`, data.updates);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      toast({
        title: 'Order updated',
        description: 'The order has been successfully updated.',
      });
      onOpenChange(false);
    },
    onError: (error: any) => {
      toast({
        title: 'Update failed',
        description: error.response?.data?.detail || 'Failed to update order',
        variant: 'destructive',
      });
    },
  });

  const resendMutation = useMutation({
    mutationFn: async (orderId: string) => {
      return api.post(`/orders/${orderId}/resend`);
    },
    onSuccess: () => {
      toast({
        title: 'Order resent',
        description: 'The order has been successfully resent.',
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Resend failed',
        description: error.response?.data?.detail || 'Failed to resend order',
        variant: 'destructive',
      });
    },
  });

  const validateAllJson = () => {
    // Validate both JSON fields before saving
    let hasErrors = false;
    ['tileware_products', 'order_data'].forEach((field) => {
      const typedField = field as 'tileware_products' | 'order_data';
      handleJsonBlur(typedField);
      if (jsonErrors[typedField]) {
        hasErrors = true;
      }
    });
    return !hasErrors;
  };

  const handleSave = () => {
    if (!order) return;
    
    // Ensure JSON is validated before saving
    handleJsonBlur('tileware_products');
    handleJsonBlur('order_data');
    
    // Small delay to ensure state updates
    setTimeout(() => {
      if (!jsonErrors.tileware_products && !jsonErrors.order_data) {
        updateMutation.mutate({ orderId: order.order_id, updates: formData });
      }
    }, 100);
  };

  const handleSaveAndResend = async () => {
    if (!order) return;
    
    // Ensure JSON is validated before saving
    handleJsonBlur('tileware_products');
    handleJsonBlur('order_data');
    
    // Small delay to ensure state updates
    setTimeout(async () => {
      if (!jsonErrors.tileware_products && !jsonErrors.order_data) {
        try {
          await updateMutation.mutateAsync({ orderId: order.order_id, updates: formData });
          await resendMutation.mutateAsync(order.order_id);
          onOpenChange(false);
        } catch (error) {
          // Errors are handled by the mutations
        }
      }
    }, 100);
  };

  const handleJsonChange = (field: 'tileware_products' | 'order_data', value: string) => {
    // Update the string value immediately for smooth typing
    setJsonStrings({ ...jsonStrings, [field]: value });
  };

  const handleJsonBlur = (field: 'tileware_products' | 'order_data') => {
    // Validate and parse JSON only when user finishes editing
    const value = jsonStrings[field];
    try {
      if (value.trim() === '') {
        // Allow empty string to represent null or empty array
        setFormData({ ...formData, [field]: field === 'tileware_products' ? [] : null });
        setJsonErrors({ ...jsonErrors, [field]: undefined });
      } else {
        const parsed = JSON.parse(value);
        setFormData({ ...formData, [field]: parsed });
        setJsonErrors({ ...jsonErrors, [field]: undefined });
      }
    } catch (e) {
      setJsonErrors({ ...jsonErrors, [field]: 'Invalid JSON format' });
    }
  };

  const formatJson = (value: any) => {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return '';
    }
  };

  if (!order) return null;

  const isLoading = updateMutation.isPending || resendMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Order #{order.order_id}</DialogTitle>
          <DialogDescription>
            Modify order details below. Changes will be saved to the database.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="basic" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="json">JSON Data</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="order_id">Order ID</Label>
                <Input
                  id="order_id"
                  value={formData.order_id || ''}
                  onChange={(e) => setFormData({ ...formData, order_id: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="customer_name">Customer Name</Label>
                <Input
                  id="customer_name"
                  value={formData.customer_name || ''}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sent_to">Sent To</Label>
                <Input
                  id="sent_to"
                  value={formData.sent_to || ''}
                  onChange={(e) => setFormData({ ...formData, sent_to: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="order_total">Order Total</Label>
                <Input
                  id="order_total"
                  value={formData.order_total || ''}
                  onChange={(e) => setFormData({ ...formData, order_total: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email_subject">Email Subject</Label>
              <Input
                id="email_subject"
                value={formData.email_subject || ''}
                onChange={(e) => setFormData({ ...formData, email_subject: e.target.value })}
              />
            </div>
          </TabsContent>

          <TabsContent value="content" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="formatted_content">Formatted Content</Label>
              <Textarea
                id="formatted_content"
                rows={10}
                value={formData.formatted_content || ''}
                onChange={(e) => setFormData({ ...formData, formatted_content: e.target.value })}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="original_html">Original HTML</Label>
              <Textarea
                id="original_html"
                rows={10}
                value={formData.original_html || ''}
                onChange={(e) => setFormData({ ...formData, original_html: e.target.value })}
                className="font-mono text-sm"
              />
            </div>
          </TabsContent>

          <TabsContent value="json" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="tileware_products">TileWare Products (JSON Array)</Label>
              <Textarea
                id="tileware_products"
                rows={8}
                value={jsonStrings.tileware_products}
                onChange={(e) => handleJsonChange('tileware_products', e.target.value)}
                onBlur={() => handleJsonBlur('tileware_products')}
                className="font-mono text-sm"
                placeholder='[]'
              />
              {jsonErrors.tileware_products && (
                <p className="text-sm text-destructive">{jsonErrors.tileware_products}</p>
              )}
              {!jsonErrors.tileware_products && (
                <p className="text-sm text-muted-foreground">JSON validation occurs when you click outside the field</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="order_data">Order Data (JSON Object)</Label>
              <Textarea
                id="order_data"
                rows={12}
                value={jsonStrings.order_data}
                onChange={(e) => handleJsonChange('order_data', e.target.value)}
                onBlur={() => handleJsonBlur('order_data')}
                className="font-mono text-sm"
                placeholder='null or {}'
              />
              {jsonErrors.order_data && (
                <p className="text-sm text-destructive">{jsonErrors.order_data}</p>
              )}
              {!jsonErrors.order_data && (
                <p className="text-sm text-muted-foreground">JSON validation occurs when you click outside the field</p>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isLoading || Object.keys(jsonErrors).some(k => jsonErrors[k as keyof typeof jsonErrors])}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            Save Changes
          </Button>
          <Button
            onClick={handleSaveAndResend}
            disabled={isLoading || Object.keys(jsonErrors).some(k => jsonErrors[k as keyof typeof jsonErrors])}
            variant="default"
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Send className="mr-2 h-4 w-4" />
            Save & Resend
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}