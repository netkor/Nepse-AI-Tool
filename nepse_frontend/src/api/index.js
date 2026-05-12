import client from './axios'

// Auth APIs
export const authAPI = {
  register: (email, username, password, firstName, lastName) =>
    client.post('/auth/register/', {
      email,
      username,
      password,
      password2: password,
      first_name: firstName,
      last_name: lastName,
    }),
  
  login: (email, password) =>
    client.post('/auth/login/', { username: email, password }),
  
  refreshToken: (refreshToken) =>
    client.post('/auth/refresh/', { refresh: refreshToken }),
  
  getProfile: () =>
    client.get('/auth/profile/'),
  
  updateProfile: (data) =>
    client.patch('/auth/profile/', data),
  
  changePassword: (oldPassword, newPassword) =>
    client.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password2: newPassword,
    }),
}

// Stocks APIs
export const stocksAPI = {
  listStocks: (params) =>
    client.get('/stocks/', { params }),
  
  getStock: (id) =>
    client.get(`/stocks/${id}/`),
  
  getStockHistory: (symbol, days = 90) =>
    client.get(`/stocks/${symbol}/history/`, { params: { days } }),
  
  getStatistics: () =>
    client.get('/stocks/statistics/overview/'),
}

// Signals APIs
export const signalsAPI = {
  listSignals: (params) =>
    client.get('/signals/', { params }),
  
  getSignal: (id) =>
    client.get(`/signals/${id}/`),
  
  getSignalsByStock: (symbol) =>
    client.get(`/signals/stock/${symbol}/`),
  
  markNotified: (signalId) =>
    client.post(`/signals/${signalId}/mark-notified/`),
}

// Alerts APIs (Watchlist)
export const alertsAPI = {
  // Watchlist
  getWatchlist: () =>
    client.get('/alerts/watchlist/'),
  
  addToWatchlist: (stockId) =>
    client.post('/alerts/watchlist/', { stock_id: stockId }),
  
  removeFromWatchlist: (stockId) =>
    client.delete(`/alerts/watchlist/${stockId}/`),
  
  // Price Alerts
  listPriceAlerts: (status) =>
    client.get('/alerts/price/', { params: { status } }),
  
  createPriceAlert: (stockId, minPrice, maxPrice) =>
    client.post('/alerts/price/', {
      stock_id: stockId,
      min_price: minPrice,
      max_price: maxPrice,
    }),
  
  updatePriceAlert: (alertId, data) =>
    client.patch(`/alerts/price/${alertId}/`, data),
  
  deletePriceAlert: (alertId) =>
    client.delete(`/alerts/price/${alertId}/`),
}

export default client
