import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { format } from 'date-fns';
import { Loader2, Search, RefreshCw, Edit } from 'lucide-react';
import { EditOrderModal } from '@/components/EditOrderModal';

export default function Orders() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [editingOrder, setEditingOrder] = useState<any>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const limit = 20;

  const { data: orders, isLoading, refetch } = useQuery({
    queryKey: ['orders', page, search],
    queryFn: () => 
      api.get('/orders', {
        params: {
          skip: page * limit,
          limit,
          search: search || undefined
        }
      }).then(res => res.data)
  });

  const handleResend = async (orderId: string) => {
    try {
      await api.post(`/orders/${orderId}/resend`);
      alert('Order resent successfully');
    } catch (error: any) {
      alert('Failed to resend order: ' + (error.response?.data?.detail || error.message));
    }
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
        <h1 className="text-2xl font-semibold text-gray-900">Orders</h1>
        <p className="mt-2 text-sm text-gray-700">
          View and manage processed orders
        </p>
      </div>

      {/* Search and Actions */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search orders..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Orders Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {orders && orders.length > 0 ? (
            orders.map((order: any) => (
              <li key={order.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-indigo-600 truncate">
                        Order #{order.order_id}
                      </p>
                      <p className="ml-4 text-sm text-gray-500">
                        {order.customer_name}
                      </p>
                    </div>
                    <div className="ml-2 flex-shrink-0 flex space-x-2">
                      <button
                        onClick={() => {
                          setEditingOrder(order);
                          setEditModalOpen(true);
                        }}
                        className="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-900 inline-flex items-center"
                      >
                        <Edit className="h-4 w-4 mr-1" />
                        Edit
                      </button>
                      <button
                        onClick={() => handleResend(order.order_id)}
                        className="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-900"
                      >
                        Resend
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        Sent to: {order.sent_to}
                      </p>
                      <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                        Total: {order.order_total}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      {format(new Date(order.created_at), 'MMM d, yyyy h:mm a')}
                    </div>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="px-4 py-8 text-center text-gray-500">
              No orders found
            </li>
          )}
        </ul>
      </div>

      {/* Pagination */}
      {orders && orders.length > 0 && (
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">
            Page {page + 1}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={orders.length < limit}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Edit Order Modal */}
      <EditOrderModal
        order={editingOrder}
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
      />
    </div>
  );
}