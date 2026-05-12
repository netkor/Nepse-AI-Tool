import React from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const Navigation = () => {
    const { user, logout } = useAuth()
    const navigate = useNavigate()

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <nav className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
                <div className="flex items-center gap-4">
                    <Link to="/" className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 text-sm font-black text-slate-950 shadow-lg shadow-cyan-500/20">
                            N
                        </div>
                        <div>
                            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300">NEPSE AI</p>
                            <p className="text-xs text-slate-400">Signals • Watchlist • Intelligence</p>
                        </div>
                    </Link>

                    {user && (
                        <div className="hidden lg:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1">
                            {['/dashboard', '/watchlist', '/signals'].map((path) => (
                                <NavLink
                                    key={path}
                                    to={path}
                                    className={({ isActive }) =>
                                        `rounded-full px-4 py-2 text-sm font-medium transition ${isActive
                                            ? 'bg-white text-slate-950 shadow-soft'
                                            : 'text-slate-300 hover:bg-white/8 hover:text-white'
                                        }`
                                    }
                                >
                                    {path.replace('/', '')}
                                </NavLink>
                            ))}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-3">
                    {user ? (
                        <>
                            <div className="hidden sm:flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
                                <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                                <span>Welcome, {user.first_name || user.email}</span>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <div className="flex items-center gap-2">
                            <Link
                                to="/login"
                                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
                            >
                                Login
                            </Link>
                            <Link
                                to="/register"
                                className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:scale-[1.01]"
                            >
                                Sign Up
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    )
}

export default Navigation
