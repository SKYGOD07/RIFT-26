import { useWallet } from '@txnlab/use-wallet-react'
import React, { useState, useEffect, useCallback, useRef } from 'react'
import { motion, useScroll, useTransform, useInView } from 'framer-motion'
import ConnectWallet from './components/ConnectWallet'
import AppCalls from './components/AppCalls'
import SendAlgo from './components/SendAlgo'
import MintNFT from './components/MintNFT'
import CreateASA from './components/CreateASA'
import AssetOptIn from './components/AssetOptIn'
import Bank from './components/Bank'
import LoadingScreen from './components/LoadingScreen'
import ThemeToggle from './components/ThemeToggle'

interface HomeProps { }

const TOTAL_FRAMES = 240

// Feature data
const features = [
  {
    icon: '⚡',
    title: 'Send Algo',
    desc: 'Instantly send payment transactions to any Algorand address on the network with near-zero fees and 3-second finality.',
    key: 'sendAlgo',
  },
  {
    icon: '🎨',
    title: 'Mint NFT (ARC-18)',
    desc: 'Seamlessly upload your assets to IPFS via Pinata and mint standard ARC-18 NFTs directly from the interface.',
    key: 'mintNft',
  },
  {
    icon: '🪙',
    title: 'Create Token (ASA)',
    desc: 'Launch your own fungible Algorand Standard Asset (ASA) with custom supply, decimals, and metadata in seconds.',
    key: 'createAsa',
  },
  {
    icon: '🔗',
    title: 'Asset Opt-In',
    desc: 'Manage your asset portfolio by opting in to receive new tokens. A crucial step for Algorand DeFi participation.',
    key: 'assetOptIn',
  },
  {
    icon: '🔢',
    title: 'Counter Contract',
    desc: 'Interact with a live, shared on-chain counter smart contract (App ID 747652603) to understand state management.',
    key: 'appCalls',
  },
  {
    icon: '🏦',
    title: 'Decentralized Bank',
    desc: 'Deposit and withdraw ALGOs from a secure, non-custodial bank smart contract. Track your transaction history on-chain.',
    key: 'bank',
  },
]

// Preload all frames
const frameImages: string[] = []
for (let i = 1; i <= TOTAL_FRAMES; i++) {
  frameImages.push(`/frames/${String(i).padStart(4, '0')}.jpg`)
}

// Particles background
const Particles = () => (
  <div className="bg-particles">
    {Array.from({ length: 25 }).map((_, i) => (
      <div
        key={i}
        className="particle"
        style={{
          left: `${Math.random() * 100}%`,
          animationDuration: `${8 + Math.random() * 12}s`,
          animationDelay: `${Math.random() * 8}s`,
          width: `${1 + Math.random() * 2}px`,
          height: `${1 + Math.random() * 2}px`,
          opacity: 0.15 + Math.random() * 0.3,
        }}
      />
    ))}
  </div>
)

// Scroll-driven frame animation — optimized for 60fps
const FRAME_STEP = 2 // Use every 2nd frame → 96 frames total
const SAMPLED_COUNT = Math.ceil(TOTAL_FRAMES / FRAME_STEP)

const ScrollFrameAnimation = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const bitmapsRef = useRef<(ImageBitmap | null)[]>([])
  const lastFrameRef = useRef(-1)
  const rafRef = useRef(0)
  const readyRef = useRef(false)

  const { scrollYProgress } = useScroll()

  // Preload as ImageBitmaps (GPU-accelerated)
  useEffect(() => {
    let cancelled = false
    const bitmaps: (ImageBitmap | null)[] = new Array(SAMPLED_COUNT).fill(null)
    let loaded = 0

    for (let i = 0; i < SAMPLED_COUNT; i++) {
      const frameIdx = i * FRAME_STEP + 1
      const src = `/frames/${String(frameIdx).padStart(4, '0')}.png`
      fetch(src)
        .then(r => r.blob())
        .then(blob => createImageBitmap(blob))
        .then(bmp => {
          if (cancelled) return
          bitmaps[i] = bmp
          loaded++
          if (loaded === SAMPLED_COUNT) {
            bitmapsRef.current = bitmaps
            readyRef.current = true
            // Draw first frame immediately
            drawIndex(0)
          }
        })
        .catch(() => {
          loaded++
          if (loaded === SAMPLED_COUNT) {
            bitmapsRef.current = bitmaps
            readyRef.current = true
          }
        })
    }

    return () => { cancelled = true }
  }, [])

  // Cover-fit draw
  const drawIndex = useCallback((idx: number) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const bmp = bitmapsRef.current[idx]
    if (!bmp) return

    const cw = canvas.width
    const ch = canvas.height
    const scale = Math.max(cw / bmp.width, ch / bmp.height)
    const sw = bmp.width * scale
    const sh = bmp.height * scale
    ctx.drawImage(bmp, (cw - sw) / 2, (ch - sh) / 2, sw, sh)
  }, [])

  // Canvas resize (DPR-aware but capped for perf)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = window.innerWidth * dpr
      canvas.height = window.innerHeight * dpr
      canvas.style.width = '100%'
      canvas.style.height = '100%'
      // Redraw current frame after resize
      if (readyRef.current && lastFrameRef.current >= 0) {
        drawIndex(lastFrameRef.current)
      }
    }
    resize()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [drawIndex])

  // Scroll → frame (rAF-throttled, deduplicated)
  useEffect(() => {
    const unsubscribe = scrollYProgress.on('change', (v) => {
      if (!readyRef.current) return
      const idx = Math.min(Math.floor(v * SAMPLED_COUNT), SAMPLED_COUNT - 1)
      if (idx === lastFrameRef.current) return // Skip — same frame
      lastFrameRef.current = idx

      cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(() => drawIndex(idx))
    })

    return () => {
      unsubscribe()
      cancelAnimationFrame(rafRef.current)
    }
  }, [scrollYProgress, drawIndex])

  return (
    <div className="scroll-animation-container">
      <canvas
        ref={canvasRef}
        className="scroll-animation-canvas"
      />
    </div>
  )
}

