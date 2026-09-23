import axios from 'axios'

const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

const client = axios.create({ baseURL: BASE })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh')
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE}/auth/token/refresh/`, { refresh })
          localStorage.setItem('access', data.access)
          if (data.refresh) localStorage.setItem('refresh', data.refresh)
          original.headers.Authorization = `Bearer ${data.access}`
          return client(original)
        } catch {
          localStorage.removeItem('access')
          localStorage.removeItem('refresh')
        }
      }
    }
    return Promise.reject(err)
  }
)

export const blogApi = {
  getPosts: (params) => client.get('/blog/posts/', { params }),
  getPost: (slug) => client.get(`/blog/posts/${slug}/`),
  getFeatured: () => client.get('/blog/posts/featured/'),
  getCategories: () => client.get('/blog/categories/'),
  createCategory: (data) => client.post('/blog/categories/', data),
  getCategory: (slug) => client.get(`/blog/categories/${slug}/`),
  getTags: () => client.get('/blog/tags/'),
  search: (q) => client.get('/blog/search/', { params: { q } }),
  getStats: () => client.get('/blog/stats/'),
  addComment: (slug, data) => client.post(`/blog/posts/${slug}/comments/`, data),
  subscribe: (data) => client.post('/blog/newsletter/', data),
  confirmSubscription: (token) => client.post('/blog/newsletter/confirm/', { token }),
  unsubscribe: (token) => client.post('/blog/newsletter/unsubscribe/', { token }),
  sendContactMessage: (data) => client.post('/blog/contact/', data),
  // editor
  myPosts: () => client.get('/blog/posts/mine/'),
  createPost: (data) => client.post('/blog/posts/create/', data),
  updatePost: (slug, data) => client.patch(`/blog/posts/${slug}/edit/`, data),
  deletePost: (slug) => client.delete(`/blog/posts/${slug}/edit/`),
  getPostForEdit: (slug) => client.get(`/blog/posts/${slug}/edit/`),
}

export const authApi = {
  login: (data) => client.post('/auth/login/', data),
  me: () => client.get('/auth/me/'),
}

export default client
