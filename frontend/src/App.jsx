import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  getCategories,
  getCustomerSegments,
  getCustomerSummary,
  getDashboardSummary,
  getForecast,
  getGeography,
  getInsights,
  getPayments,
  getRFMData,
  getSalesTrend,
  getTopProducts,
  uploadCsv,
} from './services/api';

const NAV_ITEMS = [
  'Overview',
  'Sales',
  'Products',
  'Customers',
  'Geography',
  'Forecast',
];

const COLORS = ['#38bdf8', '#34d399', '#fbbf24', '#f472b6', '#a78bfa', '#f87171'];

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatCompactCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value || 0);
}

function StatCard({ title, value, subtext, tone = 'blue' }) {
  const toneMap = {
    blue: 'from-sky-500/20 to-sky-500/5 text-sky-300',
    emerald: 'from-emerald-500/20 to-emerald-500/5 text-emerald-300',
    violet: 'from-violet-500/20 to-violet-500/5 text-violet-300',
    amber: 'from-amber-500/20 to-amber-500/5 text-amber-300',
    rose: 'from-rose-500/20 to-rose-500/5 text-rose-300',
  };

  return (
    <div className="stat-card">
      <div className={`mb-4 inline-flex rounded-xl bg-gradient-to-br p-2 ${toneMap[tone]}`}>
        <span className="text-lg font-semibold">{title.slice(0, 1)}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      <div className="mt-2 text-xs text-slate-400">{subtext}</div>
    </div>
  );
}