// Feature Row with alternating layout + neon glow
const FeatureRow = ({ feature, index, openModal, activeAddress }: {
  feature: typeof features[0]
  index: number
  openModal: (key: string) => void
  activeAddress: string | null | undefined
}) => {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: false, amount: 0.15 })
  const isEven = index % 2 === 0

  const textVariants = {
    hidden: { opacity: 0, x: isEven ? -80 : 80 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.7, ease: 'easeOut' as const } },
  }

  const iconVariants = {
    hidden: { opacity: 0, scale: 0.5 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' as const, delay: 0.2 } },
  }

  return (
    <div
      className={`feature-row ${isEven ? 'row-normal' : 'row-reversed'}`}
      ref={ref}
    >
      <div className="feature-container">
        {/* TEXT SIDE */}
        <motion.div
          className="feature-text-content"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={textVariants}
        >
          <motion.div
            className="feature-icon-badge"
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            variants={iconVariants}
          >
            {feature.icon}
          </motion.div>

          <h2 className="feature-title neon-text">{feature.title}</h2>

          <p className="feature-desc">{feature.desc}</p>

          <button
            className="card-btn"
            disabled={!activeAddress}
            onClick={() => openModal(feature.key)}
          >
            {activeAddress ? 'Launch App' : 'Connect Wallet to Launch'}
          </button>
        </motion.div>

        {/* EXPLANATION SIDE */}
        <motion.div
          className="feature-explanation"
          initial={{ opacity: 0, x: isEven ? 80 : -80 }}
          animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: isEven ? 80 : -80 }}
          transition={{ duration: 0.7, ease: 'easeOut' as const, delay: 0.3 }}
        >
          <div className="explanation-card">
            <div className="explanation-number">{String(index + 1).padStart(2, '0')}</div>
            <h3 className="explanation-heading">How it works</h3>
            <p className="explanation-text">{feature.desc}</p>
            <div className="explanation-divider" />
            <div className="explanation-footer">
              <span className="explanation-tag">Algorand Blockchain</span>
              <span className="explanation-tag">Secure</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

