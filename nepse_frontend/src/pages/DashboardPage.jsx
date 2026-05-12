import React, { useEffect, useMemo, useState } from 'react'
import { stocksAPI, signalsAPI } from '../api/index'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import GlassCard from '../components/GlassCard'
import MetricCard from '../components/MetricCard'

export const DashboardPage = () => {
    const [stats, setStats] = useState(null)
    const [stocks, setStocks] = useState([])
    const [signals, setSignals] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const [statsRes, stocksRes, signalsRes] = await Promise.all([
                    stocksAPI.getStatistics(),
                    stocksAPI.listStocks({ limit: 5 }),
                    signalsAPI.listSignals({ limit: 10 }),
                ])

                setStats(statsRes.data.data)
                setStocks(stocksRes.data.results || [])
                setSignals(signalsRes.data.results || [])
                setError(null)
            } catch (err) {
                setError('Failed to load dashboard data')
                console.error(err)
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [])

    const marketChartData = useMemo(() => {
        return stocks.slice(0, 8).map((stock, index) => ({
            name: stock.symbol || `S${index + 1}`,
            price: Number(stock.price || 0),
            change: Number(stock.change_percent || 0),
        }))
    }, [stocks])

    const signalTypeCounts = useMemo(() => {
        const counts = signals.reduce((accumulator, signal) => {
            const key = signal.signal_type || 'UNKNOWN'
            accumulator[key] = (accumulator[key] || 0) + 1
            return accumulator
        }, {})

        return Object.entries(counts).map(([name, value]) => ({ name, value }))
    }, [signals])

    if (loading) {
        return (
            <div className="flex min-h-[70vh] items-center justify-center px-6">
                <div className="panel-surface rounded-3xl px-8 py-6 text-sm text-slate-200 shadow-soft">
                    Loading dashboard...
                </div>
            </div>
        )
    }

    const getSignalTone = (type) => {
        switch ((type || '').toUpperCase()) {
            case 'BUY':
                return 'emerald'
            case 'SELL':
                return 'rose'
            default:
                return 'cyan'
        }
    }

    const signalToneClasses = {
        emerald: 'bg-emerald-500/15 text-emerald-200 ring-emerald-400/20',
        rose: 'bg-rose-500/15 text-rose-200 ring-rose-400/20',
        cyan: 'bg-cyan-500/15 text-cyan-200 ring-cyan-400/20',
        amber: 'bg-amber-500/15 text-amber-200 ring-amber-400/20',
    }

    return (
        <div className="mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <PageHeader
                eyebrow="Market control center"
                title="Trade smarter with a single glance"
                description="Track market breadth, recent signals, and stock performance from one focused dashboard built for fast decisions."
            />

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {error && (
                    <div className="md:col-span-2 xl:col-span-4 rounded-3xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-rose-100">
                        {error}
                    </div>
                )}

                <MetricCard label="Total Stocks" value={stats?.total_stocks ?? '—'} helper="Active listings across the market" tone="cyan" />
                <MetricCard label="Gainers" value={stats?.gainers ?? '—'} helper="Momentum leaders today" tone="emerald" />
                <MetricCard label="Losers" value={stats?.losers ?? '—'} helper="Names under pressure" tone="rose" />
                <MetricCard
                    label="Avg Change"
                    value={typeof stats?.average_change_percent === 'number' ? `${stats.average_change_percent.toFixed(2)}%` : '—'}
                    helper="Breadth across the board"
                    tone={stats?.average_change_percent >= 0 ? 'emerald' : 'amber'}
                    delta={stats?.average_change_percent >= 0 ? 'Positive' : 'Negative'}
                />
            </div>

            <div className="mt-8 grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
                <GlassCard
                    title="Market pulse"
                    subtitle="A compact view of the most active stocks"
                    className="fade-up"
                >
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={marketChartData}>
                                <defs>
                                    <linearGradient id="marketFill" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.35} />
                                        <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                                <XAxis dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(15, 23, 42, 0.96)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '16px',
                                        color: '#fff',
                                    }}
                                />
                                <Area type="monotone" dataKey="price" stroke="#22d3ee" fill="url(#marketFill)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>

                <GlassCard title="Signal mix" subtitle="Recent notifications by type" className="fade-up stagger-1">
                    <div className="h-56">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={signalTypeCounts}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" vertical={false} />
                                <XAxis dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} allowDecimals={false} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(15, 23, 42, 0.96)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '16px',
                                        color: '#fff',
                                    }}
                                />
                                <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#60a5fa" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </GlassCard>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
                <GlassCard title="Top stocks" subtitle="Highest ranked names in the current feed" className="fade-up stagger-2">
                    <div className="space-y-3">
                        {stocks.length > 0 ? (
                            stocks.map((stock) => (
                                <div key={stock.id} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-4 transition hover:bg-white/8">
                                    <div>
                                        <p className="font-semibold text-white">{stock.symbol}</p>
                                        <p className="text-sm text-slate-400">{stock.name}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-semibold text-white">Rs {stock.price}</p>
                                        <p className={`text-sm ${Number(stock.change_percent) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                                            {Number(stock.change_percent) > 0 ? '+' : ''}{stock.change_percent}%
                                        </p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 px-4 py-8 text-center text-slate-400">
                                No stocks available yet.
                            </div>
                        )}
                    </div>
                </GlassCard>

                <GlassCard title="Recent signals" subtitle="Latest high-confidence entries" className="fade-up stagger-3">
                    <div className="max-h-[32rem] space-y-3 overflow-y-auto pr-1">
                        {signals.length > 0 ? (
                            signals.map((signal) => {
                                const tone = getSignalTone(signal.signal_type)
                                return (
                                    <article key={signal.id} className="rounded-2xl border border-white/8 bg-white/5 p-4 transition hover:bg-white/8">
                                        <div className="flex items-start justify-between gap-4">
                                            <div>
                                                <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${signalToneClasses[tone] || signalToneClasses.cyan}`}>
                                                    {signal.signal_type}
                                                </span>
                                                <p className="mt-3 text-base font-semibold text-white">{signal.stock_symbol}</p>
                                                <p className="mt-1 text-sm text-slate-400">
                                                    {signal.reason || 'Signal generated from technical conditions.'}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-2xl font-semibold text-cyan-300">{signal.confidence_score}%</p>
                                                <p className="mt-1 text-xs uppercase tracking-[0.24em] text-slate-500">Confidence</p>
                                            </div>
                                        </div>
                                    </article>
                                )
                            })
                        ) : (
                            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 px-4 py-8 text-center text-slate-400">
                                No signals yet.
                            </div>
                        )}
                    </div>
                </GlassCard>
            </div>
        </div>
    )
}

export default DashboardPage
