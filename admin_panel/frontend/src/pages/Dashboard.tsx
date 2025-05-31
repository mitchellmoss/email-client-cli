import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Loader2, Package, ShoppingCart, AlertCircle, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['orderStats'],
    queryFn: () => api.get('/orders/stats').then(res => res.data)
  });

  const { data: systemStatus } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => api.get('/system/status').then(res => res.data),
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-700">
          Monitor your email order processing system
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShoppingCart className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Orders (7d)
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.total_orders_sent || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {systemStatus?.is_running ? (
                  <CheckCircle className="h-6 w-6 text-green-400" />
                ) : (
                  <AlertCircle className="h-6 w-6 text-red-400" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    System Status
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStatus?.is_running ? 'Running' : 'Stopped'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Package className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Duplicates Blocked
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.duplicate_attempts_blocked || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AlertCircle className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Last Check
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {systemStatus?.last_check ? 
                      new Date(systemStatus.last_check).toLocaleTimeString() : 
                      'Never'
                    }
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Order Chart */}
      {stats?.daily_counts && stats.daily_counts.length > 0 && (
        <div className="mt-8 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Orders by Day
            </h3>
            <div className="mt-5">
              <div className="flex flex-col">
                {stats.daily_counts.map((day: any) => (
                  <div key={day.date} className="flex items-center py-2">
                    <div className="w-32 text-sm text-gray-500">
                      {new Date(day.date).toLocaleDateString()}
                    </div>
                    <div className="flex-1 ml-4">
                      <div className="bg-blue-200 h-6 rounded" 
                           style={{ width: `${(day.count / Math.max(...stats.daily_counts.map((d: any) => d.count))) * 100}%` }}>
                        <span className="text-xs text-gray-700 ml-2">{day.count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Logs Preview */}
      {systemStatus?.last_logs && systemStatus.last_logs.length > 0 && (
        <div className="mt-8 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Recent Logs
            </h3>
            <div className="bg-gray-50 rounded p-4 overflow-x-auto">
              <pre className="text-xs text-gray-600">
                {systemStatus.last_logs.slice(-5).join('')}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}