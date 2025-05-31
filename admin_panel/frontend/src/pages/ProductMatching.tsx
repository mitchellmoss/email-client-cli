import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Loader2, Plus, Edit2, Trash2, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';

interface ProductMapping {
  id: number;
  product_name: string;
  matched_sku: string;
  matched_name: string;
  matched_price: number;
  created_at: string;
  updated_at: string;
}

export default function ProductMatching() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedMapping, setSelectedMapping] = useState<ProductMapping | null>(null);
  const [formData, setFormData] = useState({
    product_name: '',
    matched_sku: '',
    matched_name: '',
    matched_price: ''
  });

  const { data: mappings, isLoading } = useQuery({
    queryKey: ['productMappings', searchTerm],
    queryFn: () => api.get('/products/mappings', {
      params: { search: searchTerm }
    }).then(res => res.data)
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/products/mappings', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productMappings'] });
      setIsAddDialogOpen(false);
      resetForm();
      toast({
        title: 'Success',
        description: 'Product mapping created successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create product mapping',
        variant: 'destructive',
      });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => 
      api.put(`/products/mappings/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productMappings'] });
      setIsEditDialogOpen(false);
      setSelectedMapping(null);
      resetForm();
      toast({
        title: 'Success',
        description: 'Product mapping updated successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update product mapping',
        variant: 'destructive',
      });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/products/mappings/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['productMappings'] });
      toast({
        title: 'Success',
        description: 'Product mapping deleted successfully',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete product mapping',
        variant: 'destructive',
      });
    }
  });

  const resetForm = () => {
    setFormData({
      product_name: '',
      matched_sku: '',
      matched_name: '',
      matched_price: ''
    });
  };

  const handleAdd = () => {
    createMutation.mutate({
      ...formData,
      matched_price: parseFloat(formData.matched_price)
    });
  };

  const handleEdit = () => {
    if (selectedMapping) {
      updateMutation.mutate({
        id: selectedMapping.id,
        data: {
          ...formData,
          matched_price: parseFloat(formData.matched_price)
        }
      });
    }
  };

  const openEditDialog = (mapping: ProductMapping) => {
    setSelectedMapping(mapping);
    setFormData({
      product_name: mapping.product_name,
      matched_sku: mapping.matched_sku,
      matched_name: mapping.matched_name,
      matched_price: mapping.matched_price.toString()
    });
    setIsEditDialogOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Product Matching</h1>
        <p className="mt-2 text-sm text-gray-700">
          Map unmatched products to Laticrete SKUs for automatic pricing
        </p>
      </div>

      <div className="mb-6 flex justify-between items-center">
        <div className="flex items-center space-x-2 max-w-sm">
          <Search className="w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1"
          />
        </div>
        <Button onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Mapping
        </Button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Product Name</TableHead>
              <TableHead>Matched SKU</TableHead>
              <TableHead>Matched Name</TableHead>
              <TableHead>Price</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mappings?.map((mapping: ProductMapping) => (
              <TableRow key={mapping.id}>
                <TableCell className="font-medium">{mapping.product_name}</TableCell>
                <TableCell>{mapping.matched_sku}</TableCell>
                <TableCell>{mapping.matched_name}</TableCell>
                <TableCell>${mapping.matched_price.toFixed(2)}</TableCell>
                <TableCell>
                  {new Date(mapping.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditDialog(mapping)}
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(mapping.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {mappings?.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No product mappings found
          </div>
        )}
      </div>

      {/* Add Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Product Mapping</DialogTitle>
            <DialogDescription>
              Map an unmatched product name to a Laticrete SKU
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="product_name" className="text-right">
                Product Name
              </Label>
              <Input
                id="product_name"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="matched_sku" className="text-right">
                SKU
              </Label>
              <Input
                id="matched_sku"
                value={formData.matched_sku}
                onChange={(e) => setFormData({ ...formData, matched_sku: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="matched_name" className="text-right">
                Matched Name
              </Label>
              <Input
                id="matched_name"
                value={formData.matched_name}
                onChange={(e) => setFormData({ ...formData, matched_name: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="matched_price" className="text-right">
                Price
              </Label>
              <Input
                id="matched_price"
                type="number"
                step="0.01"
                value={formData.matched_price}
                onChange={(e) => setFormData({ ...formData, matched_price: e.target.value })}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAdd} disabled={createMutation.isPending}>
              {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Add Mapping
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Product Mapping</DialogTitle>
            <DialogDescription>
              Update the product mapping details
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit_product_name" className="text-right">
                Product Name
              </Label>
              <Input
                id="edit_product_name"
                value={formData.product_name}
                onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit_matched_sku" className="text-right">
                SKU
              </Label>
              <Input
                id="edit_matched_sku"
                value={formData.matched_sku}
                onChange={(e) => setFormData({ ...formData, matched_sku: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit_matched_name" className="text-right">
                Matched Name
              </Label>
              <Input
                id="edit_matched_name"
                value={formData.matched_name}
                onChange={(e) => setFormData({ ...formData, matched_name: e.target.value })}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit_matched_price" className="text-right">
                Price
              </Label>
              <Input
                id="edit_matched_price"
                type="number"
                step="0.01"
                value={formData.matched_price}
                onChange={(e) => setFormData({ ...formData, matched_price: e.target.value })}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} disabled={updateMutation.isPending}>
              {updateMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Update Mapping
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}