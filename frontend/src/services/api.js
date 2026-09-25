const configuredApiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_BASE_URL = configuredApiUrl.startsWith('http')
  ? configuredApiUrl.replace(/\/$/, '')
  : `https://${configuredApiUrl.replace(/\/$/, '')}`;

async function fetchJson(url) {
  const response = await fetch(`${API_BASE_URL}${url}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

export async function getDashboardSummary() {
  return fetchJson('/api/dashboard/summary');
}

export async function getSalesTrend() {
  return fetchJson('/api/sales/trend');
}

export async function getTopProducts() {
  return fetchJson('/api/products/top');
}

export async function getCategories() {
  return fetchJson('/api/products/categories');
}

export async function getCustomerSummary() {
  return fetchJson('/api/customers/summary');
}

export async function getRFMData() {
  return fetchJson('/api/customers/rfm');
}

export async function getCustomerSegments() {
  return fetchJson('/api/customers/segments');
}

export async function getGeography() {
  return fetchJson('/api/geography');
}

export async function getPayments() {
  return fetchJson('/api/payments');
}

export async function getForecast() {
  return fetchJson('/api/forecast');
}

export async function getInsights() {
  return fetchJson('/api/insights');
}

export async function uploadCsv(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || 'Upload failed');
  }
  return payload;
}