export default function App() {
  const [summary, setSummary] = useState(null);
  const [salesTrend, setSalesTrend] = useState({ daily: [], monthly: [] });
  const [topProducts, setTopProducts] = useState([]);
  const [categories, setCategories] = useState({ by_revenue: [], by_quantity: [], avg_price_by_category: [] });
  const [customers, setCustomers] = useState({ summary: {}, top_customers: [] });
  const [rfm, setRfm] = useState({ segments: {}, records: [] });
  const [segments, setSegments] = useState({ clusters: [], details: [] });
  const [geography, setGeography] = useState({ by_state: [] });
  const [payments, setPayments] = useState({ payments: [] });
  const [forecast, setForecast] = useState({ monthly: [], forecast: [] });
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [uploading, setUploading] = useState(false);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError('');

      const [summaryData, trendData, productsData, categoryData, customerData, rfmData, segmentData, geographyData, paymentData, forecastData, insightsData] = await Promise.all([
        getDashboardSummary(),
        getSalesTrend(),
        getTopProducts(),
        getCategories(),
        getCustomerSummary(),
        getRFMData(),
        getCustomerSegments(),
        getGeography(),
        getPayments(),
        getForecast(),
        getInsights(),
      ]);

      setSummary(summaryData);
      setSalesTrend(trendData);
      setTopProducts(productsData.top_products || []);
      setCategories(categoryData);
      setCustomers(customerData);
      setRfm(rfmData);
      setSegments(segmentData);
      setGeography(geographyData);
      setPayments(paymentData);
      setForecast(forecastData);
      setInsights(insightsData.insights || []);
    } catch (err) {
      setError('Unable to load analytics data from the backend. Please ensure the FastAPI service is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const filteredCategoryData = useMemo(() => {
    if (!selectedCategory || selectedCategory === 'All') return categories.by_revenue || [];
    return (categories.by_revenue || []).filter((item) => item.category === selectedCategory);
  }, [categories.by_revenue, selectedCategory]);

  const rfmSegments = useMemo(() => {
    return Object.entries(rfm.segments || {}).map(([name, value]) => ({ name, value }));
  }, [rfm]);

  const paymentChart = useMemo(() => payments.payments || [], [payments]);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const result = await uploadCsv(file);
      await loadDashboardData();
      alert(`${result.message} Loaded ${result.rows_loaded} rows.`);
    } catch (err) {
      setError(err.message || 'Upload failed.');
      alert(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="card p-8 text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-sky-500 border-t-transparent" />
          Loading analytics dashboard...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
        <div className="card max-w-xl p-8 text-center text-red-300">
          <h2 className="mb-3 text-xl font-semibold text-white">Backend connection issue</h2>
          <p>{error}</p>
          <button onClick={loadDashboardData} className="mt-5 rounded-lg bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500">
            Retry loading
          </button>
        </div>
      </div>
    );
  }

  const categoriesList = ['All', ...new Set((categories.by_revenue || []).map((item) => item.category))];
  const hasData = (summary && summary.total_revenue !== undefined) || topProducts.length > 0;

  if (!hasData) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
        <div className="card max-w-xl p-8 text-center text-slate-200">
          <h2 className="text-xl font-semibold text-white">No data available</h2>
          <p className="mt-2 text-slate-400">Upload a CSV file to populate the dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-800 bg-slate-950/90 p-6 lg:w-72 lg:border-b-0 lg:border-r">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-sky-400">Analytics</p>
              <h1 className="mt-2 text-2xl font-bold text-white">PulseCart</h1>
            </div>
            <div className="rounded-xl border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-xs text-sky-300">Live</div>
          </div>

          <nav className="space-y-2">
            {NAV_ITEMS.map((item, index) => (
              <button key={item} className={`sidebar-link w-full ${index === 0 ? 'bg-slate-800 text-white' : ''}`}>
                <span className="h-2 w-2 rounded-full bg-sky-400" />
                {item}
              </button>
            ))}
          </nav>

          <div className="mt-8 card p-4">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Upload</div>
            <label className="mt-3 block cursor-pointer rounded-xl border border-dashed border-slate-600 bg-slate-900 px-3 py-5 text-center text-sm text-slate-300 hover:border-sky-400 hover:text-sky-300">
              {uploading ? 'Uploading...' : 'Import CSV'}
              <input type="file" accept=".csv" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
          </div>
        </aside>

        <main className="flex-1 p-5 lg:p-8">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Performance overview</p>
              <h2 className="text-3xl font-bold text-white">E-Commerce Sales & Customer Intelligence Dashboard</h2>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none"
              >
                {categoriesList.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
          </header>

          <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <StatCard title="Revenue" value={formatCompactCurrency(summary.total_revenue)} subtext="Total revenue" tone="blue" />
            <StatCard title="Orders" value={summary.total_orders.toLocaleString()} subtext="Completed orders" tone="emerald" />
            <StatCard title="Customers" value={summary.total_customers.toLocaleString()} subtext="Unique buyers" tone="violet" />
            <StatCard title="AOV" value={formatCurrency(summary.avg_order_value)} subtext="Average order value" tone="amber" />
            <StatCard title="Growth" value={`${summary.revenue_growth_pct.toFixed(1)}%`} subtext="Month-over-month" tone="rose" />
          </section>

          <section className="mb-6 grid gap-6 xl:grid-cols-[2fr_1fr]">
            <div className="card p-5">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Revenue trend</h3>
                <span className="text-xs text-slate-400">Daily</span>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={salesTrend.daily || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#38bdf8" strokeWidth={3} dot={{ r: 2 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Business insights</h3>
              <div className="space-y-3">
                {insights.map((insight) => (
                  <div key={insight.title} className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                    <div className="mb-1 text-xs uppercase tracking-[0.2em] text-sky-300">{insight.type}</div>
                    <div className="font-medium text-white">{insight.title}</div>
                    <p className="mt-1 text-sm text-slate-300">{insight.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mb-6 grid gap-6 xl:grid-cols-2">
            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Revenue by category</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={filteredCategoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="revenue" radius={[8, 8, 0, 0]} fill="#34d399" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Top products</h3>
              <div className="space-y-3">
                {(topProducts || []).slice(0, 6).map((item, index) => (
                  <div key={item.product_id} className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2">
                    <div>
                      <div className="text-sm font-medium text-white">#{index + 1} {item.product_name}</div>
                      <div className="text-xs text-slate-400">{item.quantity} units sold</div>
                    </div>
                    <div className="text-sm font-semibold text-sky-300">{formatCurrency(item.revenue)}</div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mb-6 grid gap-6 xl:grid-cols-2">
            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Customer segments</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={rfmSegments} dataKey="value" nameKey="name" outerRadius={90} label>
                    {rfmSegments.map((entry, index) => (
                      <Cell key={`${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value} customers`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Revenue by state</h3>
              <div className="space-y-3">
                {(geography.by_state || []).slice(0, 6).map((state) => (
                  <div key={state.state}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-slate-300">{state.state}</span>
                      <span className="text-sky-300">{formatCurrency(state.revenue)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                      <div className="h-full rounded-full bg-gradient-to-r from-sky-500 to-emerald-400" style={{ width: `${Math.min(100, (state.revenue / Math.max(...(geography.by_state || []).map((item) => item.revenue), 1)) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mb-6 grid gap-6 xl:grid-cols-2">
            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Payment methods</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={paymentChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="payment_method" tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="revenue" fill="#fbbf24" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Forecast</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={forecast.forecast || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#cbd5e1' }} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Line type="monotone" dataKey="forecast" stroke="#a78bfa" strokeWidth={3} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Top customers</h3>
              <div className="space-y-3">
                {(customers.top_customers || []).slice(0, 5).map((customer, index) => (
                  <div key={customer.customer_id} className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2">
                    <div>
                      <div className="text-sm font-medium text-white">#{index + 1} {customer.customer_id}</div>
                      <div className="text-xs text-slate-400">{customer.orders} orders</div>
                    </div>
                    <div className="text-sm font-semibold text-emerald-300">{formatCurrency(customer.revenue)}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h3 className="mb-4 text-lg font-semibold text-white">Customer retention</h3>
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">New customers</div>
                  <div className="mt-2 text-2xl font-bold text-white">{customers.summary.new_customers || 0}</div>
                </div>
                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Returning customers</div>
                  <div className="mt-2 text-2xl font-bold text-white">{customers.summary.returning_customers || 0}</div>
                </div>
                <div className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Average revenue/customer</div>
                  <div className="mt-2 text-2xl font-bold text-white">{formatCurrency(customers.summary.avg_revenue_per_customer || 0)}</div>
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
