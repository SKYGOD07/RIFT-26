import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const ThemeToggle = () => {
    // Initialize from document or local storage, default to 'dark'
    const [theme, setTheme] = useState(
        document.documentElement.getAttribute('data-theme') || 'dark'
    )

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem('theme', theme)
    }, [theme])

    const toggleTheme = () => {
        setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
    }

    return (
        <button
            onClick={toggleTheme}
            className="theme-toggle-btn"
            aria-label="Toggle Theme"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
            <div className="toggle-track">
                <motion.div
                    className="toggle-thumb"
                    layout
                    transition={{ type: "spring", stiffness: 700, damping: 30 }}
                    style={{
                        x: theme === 'dark' ? 2 : 26,
                        backgroundColor: theme === 'dark' ? '#00d4ff' : '#fbbf24'
                    }}
                >
                    {theme === 'dark' ? (
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3 text-black">
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3 text-white">
                            <circle cx="12" cy="12" r="5"></circle>
                            <line x1="12" y1="1" x2="12" y2="3"></line>
                            <line x1="12" y1="21" x2="12" y2="23"></line>
                            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                            <line x1="1" y1="12" x2="3" y2="12"></line>
                            <line x1="21" y1="12" x2="23" y2="12"></line>
                            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                        </svg>
                    )}
                </motion.div>
            </div>
        </button>
    )
}

export default ThemeToggle
