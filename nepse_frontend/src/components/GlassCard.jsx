import React from 'react'

export const GlassCard = ({ title, subtitle, children, action, className = '' }) => {
    return (
        <section className={`glass-card rounded-3xl border border-white/10 bg-slate-950/50 shadow-soft ${className}`}>
            {(title || subtitle || action) && (
                <header className="flex items-start justify-between gap-4 border-b border-white/8 px-5 py-4 sm:px-6">
                    <div>
                        {title && <h2 className="text-lg font-semibold text-white">{title}</h2>}
                        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
                    </div>
                    {action}
                </header>
            )}
            <div className="px-5 py-5 sm:px-6">{children}</div>
        </section>
    )
}

export default GlassCard
