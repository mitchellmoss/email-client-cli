import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../src/pages/Dashboard';
import { AuthContext } from '../src/contexts/AuthContext';
import * as api from '../src/api/client';

// Mock the API client
vi.mock('../src/api/client');

// Mock recharts to avoid render issues in tests
vi.mock('recharts', () => ({
  LineChart: vi.fn(() => null),
  Line: vi.fn(() => null),
  XAxis: vi.fn(() => null),
  YAxis: vi.fn(() => null),
  CartesianGrid: vi.fn(() => null),
  Tooltip: vi.fn(() => null),
  ResponsiveContainer: vi.fn(({ children }: any) => <div>{children}</div>),
}));

const mockAuthContext = {
  user: { id: 1, email: 'test@example.com', username: 'testuser' },
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
};

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>
        <Dashboard />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with loading state', () => {
    renderDashboard();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Loading dashboard data...')).toBeInTheDocument();
  });

  it('displays statistics when data is loaded', async () => {
    const mockStats = {
      total_orders: 150,
      orders_today: 12,
      orders_this_week: 45,
      orders_this_month: 120,
      success_rate: 95.5,
      pending_orders: 5,
      failed_orders: 3,
      total_revenue: 45678.90,
    };

    const mockRecentOrders = [
      {
        order_id: '12345',
        customer_name: 'John Doe',
        order_date: '2024-01-15T10:00:00',
        status: 'processed',
        total_amount: 299.99,
      },
      {
        order_id: '12346',
        customer_name: 'Jane Smith',
        order_date: '2024-01-15T11:00:00',
        status: 'pending',
        total_amount: 199.99,
      },
    ];

    const mockChartData = [
      { date: '2024-01-10', orders: 10, revenue: 2999.90 },
      { date: '2024-01-11', orders: 15, revenue: 4499.85 },
      { date: '2024-01-12', orders: 12, revenue: 3599.88 },
    ];

    vi.mocked(api.get).mockImplementation((url) => {
      if (url === '/analytics/dashboard') {
        return Promise.resolve({
          data: {
            stats: mockStats,
            recent_orders: mockRecentOrders,
            chart_data: mockChartData,
          },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard data...')).not.toBeInTheDocument();
    });

    // Check statistics cards
    expect(screen.getByText('Total Orders')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    
    expect(screen.getByText('Orders Today')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
    expect(screen.getByText('95.5%')).toBeInTheDocument();
    
    expect(screen.getByText('Total Revenue')).toBeInTheDocument();
    expect(screen.getByText('$45,678.90')).toBeInTheDocument();

    // Check recent orders
    expect(screen.getByText('Recent Orders')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.getByText('$299.99')).toBeInTheDocument();
    expect(screen.getByText('$199.99')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('API Error'));

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard data/i)).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh button is clicked', async () => {
    const mockStats = {
      total_orders: 150,
      orders_today: 12,
      orders_this_week: 45,
      orders_this_month: 120,
      success_rate: 95.5,
      pending_orders: 5,
      failed_orders: 3,
      total_revenue: 45678.90,
    };

    vi.mocked(api.get).mockResolvedValue({
      data: {
        stats: mockStats,
        recent_orders: [],
        chart_data: [],
      },
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard data...')).not.toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(2);
  });

  it('displays correct status badges for orders', async () => {
    const mockOrders = [
      {
        order_id: '1',
        customer_name: 'Test User 1',
        order_date: '2024-01-15T10:00:00',
        status: 'processed',
        total_amount: 100,
      },
      {
        order_id: '2',
        customer_name: 'Test User 2',
        order_date: '2024-01-15T11:00:00',
        status: 'pending',
        total_amount: 200,
      },
      {
        order_id: '3',
        customer_name: 'Test User 3',
        order_date: '2024-01-15T12:00:00',
        status: 'failed',
        total_amount: 300,
      },
    ];

    vi.mocked(api.get).mockResolvedValue({
      data: {
        stats: {},
        recent_orders: mockOrders,
        chart_data: [],
      },
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('processed')).toHaveClass('bg-green-100');
      expect(screen.getByText('pending')).toHaveClass('bg-yellow-100');
      expect(screen.getByText('failed')).toHaveClass('bg-red-100');
    });
  });

  it('navigates to orders page when view all orders is clicked', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        stats: {},
        recent_orders: [],
        chart_data: [],
      },
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.queryByText('Loading dashboard data...')).not.toBeInTheDocument();
    });

    const viewAllLink = screen.getByText('View all orders →');
    expect(viewAllLink).toHaveAttribute('href', '/orders');
  });

  it('formats dates correctly', async () => {
    const mockOrders = [
      {
        order_id: '1',
        customer_name: 'Test User',
        order_date: '2024-01-15T10:30:45',
        status: 'processed',
        total_amount: 100,
      },
    ];

    vi.mocked(api.get).mockResolvedValue({
      data: {
        stats: {},
        recent_orders: mockOrders,
        chart_data: [],
      },
    });

    renderDashboard();

    await waitFor(() => {
      // Check if date is formatted (exact format may vary based on locale)
      expect(screen.getByText(/Jan.*15.*2024/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no recent orders', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        stats: {},
        recent_orders: [],
        chart_data: [],
      },
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('No recent orders')).toBeInTheDocument();
    });
  });

  it('handles real-time updates', async () => {
    const initialStats = {
      total_orders: 150,
      orders_today: 12,
    };

    const updatedStats = {
      total_orders: 151,
      orders_today: 13,
    };

    vi.mocked(api.get)
      .mockResolvedValueOnce({
        data: {
          stats: initialStats,
          recent_orders: [],
          chart_data: [],
        },
      })
      .mockResolvedValueOnce({
        data: {
          stats: updatedStats,
          recent_orders: [],
          chart_data: [],
        },
      });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
    });

    // Simulate auto-refresh (in real app this would be on a timer)
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(screen.getByText('151')).toBeInTheDocument();
      expect(screen.getByText('13')).toBeInTheDocument();
    });
  });
});