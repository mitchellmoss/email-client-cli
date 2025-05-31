import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Orders from '../src/pages/Orders';
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
  user: { id: 1, email: 'test@example.com', username: 'testuser' },
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
};

const renderOrders = () => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>
        <Orders />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

const mockOrders = [
  {
    order_id: '12345',
    customer_name: 'John Doe',
    email: 'john@example.com',
    order_date: '2024-01-15T10:00:00',
    status: 'processed',
    total_amount: 299.99,
    products: [
      { name: 'Product 1', sku: 'SKU1', quantity: 2, price: 149.99 }
    ],
    shipping_address: {
      street: '123 Main St',
      city: 'Anytown',
      state: 'CA',
      zip: '12345'
    },
  },
  {
    order_id: '12346',
    customer_name: 'Jane Smith',
    email: 'jane@example.com',
    order_date: '2024-01-16T11:00:00',
    status: 'pending',
    total_amount: 199.99,
    products: [
      { name: 'Product 2', sku: 'SKU2', quantity: 1, price: 199.99 }
    ],
    shipping_address: {
      street: '456 Oak Ave',
      city: 'Other City',
      state: 'NY',
      zip: '54321'
    },
  },
];

describe('Orders Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders orders page with loading state', () => {
    renderOrders();
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Loading orders...')).toBeInTheDocument();
  });

  it('displays orders table when data is loaded', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Order ID')).toBeInTheDocument();
    expect(screen.getByText('Customer')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Total')).toBeInTheDocument();

    // Check order data
    expect(screen.getByText('12345')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('$299.99')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search orders...');
    await user.type(searchInput, 'John');

    // Debounce delay
    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('search=John')
      );
    }, { timeout: 1000 });
  });

  it('handles status filter', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders.filter(o => o.status === 'processed'),
        total: 1,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    const statusFilter = screen.getByRole('combobox', { name: /filter by status/i });
    await user.selectOptions(statusFilter, 'processed');

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('status=processed')
      );
    });
  });

  it('handles date range filter', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    const startDateInput = screen.getByLabelText(/start date/i);
    const endDateInput = screen.getByLabelText(/end date/i);

    await user.type(startDateInput, '2024-01-15');
    await user.type(endDateInput, '2024-01-16');

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-15')
      );
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-01-16')
      );
    });
  });

  it('handles pagination', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 50,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Check pagination info
    expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();

    // Click next page
    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('page=2')
      );
    });
  });

  it('opens order detail modal', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Click on an order
    const orderRow = screen.getByText('12345');
    fireEvent.click(orderRow);

    // Check modal content
    await waitFor(() => {
      expect(screen.getByText('Order Details')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('123 Main St')).toBeInTheDocument();
      expect(screen.getByText('Product 1')).toBeInTheDocument();
    });
  });

  it('handles status update', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    vi.mocked(api.patch).mockResolvedValue({
      data: { message: 'Status updated successfully' },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Open order details
    const orderRow = screen.getByText('12345');
    fireEvent.click(orderRow);

    await waitFor(() => {
      expect(screen.getByText('Order Details')).toBeInTheDocument();
    });

    // Update status
    const statusSelect = screen.getByLabelText(/update status/i);
    const user = userEvent.setup();
    await user.selectOptions(statusSelect, 'shipped');

    const updateButton = screen.getByRole('button', { name: /update status/i });
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(vi.mocked(api.patch)).toHaveBeenCalledWith(
        '/orders/12345/status',
        expect.objectContaining({ status: 'shipped' })
      );
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Order status updated successfully',
        })
      );
    });
  });

  it('handles resend email', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    vi.mocked(api.post).mockResolvedValue({
      data: { message: 'Email resent successfully' },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Open order details
    const orderRow = screen.getByText('12345');
    fireEvent.click(orderRow);

    await waitFor(() => {
      expect(screen.getByText('Order Details')).toBeInTheDocument();
    });

    // Click resend email
    const resendButton = screen.getByRole('button', { name: /resend email/i });
    fireEvent.click(resendButton);

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith('/orders/12345/resend');
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Order email resent successfully',
        })
      );
    });
  });

  it('handles export functionality', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    // Mock window.open
    const mockOpen = vi.fn();
    window.open = mockOpen;

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Click export CSV
    const exportButton = screen.getByRole('button', { name: /export/i });
    fireEvent.click(exportButton);

    const exportCSV = screen.getByText('Export as CSV');
    fireEvent.click(exportCSV);

    expect(mockOpen).toHaveBeenCalledWith(
      expect.stringContaining('/orders/export?format=csv'),
      '_blank'
    );
  });

  it('handles bulk actions for admin users', async () => {
    const adminContext = {
      ...mockAuthContext,
      user: { ...mockAuthContext.user, is_superuser: true },
    };

    render(
      <BrowserRouter>
        <AuthContext.Provider value={adminContext}>
          <Orders />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: mockOrders,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    // Select orders
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]); // Select all
    
    // Bulk actions should be visible
    expect(screen.getByText(/2 selected/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /bulk update/i })).toBeInTheDocument();
  });

  it('displays empty state when no orders', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        orders: [],
        total: 0,
        page: 1,
        per_page: 20,
      },
    });

    renderOrders();

    await waitFor(() => {
      expect(screen.queryByText('Loading orders...')).not.toBeInTheDocument();
    });

    expect(screen.getByText('No orders found')).toBeInTheDocument();
    expect(screen.getByText(/try adjusting your filters/i)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('API Error'));

    renderOrders();

    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Failed to load orders',
          variant: 'destructive',
        })
      );
    });
  });
});