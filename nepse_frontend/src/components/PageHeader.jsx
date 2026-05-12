import React from 'react'

export const PageHeader = ({ eyebrow, title, description, action }) => {
    return (
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
                {eyebrow && (
                    <p className="mb-3 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-300/90">
                        {eyebrow}
                    </p>
                )}
                <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                    {title}
                </h1>
                {description && (
                    <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
                        {description}
                    </p>
                )}
            </div>
            {action && <div className="shrink-0">{action}</div>}
        </div>
    )
}

export default PageHeader
