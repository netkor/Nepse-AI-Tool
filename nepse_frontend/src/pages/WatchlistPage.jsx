import React, { useEffect, useState } from 'react'
import { alertsAPI, stocksAPI } from '../api/index'
import PageHeader from '../components/PageHeader'
import GlassCard from '../components/GlassCard'

export const WatchlistPage = () => {
    const [watchlist, setWatchlist] = useState(null)
    const [stocks, setStocks] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')

    useEffect(() => {
        fetchWatchlist()
    }, [])

    const fetchWatchlist = async () => {
        try {
            setLoading(true)
            const [watchlistRes, stocksRes] = await Promise.all([
                alertsAPI.getWatchlist(),
                stocksAPI.listStocks({ limit: 100 }),
            ])
            setWatchlist(watchlistRes.data.data)
            setStocks(stocksRes.data.results || [])
            setError(null)
        } catch (err) {
            setError('Failed to load watchlist')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleAddStock = async (stockId) => {
        try {
            await alertsAPI.addToWatchlist(stockId)
            await fetchWatchlist()
        } catch (err) {
            setError('Failed to add stock to watchlist')
        }
    }

    const handleRemoveStock = async (stockId) => {
        try {
            await alertsAPI.removeFromWatchlist(stockId)
            await fetchWatchlist()
        } catch (err) {
            setError('Failed to remove stock from watchlist')
        }
    }

    const filteredStocks = stocks.filter(
        (stock) =>
            stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            stock.name.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const watchlistStockIds = watchlist?.stocks?.map((stock) => stock.stock) || []

    if (loading) {
        return (
            <div className="flex min-h-[70vh] items-center justify-center px-6">
                <div className="panel-surface rounded-3xl px-8 py-6 text-sm text-slate-200 shadow-soft">
                    Loading watchlist...
                </div>
            </div>
        )
    }

    return (
        <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
            <PageHeader
                eyebrow="Portfolio tracking"
                title="My watchlist"
                description="Add and remove stocks from a clean, responsive market watchlist."
            />

            {error && (
                <div className="mb-6 rounded-3xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-rose-100">
                    {error}
                </div>
            )}

            <div className="grid gap-6 lg:grid-cols-[1.18fr_0.82fr]">
                <GlassCard
                    title={`Tracked stocks (${watchlist?.stock_count || 0})`}
                    subtitle="Symbols you are actively monitoring"
                    className="fade-up"
                >
                    {watchlist?.stocks && watchlist.stocks.length > 0 ? (
                        <div className="space-y-3">
                            {watchlist.stocks.map((item) => (
                                <div
                                    key={item.id}
                                    className="flex flex-col gap-4 rounded-2xl border border-white/8 bg-white/5 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                                >
                                    <div>
                                        <p className="text-lg font-semibold text-white">{item.symbol}</p>
                                        <p className="text-sm text-slate-400">{item.name}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-semibold text-white">Rs {item.price}</p>
                                        <p className={`text-sm ${item.change_percent >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                                            {item.change_percent > 0 ? '+' : ''}{item.change_percent}%
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleRemoveStock(item.id)}
                                        className="rounded-full border border-rose-400/20 bg-rose-500/10 px-4 py-2 text-sm font-semibold text-rose-100 transition hover:bg-rose-500/20"
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 px-6 py-10 text-center text-slate-400">
                            <p className="text-base font-medium text-slate-200">No stocks in your watchlist yet</p>
                            <p className="mt-2 text-sm">Add stocks from the list below.</p>
                        </div>
                    )}
                </GlassCard>

                <GlassCard
                    title="Add stocks"
                    subtitle="Search the market and add names to your list"
                    className="fade-up stagger-1 sticky top-24 h-fit"
                >
                    <input
                        type="text"
                        placeholder="Search stocks..."
                        className="field-input mb-4 w-full rounded-2xl px-4 py-3"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />

                    <div className="max-h-[34rem] space-y-2 overflow-y-auto pr-1">
                        {filteredStocks.map((stock) => (
                            <div key={stock.id} className="flex items-center justify-between gap-3 rounded-2xl border border-white/8 bg-white/5 px-3 py-3">
                                <div className="min-w-0 flex-1">
                                    <p className="font-semibold text-white">{stock.symbol}</p>
                                    <p className="truncate text-xs text-slate-400">{stock.name}</p>
                                </div>
                                <button
                                    onClick={() => handleAddStock(stock.id)}
                                    disabled={watchlistStockIds.includes(stock.id)}
                                    className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-3 py-2 text-xs font-semibold text-slate-950 shadow-lg shadow-cyan-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {watchlistStockIds.includes(stock.id) ? 'Added' : 'Add'}
                                </button>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </div>
        </div>
    )
}

export default WatchlistPage
