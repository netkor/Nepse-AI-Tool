import React from 'react'

const toneClasses = {
    cyan: 'from-cyan-500/20 to-sky-500/10 border-cyan-400/20 text-cyan-100',
    emerald: 'from-emerald-500/20 to-teal-500/10 border-emerald-400/20 text-emerald-100',
    rose: 'from-rose-500/20 to-pink-500/10 border-rose-400/20 text-rose-100',
    amber: 'from-amber-500/20 to-orange-500/10 border-amber-400/20 text-amber-100',
}

export const MetricCard = ({ label, value, helper, tone = 'cyan', delta }) => {
    return (
        <div className={`glass-card rounded-3xl border bg-gradient-to-br p-5 shadow-soft ${toneClasses[tone] || toneClasses.cyan}`}>
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-300">{label}</p>
                    <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{value}</p>
                    {helper && <p className="mt-2 text-sm text-slate-300">{helper}</p>}
                </div>
                {delta && (
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold text-white/90">
                        {delta}
                    </span>
                )}
            </div>
        </div>
    )
}

export default MetricCard
