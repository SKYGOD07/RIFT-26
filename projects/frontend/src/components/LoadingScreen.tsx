import { motion, AnimatePresence } from 'framer-motion'
import { useState, useRef, useEffect } from 'react'

interface LoadingScreenProps {
    onComplete: () => void
}

const LoadingScreen = ({ onComplete }: LoadingScreenProps) => {
    const [isVisible, setIsVisible] = useState(true)
    const videoRef = useRef<HTMLVideoElement>(null)

    useEffect(() => {
        // Fallback timeout in case video fails to load or play
        const fallback = setTimeout(() => {
            setIsVisible(false)
            setTimeout(onComplete, 800)
        }, 8000)

        return () => clearTimeout(fallback)
    }, [onComplete])

    const handleVideoEnd = () => {
        // Small delay before fade out
        setTimeout(() => {
            setIsVisible(false)
            setTimeout(onComplete, 800)
        }, 300)
    }

    const handleVideoError = () => {
        setIsVisible(false)
        setTimeout(onComplete, 400)
    }

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    className="loading-screen"
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.8, ease: 'easeInOut' }}
                >
                    <video
                        ref={videoRef}
                        className="loading-video"
                        autoPlay
                        muted
                        playsInline
                        onEnded={handleVideoEnd}
                        onError={handleVideoError}
                    >
                        <source src="/ticket-intro.mp4" type="video/mp4" />
                    </video>

                    {/* Subtle loading indicator at bottom */}
                    <motion.div
                        className="loading-indicator"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1, duration: 0.5 }}
                    >
                        <div className="loading-dots">
                            {[0, 1, 2].map((i) => (
                                <motion.span
                                    key={i}
                                    className="loading-dot"
                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                                />
                            ))}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}

export default LoadingScreen