const Home: React.FC<HomeProps> = () => {
  const [openWalletModal, setOpenWalletModal] = useState(false)
  const [appCallsDemoModal, setAppCallsDemoModal] = useState(false)
  const [sendAlgoModal, setSendAlgoModal] = useState(false)
  const [mintNftModal, setMintNftModal] = useState(false)
  const [createAsaModal, setCreateAsaModal] = useState(false)
  const [assetOptInModal, setAssetOptInModal] = useState(false)
  const [bankModal, setBankModal] = useState(false)
  const [showLoading, setShowLoading] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [navScrolled, setNavScrolled] = useState(false)
  const { activeAddress } = useWallet()

  // Play on every mount
  useEffect(() => {
    setShowLoading(true)
  }, [])

  const handleLoadingComplete = useCallback(() => {
    setShowLoading(false)
  }, [])

  // Navbar scroll effect
  useEffect(() => {
    const handleScroll = () => setNavScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Hero parallax
  const { scrollY } = useScroll()
  const heroOpacity = useTransform(scrollY, [0, 400], [1, 0])

  const toggleWalletModal = () => setOpenWalletModal(!openWalletModal)

  const openFeatureModal = (key: string) => {
    switch (key) {
      case 'sendAlgo': setSendAlgoModal(true); break
      case 'mintNft': setMintNftModal(true); break
      case 'createAsa': setCreateAsaModal(true); break
      case 'assetOptIn': setAssetOptInModal(true); break
      case 'appCalls': setAppCallsDemoModal(true); break
      case 'bank': setBankModal(true); break
    }
  }

  const scrollToFeatures = () => {
    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
    setMobileMenuOpen(false)
  }

  return (
    <>
      {showLoading && <LoadingScreen onComplete={handleLoadingComplete} />}

      {/* FIXED BACKGROUND ANIMATION (z-index: 0) */}
      <ScrollFrameAnimation />

      <div className="content-wrapper">
        <Particles />
        <nav className={`navbar ${navScrolled ? 'scrolled' : ''}`}>
          <div className="navbar-brand">SMAREET</div>
          <ul className="nav-links">
            <li><a href="#hero" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Home</a></li>
            <li><a href="#features" onClick={scrollToFeatures}>Features</a></li>
            <li><ThemeToggle /></li>
            <li>
              <button className="nav-cta" onClick={toggleWalletModal} data-test-id="connect-wallet">
                {activeAddress ? `${activeAddress.slice(0, 4)}...${activeAddress.slice(-4)}` : 'Connect Wallet'}
              </button>
            </li>
          </ul>
          <div className="flex items-center gap-4 md:hidden z-[201]">
            <ThemeToggle />
            <button
              className={`hamburger ${mobileMenuOpen ? 'active' : ''}`}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Menu"
            >
              <span /><span /><span />
            </button>
          </div>
        </nav>

        {/* Mobile Menu */}
        <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <a href="#hero" onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); setMobileMenuOpen(false) }}>Home</a>
          <a href="#features" onClick={() => { scrollToFeatures(); setMobileMenuOpen(false) }}>Features</a>
          <button onClick={() => { toggleWalletModal(); setMobileMenuOpen(false) }}>
            {activeAddress ? 'Wallet Connected' : 'Connect Wallet'}
          </button>
        </div>

        {/* HERO */}
        <section className="hero" id="hero">
          <div className="hero-gradient" />
          <motion.div className="hero-content" style={{ opacity: heroOpacity }}>
            <motion.div className="hero-badge" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.6 }}>
              Powered by Algorand
            </motion.div>
            <motion.h1 className="hero-title" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.7 }}>
              <span>SMAREET</span>
            </motion.h1>
            <motion.p className="hero-subtitle" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7, duration: 0.6 }}>
              The next-generation smart ticketing platform built on the Algorand blockchain. Secure. Transparent. Decentralized.
            </motion.p>
            <motion.div className="hero-actions" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9, duration: 0.6 }}>
              <button className="btn-primary-glow" onClick={scrollToFeatures}>Explore Features</button>
              <button className="btn-secondary-outline" onClick={toggleWalletModal}>
                {activeAddress ? 'Wallet Connected' : 'Connect Wallet'}
              </button>
            </motion.div>
          </motion.div>
          <motion.div className="hero-scroll-indicator" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 0.8 }}>
            <motion.div className="scroll-line" animate={{ scaleY: [1, 0.5, 1] }} transition={{ duration: 2, repeat: Infinity }} />
          </motion.div>
        </section>

        {/* FEATURES */}
        <section className="features-section" id="features">
          {features.map((feature, index) => (
            <FeatureRow
              key={feature.key}
              feature={feature}
              index={index}
              openModal={openFeatureModal}
              activeAddress={activeAddress}
            />
          ))}
        </section>

        {/* FOOTER */}
        <footer className="footer">
          <p>Built on <a href="https://algorand.com" target="_blank" rel="noopener noreferrer">Algorand</a> &bull; SMAREET &copy; 2026</p>
        </footer>
      </div>

      {/* Modals */}
      <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
      <AppCalls openModal={appCallsDemoModal} setModalState={setAppCallsDemoModal} />
      <SendAlgo openModal={sendAlgoModal} closeModal={() => setSendAlgoModal(false)} />
      <MintNFT openModal={mintNftModal} closeModal={() => setMintNftModal(false)} />
      <CreateASA openModal={createAsaModal} closeModal={() => setCreateAsaModal(false)} />
      <AssetOptIn openModal={assetOptInModal} closeModal={() => setAssetOptInModal(false)} />
      <Bank openModal={bankModal} closeModal={() => setBankModal(false)} />
    </>
  )
}

export default Home
