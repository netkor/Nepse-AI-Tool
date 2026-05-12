import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const LoginPage = () => {
    const navigate = useNavigate()
    const location = useLocation()
    const { login, loading, error } = useAuth()
    const [formData, setFormData] = useState({ email: '', password: '' })
    const [formError, setFormError] = useState('')
    const [successMessage, setSuccessMessage] = useState(location.state?.message || '')

    useEffect(() => {
        if (!location.state?.message) {
            return
        }

        const timer = window.setTimeout(() => setSuccessMessage(''), 4000)
        return () => window.clearTimeout(timer)
    }, [location.state?.message])

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await login(formData.email, formData.password)
            navigate('/dashboard')
        } catch (err) {
            setFormError(error || 'Login failed')
        }
    }

    return (
        <div className="auth-grid min-h-[calc(100vh-5rem)] px-4 py-10 sm:px-6 lg:px-8">
            <div className="mx-auto grid min-h-[calc(100vh-7rem)] max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
                <section className="fade-up space-y-6 text-white">
                    <div className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">
                        NEPSE AI trading terminal
                    </div>
                    <div>
                        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Signal intelligence, not noise.</h1>
                        <p className="mt-4 max-w-xl text-lg leading-8 text-slate-300">
                            Sign in to monitor live signals, watchlists, and performance from one focused workspace.
                        </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-3">
                        {['Real-time alerts', 'Curated watchlists', 'Analytics-ready'].map((item) => (
                            <div key={item} className="panel-surface rounded-2xl px-4 py-4 text-sm text-slate-200">
                                {item}
                            </div>
                        ))}
                    </div>
                </section>

                <section className="fade-up stagger-1 auth-panel rounded-[2rem] p-6 shadow-soft sm:p-8">
                    <div className="mb-6">
                        <h2 className="text-2xl font-semibold text-white">Welcome back</h2>
                        <p className="mt-2 text-sm text-slate-400">Log in to continue to your dashboard.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {(formError || error) && (
                            <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                                {formError || error}
                            </div>
                        )}
                        {successMessage && (
                            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                                {successMessage}
                            </div>
                        )}

                        <div>
                            <label htmlFor="email" className="mb-2 block text-sm font-medium text-slate-200">Email</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                className="field-input w-full rounded-2xl px-4 py-3"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="your@email.com"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="mb-2 block text-sm font-medium text-slate-200">Password</label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="field-input w-full rounded-2xl px-4 py-3"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? 'Signing in...' : 'Login'}
                        </button>

                        <p className="text-center text-sm text-slate-400">
                            Don&apos;t have an account?{' '}
                            <Link to="/register" className="font-semibold text-cyan-300 hover:text-cyan-200">
                                Sign up
                            </Link>
                        </p>
                    </form>
                </section>
            </div>
        </div>
    )
}

export default LoginPage
