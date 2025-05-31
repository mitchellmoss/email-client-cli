import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import ProductMatching from '../src/pages/ProductMatching';
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

const renderProductMatching = () => {
  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>
        <ProductMatching />
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

const mockMappings = [
  {
    id: 1,
    original_name: 'TileWare Original Product',
    mapped_name: 'TileWare Mapped Product',
    mapped_sku: 'TW-001',
    product_type: 'tileware',
    confidence_score: 0.95,
    created_at: '2024-01-15T10:00:00',
    updated_at: '2024-01-15T10:00:00',
  },
  {
    id: 2,
    original_name: 'Laticrete Original Product',
    mapped_name: 'Laticrete Mapped Product',
    mapped_sku: 'LAT-001',
    product_type: 'laticrete',
    confidence_score: 0.87,
    created_at: '2024-01-14T09:00:00',
    updated_at: '2024-01-14T09:00:00',
  },
];

const mockUnmappedProducts = [
  {
    product_name: 'Unknown Product 1',
    occurrences: 5,
    last_seen: '2024-01-15T12:00:00',
    example_order_id: '12345',
  },
  {
    product_name: 'Unknown Product 2',
    occurrences: 3,
    last_seen: '2024-01-14T15:00:00',
    example_order_id: '12344',
  },
];

describe('ProductMatching Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders product matching page with tabs', () => {
    renderProductMatching();
    expect(screen.getByText('Product Matching')).toBeInTheDocument();
    expect(screen.getByText('Manage product name mappings for order processing')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /existing mappings/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /unmapped products/i })).toBeInTheDocument();
  });

  it('displays existing mappings', async () => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url.includes('/products/mappings')) {
        return Promise.resolve({
          data: {
            mappings: mockMappings,
            total: 2,
            page: 1,
            per_page: 20,
          },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderProductMatching();

    await waitFor(() => {
      expect(screen.getByText('TileWare Original Product')).toBeInTheDocument();
      expect(screen.getByText('TW-001')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
    });
  });

  it('handles search functionality', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: mockMappings,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    renderProductMatching();

    await waitFor(() => {
      expect(screen.getByText('TileWare Original Product')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search mappings/i);
    await user.type(searchInput, 'tileware');

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('search=tileware')
      );
    });
  });

  it('handles product type filter', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: mockMappings.filter(m => m.product_type === 'tileware'),
        total: 1,
        page: 1,
        per_page: 20,
      },
    });

    renderProductMatching();

    await waitFor(() => {
      expect(screen.getByText('TileWare Original Product')).toBeInTheDocument();
    });

    const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
    await user.selectOptions(typeFilter, 'tileware');

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        expect.stringContaining('product_type=tileware')
      );
    });
  });

  it('opens add mapping dialog', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: [],
        total: 0,
        page: 1,
        per_page: 20,
      },
    });

    renderProductMatching();

    const addButton = screen.getByRole('button', { name: /add mapping/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Add Product Mapping')).toBeInTheDocument();
      expect(screen.getByLabelText(/original product name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/mapped product name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/sku/i)).toBeInTheDocument();
    });
  });

  it('creates new mapping', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: [],
        total: 0,
        page: 1,
        per_page: 20,
      },
    });

    vi.mocked(api.post).mockResolvedValue({
      data: {
        id: 3,
        original_name: 'New Product',
        mapped_name: 'Mapped New Product',
        mapped_sku: 'NEW-001',
        product_type: 'tileware',
        confidence_score: 1.0,
      },
    });

    renderProductMatching();

    // Open dialog
    const addButton = screen.getByRole('button', { name: /add mapping/i });
    fireEvent.click(addButton);

    // Fill form
    await user.type(screen.getByLabelText(/original product name/i), 'New Product');
    await user.type(screen.getByLabelText(/mapped product name/i), 'Mapped New Product');
    await user.type(screen.getByLabelText(/sku/i), 'NEW-001');
    await user.selectOptions(screen.getByLabelText(/product type/i), 'tileware');

    // Submit
    const saveButton = screen.getByRole('button', { name: /save mapping/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/products/mappings',
        expect.objectContaining({
          original_name: 'New Product',
          mapped_name: 'Mapped New Product',
          mapped_sku: 'NEW-001',
          product_type: 'tileware',
        })
      );
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Product mapping created successfully',
        })
      );
    });
  });

  it('edits existing mapping', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: mockMappings,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    vi.mocked(api.put).mockResolvedValue({
      data: {
        ...mockMappings[0],
        mapped_name: 'Updated Mapped Product',
      },
    });

    renderProductMatching();

    await waitFor(() => {
      expect(screen.getByText('TileWare Original Product')).toBeInTheDocument();
    });

    // Click edit button
    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    fireEvent.click(editButtons[0]);

    // Update form
    const mappedNameInput = screen.getByLabelText(/mapped product name/i);
    await user.clear(mappedNameInput);
    await user.type(mappedNameInput, 'Updated Mapped Product');

    // Save
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(vi.mocked(api.put)).toHaveBeenCalledWith(
        '/products/mappings/1',
        expect.objectContaining({
          mapped_name: 'Updated Mapped Product',
        })
      );
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Product mapping updated successfully',
        })
      );
    });
  });

  it('deletes mapping (admin only)', async () => {
    const adminContext = {
      ...mockAuthContext,
      user: { ...mockAuthContext.user, is_superuser: true },
    };

    render(
      <BrowserRouter>
        <AuthContext.Provider value={adminContext}>
          <ProductMatching />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    vi.mocked(api.get).mockResolvedValue({
      data: {
        mappings: mockMappings,
        total: 2,
        page: 1,
        per_page: 20,
      },
    });

    vi.mocked(api.delete).mockResolvedValue({
      data: { message: 'Mapping deleted successfully' },
    });

    await waitFor(() => {
      expect(screen.getByText('TileWare Original Product')).toBeInTheDocument();
    });

    // Click delete button
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(vi.mocked(api.delete)).toHaveBeenCalledWith('/products/mappings/1');
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Product mapping deleted successfully',
        })
      );
    });
  });

  it('displays unmapped products tab', async () => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url.includes('/products/mappings')) {
        return Promise.resolve({
          data: { mappings: [], total: 0, page: 1, per_page: 20 },
        });
      }
      if (url.includes('/products/unmapped')) {
        return Promise.resolve({
          data: { unmapped_products: mockUnmappedProducts },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderProductMatching();

    // Switch to unmapped products tab
    const unmappedTab = screen.getByRole('tab', { name: /unmapped products/i });
    fireEvent.click(unmappedTab);

    await waitFor(() => {
      expect(screen.getByText('Unknown Product 1')).toBeInTheDocument();
      expect(screen.getByText('5 occurrences')).toBeInTheDocument();
    });
  });

  it('suggests mapping for unmapped product', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockImplementation((url) => {
      if (url.includes('/products/unmapped')) {
        return Promise.resolve({
          data: { unmapped_products: mockUnmappedProducts },
        });
      }
      return Promise.resolve({ data: { mappings: [], total: 0 } });
    });

    vi.mocked(api.post).mockImplementation((url) => {
      if (url.includes('/products/suggest-mapping')) {
        return Promise.resolve({
          data: {
            suggestions: [
              {
                mapped_name: 'Suggested Product Name',
                mapped_sku: 'SUGG-001',
                confidence: 0.92,
                reason: 'Name similarity match',
              },
            ],
          },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderProductMatching();

    // Switch to unmapped products tab
    const unmappedTab = screen.getByRole('tab', { name: /unmapped products/i });
    fireEvent.click(unmappedTab);

    await waitFor(() => {
      expect(screen.getByText('Unknown Product 1')).toBeInTheDocument();
    });

    // Click suggest mapping
    const suggestButtons = screen.getAllByRole('button', { name: /suggest mapping/i });
    fireEvent.click(suggestButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Mapping Suggestions')).toBeInTheDocument();
      expect(screen.getByText('Suggested Product Name')).toBeInTheDocument();
      expect(screen.getByText('SUGG-001')).toBeInTheDocument();
      expect(screen.getByText('92% confidence')).toBeInTheDocument();
    });
  });

  it('imports mappings from CSV', async () => {
    const adminContext = {
      ...mockAuthContext,
      user: { ...mockAuthContext.user, is_superuser: true },
    };

    render(
      <BrowserRouter>
        <AuthContext.Provider value={adminContext}>
          <ProductMatching />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    vi.mocked(api.get).mockResolvedValue({
      data: { mappings: [], total: 0, page: 1, per_page: 20 },
    });

    const file = new File(
      ['original_name,mapped_name,mapped_sku,product_type\nTest,Test Mapped,TEST-001,tileware'],
      'mappings.csv',
      { type: 'text/csv' }
    );

    renderProductMatching();

    const importButton = screen.getByRole('button', { name: /import csv/i });
    fireEvent.click(importButton);

    const fileInput = screen.getByLabelText(/choose file/i);
    const user = userEvent.setup();
    await user.upload(fileInput, file);

    vi.mocked(api.post).mockResolvedValue({
      data: { imported: 1, message: 'Import successful' },
    });

    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/products/mappings/import',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      );
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Success',
          description: 'Import successful',
        })
      );
    });
  });

  it('validates SKU format', async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.get).mockResolvedValue({
      data: { mappings: [], total: 0, page: 1, per_page: 20 },
    });

    vi.mocked(api.post).mockImplementation((url) => {
      if (url.includes('/products/validate-sku')) {
        return Promise.resolve({
          data: { valid: false, message: 'Invalid SKU format' },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderProductMatching();

    // Open add dialog
    const addButton = screen.getByRole('button', { name: /add mapping/i });
    fireEvent.click(addButton);

    // Enter invalid SKU
    const skuInput = screen.getByLabelText(/sku/i);
    await user.type(skuInput, 'invalid sku!');
    
    // Tab out to trigger validation
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/invalid sku format/i)).toBeInTheDocument();
    });
  });

  it('displays mapping statistics', async () => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url.includes('/products/stats')) {
        return Promise.resolve({
          data: {
            total_mappings: 150,
            mappings_by_type: { tileware: 95, laticrete: 55 },
            average_confidence: 0.87,
            low_confidence_count: 12,
            unmapped_products: 8,
          },
        });
      }
      if (url.includes('/products/mappings')) {
        return Promise.resolve({
          data: { mappings: mockMappings, total: 2, page: 1, per_page: 20 },
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    renderProductMatching();

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('Total Mappings')).toBeInTheDocument();
      expect(screen.getByText('87%')).toBeInTheDocument();
      expect(screen.getByText('Avg. Confidence')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Unmapped Products')).toBeInTheDocument();
    });
  });
});