import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const RegisterPage = () => {
    const navigate = useNavigate()
    const { register, loading, error } = useAuth()
    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        passwordConfirm: '',
        firstName: '',
        lastName: '',
    })
    const [formError, setFormError] = useState('')

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (formData.password !== formData.passwordConfirm) {
            setFormError('Passwords do not match')
            return
        }

        try {
            await register(
                formData.email,
                formData.username,
                formData.password,
                formData.firstName,
                formData.lastName
            )
            navigate('/login', { state: { message: 'Registration successful! Please login.' } })
        } catch (err) {
            setFormError(error || 'Registration failed')
        }
    }

    return (
        <div className="auth-grid min-h-[calc(100vh-5rem)] px-4 py-10 sm:px-6 lg:px-8">
            <div className="mx-auto grid min-h-[calc(100vh-7rem)] max-w-6xl gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
                <section className="fade-up space-y-6 text-white lg:order-2">
                    <div className="inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-200">
                        Build your trading workspace
                    </div>
                    <div>
                        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">A sharper place to follow NEPSE moves.</h1>
                        <p className="mt-4 max-w-xl text-lg leading-8 text-slate-300">
                            Create an account to build watchlists, subscribe to alerts, and get structured signal updates.
                        </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                        {['Fast onboarding', 'Secure token login', 'Watchlist + signals'].map((item) => (
                            <div key={item} className="panel-surface rounded-2xl px-4 py-4 text-sm text-slate-200">
                                {item}
                            </div>
                        ))}
                    </div>
                </section>

                <section className="fade-up stagger-1 auth-panel rounded-[2rem] p-6 shadow-soft sm:p-8 lg:order-1">
                    <div className="mb-6">
                        <h2 className="text-2xl font-semibold text-white">Create your account</h2>
                        <p className="mt-2 text-sm text-slate-400">Fill in the details below to get started.</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {(formError || error) && (
                            <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                                {formError || error}
                            </div>
                        )}

                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <div>
                                <label htmlFor="firstName" className="mb-2 block text-sm font-medium text-slate-200">First Name</label>
                                <input
                                    id="firstName"
                                    name="firstName"
                                    type="text"
                                    className="field-input w-full rounded-2xl px-4 py-3"
                                    value={formData.firstName}
                                    onChange={handleChange}
                                />
                            </div>
                            <div>
                                <label htmlFor="lastName" className="mb-2 block text-sm font-medium text-slate-200">Last Name</label>
                                <input
                                    id="lastName"
                                    name="lastName"
                                    type="text"
                                    className="field-input w-full rounded-2xl px-4 py-3"
                                    value={formData.lastName}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

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
                            <label htmlFor="username" className="mb-2 block text-sm font-medium text-slate-200">Username</label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="field-input w-full rounded-2xl px-4 py-3"
                                value={formData.username}
                                onChange={handleChange}
                                placeholder="username"
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

                        <div>
                            <label htmlFor="passwordConfirm" className="mb-2 block text-sm font-medium text-slate-200">Confirm Password</label>
                            <input
                                id="passwordConfirm"
                                name="passwordConfirm"
                                type="password"
                                required
                                className="field-input w-full rounded-2xl px-4 py-3"
                                value={formData.passwordConfirm}
                                onChange={handleChange}
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-2xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/20 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? 'Creating account...' : 'Sign up'}
                        </button>

                        <p className="text-center text-sm text-slate-400">
                            Already have an account?{' '}
                            <Link to="/login" className="font-semibold text-emerald-300 hover:text-emerald-200">
                                Login
                            </Link>
                        </p>
                    </form>
                </section>
            </div>
        </div>
    )
}

export default RegisterPage
