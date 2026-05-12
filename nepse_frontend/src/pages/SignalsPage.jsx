import React, { useEffect, useState } from 'react'
import { signalsAPI } from '../api/index'
import PageHeader from '../components/PageHeader'
import GlassCard from '../components/GlassCard'

export const SignalsPage = () => {
    const [signals, setSignals] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [filters, setFilters] = useState({
        signal_type: '',
        min_confidence: 0,
    })

    useEffect(() => {
        fetchSignals()
    }, [filters])

    const fetchSignals = async () => {
        try {
            setLoading(true)
            const params = {
                limit: 50,
                ...(filters.signal_type && { signal_type: filters.signal_type }),
                ...(filters.min_confidence > 0 && { min_confidence: filters.min_confidence }),
            }
            const response = await signalsAPI.listSignals(params)
            setSignals(response.data.results || [])
            setError(null)
        } catch (err) {
            setError('Failed to load signals')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const getSignalBadgeColor = (type) => {
        switch (type) {
            case 'BUY':
                return 'border border-emerald-400/20 bg-emerald-500/10 text-emerald-200'
            case 'SELL':
                return 'border border-rose-400/20 bg-rose-500/10 text-rose-200'
            default:
                return 'border border-cyan-400/20 bg-cyan-500/10 text-cyan-200'
        }
    }

    const getSignalEmoji = (type) => {
        switch (type) {
            case 'BUY':
                return '🟢'
            case 'SELL':
                return '🔴'
            default:
                return '🔵'
        }
    }

    if (loading) {
        return (
            <div className="flex min-h-[70vh] items-center justify-center px-6">
                <div className="panel-surface rounded-3xl px-8 py-6 text-sm text-slate-200 shadow-soft">
                    Loading signals...
                </div>
            </div>
        )
    }

    return (
        <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
            <PageHeader
                eyebrow="Technical intelligence"
                title="Trading signals"
                description="Filter the latest signal feed by type and confidence to focus on the setups that matter most."
            />

            {error && (
                <div className="mb-6 rounded-3xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-rose-100">
                    {error}
                </div>
            )}

            <div className="grid gap-6 xl:grid-cols-[0.88fr_1.12fr]">
                <GlassCard title="Filters" subtitle="Narrow the feed to high-signal opportunities" className="fade-up">
                    <div className="space-y-5">
                        <div>
                            <label className="mb-2 block text-sm font-medium text-slate-200">
                                Signal type
                            </label>
                            <select className="field-select w-full rounded-2xl px-4 py-3" value={filters.signal_type} onChange={(e) => setFilters({ ...filters, signal_type: e.target.value })}>
                                <option value="">All Types</option>
                                <option value="BUY">Buy</option>
                                <option value="SELL">Sell</option>
                                <option value="ALERT">Alert</option>
                            </select>
                        </div>
                        <div>
                            <label className="mb-2 block text-sm font-medium text-slate-200">
                                Minimum confidence: {filters.min_confidence}%
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                className="w-full accent-cyan-400"
                                value={filters.min_confidence}
                                onChange={(e) => setFilters({ ...filters, min_confidence: parseInt(e.target.value) })}
                            />
                        </div>
                    </div>
                </GlassCard>

                <GlassCard title={`Signal feed (${signals.length})`} subtitle="Latest entries from the engine" className="fade-up stagger-1">
                    {signals.length > 0 ? (
                        <div className="space-y-3">
                            {signals.map((signal) => (
                                <article key={signal.id} className="rounded-2xl border border-white/8 bg-white/5 p-4 transition hover:bg-white/8">
                                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                                        <div className="flex-1">
                                            <div className="flex flex-wrap items-center gap-3">
                                                <span className="text-2xl">{getSignalEmoji(signal.signal_type)}</span>
                                                <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getSignalBadgeColor(signal.signal_type)}`}>
                                                    {signal.signal_type}
                                                </span>
                                                <span className="text-sm text-slate-400">
                                                    {new Date(signal.created_at).toLocaleDateString()} {new Date(signal.created_at).toLocaleTimeString()}
                                                </span>
                                            </div>

                                            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                                                <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-3 py-3">
                                                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Stock</p>
                                                    <p className="mt-1 font-semibold text-white">{signal.stock_symbol}</p>
                                                </div>
                                                <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-3 py-3">
                                                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Price</p>
                                                    <p className="mt-1 font-semibold text-white">Rs {signal.stock_price}</p>
                                                </div>
                                                <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-3 py-3">
                                                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Confidence</p>
                                                    <p className="mt-1 font-semibold text-white">{signal.confidence_score}%</p>
                                                </div>
                                                <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-3 py-3">
                                                    <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Status</p>
                                                    <p className="mt-1 font-semibold text-white">
                                                        {signal.is_notified ? '✓ Notified' : '○ Pending'}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="mt-4 rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-sm text-slate-300">
                                                <strong className="text-white">Reason:</strong> {signal.reason}
                                            </div>
                                        </div>
                                    </div>
                                </article>
                            ))}
                        </div>
                    ) : (
                        <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 px-6 py-10 text-center text-slate-400">
                            <p className="text-lg font-medium text-slate-200">No signals found</p>
                            <p className="mt-2 text-sm">Try adjusting your filters.</p>
                        </div>
                    )}
                </GlassCard>
            </div>
        </div>
    )
}

export default SignalsPage
