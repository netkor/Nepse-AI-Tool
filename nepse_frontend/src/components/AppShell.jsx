import React from 'react'

export const AppShell = ({ children }) => {
    return (
        <div className="app-shell relative min-h-screen overflow-hidden text-slate-100">
            <div className="app-shell__glow app-shell__glow--one" />
            <div className="app-shell__glow app-shell__glow--two" />
            <div className="app-shell__grid" />
            <div className="relative z-10">{children}</div>
        </div>
    )
}

export default AppShell
