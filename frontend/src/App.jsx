import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Spinner from './components/Spinner'

const Home = lazy(() => import('./pages/Home'))
const PostList = lazy(() => import('./pages/PostList'))
const PostDetail = lazy(() => import('./pages/PostDetail'))
const Categories = lazy(() => import('./pages/Categories'))
const CategoryDetail = lazy(() => import('./pages/CategoryDetail'))
const About = lazy(() => import('./pages/About'))
const Contact = lazy(() => import('./pages/Contact'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const PostEditor = lazy(() => import('./pages/PostEditor'))

function NotFound() {
  return (
    <main style={{ padding: '5rem 2rem', textAlign: 'center' }}>
      <h1 style={{ color: 'var(--accent)' }}>404</h1>
      <p style={{ color: 'var(--text-muted)' }}>Page not found.</p>
    </main>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Routes>
          {/* Editor is full-screen — no navbar/footer */}
          <Route path="/editor/:slug" element={
            <ProtectedRoute>
              <Suspense fallback={<Spinner />}>
                <PostEditor />
              </Suspense>
            </ProtectedRoute>
          } />

          {/* All other routes get the shell */}
          <Route path="*" element={
            <div>
              <Navbar />
              <div id="main-content" tabIndex="-1">
                <Suspense fallback={<Spinner />}>
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/posts" element={<PostList />} />
                    <Route path="/posts/:slug" element={<PostDetail />} />
                    <Route path="/categories" element={<Categories />} />
                    <Route path="/categories/:slug" element={<CategoryDetail />} />
                    <Route path="/about" element={<About />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/dashboard" element={
                      <ProtectedRoute><Dashboard /></ProtectedRoute>
                    } />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Suspense>
              </div>
              <Footer />
            </div>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
