import { AlgorandClient } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet-react'
import { useSnackbar } from 'notistack'
import { useMemo, useState } from 'react'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'

interface MintNFTProps {
  openModal: boolean
  closeModal: () => void
}

const MintNFT = ({ openModal, closeModal }: MintNFTProps) => {
  const { activeAddress, transactionSigner } = useWallet()
  const { enqueueSnackbar } = useSnackbar()
  const [name, setName] = useState('AlgoNFT')
  const [description, setDescription] = useState('My first NFT!')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  const algorand = useMemo(() => {
    const algodConfig = getAlgodConfigFromViteEnvironment()
    const client = AlgorandClient.fromConfig({ algodConfig })
    client.setDefaultSigner(transactionSigner)
    return client
  }, [transactionSigner])

  const hasPinata = !!import.meta.env.VITE_PINATA_JWT

  const onMint = async () => {
    if (!activeAddress) return enqueueSnackbar('Connect a wallet first', { variant: 'error' })
    if (!file) return enqueueSnackbar('Select an image', { variant: 'error' })

    setLoading(true)
    try {
      let assetUrl = `https://smareet.vercel.app#arc3`

      // If Pinata is configured, upload to IPFS
      if (hasPinata) {
        const { pinFileToIPFS, pinJSONToIPFS, ipfsHttpUrl } = await import('../utils/pinata')
        const filePin = await pinFileToIPFS(file)
        const imageUrl = ipfsHttpUrl(filePin.IpfsHash)
        const metadata = { name, description, image: imageUrl, image_mimetype: file.type || 'image/png' }
        const jsonPin = await pinJSONToIPFS(metadata)
        assetUrl = `${ipfsHttpUrl(jsonPin.IpfsHash)}#arc3`
      }

      enqueueSnackbar('Please check your phone to sign the transaction!', { variant: 'info', autoHideDuration: 6000 })

      // Create ASA (NFT) on-chain
      const result = await algorand.send.assetCreate({
        sender: activeAddress,
        total: 1n,
        decimals: 0,
        unitName: name.slice(0, 8).replace(/\s+/g, ''),
        assetName: name,
        manager: activeAddress,
        reserve: activeAddress,
        freeze: activeAddress,
        clawback: activeAddress,
        url: assetUrl,
        defaultFrozen: false,
      })

      enqueueSnackbar(`🎉 NFT minted! ASA ID: ${result.assetId}`, { variant: 'success', autoHideDuration: 10000 })
      closeModal()
    } catch (e) {
      const msg = (e as Error).message || ''
      if (msg.toLowerCase().includes('network mismatch') || msg.includes('4100')) {
        enqueueSnackbar('⚠️ Network Mismatch! Open Pera Wallet → Settings → Developer Settings → Node Settings → Select "Testnet"', {
          variant: 'error',
          autoHideDuration: 10000,
        })
      } else if (msg.toLowerCase().includes('overspend')) {
        enqueueSnackbar('💸 Insufficient funds! Get free Testnet ALGO from the faucet first.', {
          variant: 'error',
          autoHideDuration: 8000,
        })
      } else {
        enqueueSnackbar(msg, { variant: 'error' })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <dialog id="mint_nft_modal" className={`modal ${openModal ? 'modal-open' : ''}`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-2xl mb-4">Mint NFT (ARC-18)</h3>
        {!hasPinata && (
          <div className="alert alert-info mb-3 text-sm">
            <span>📌 IPFS not configured. NFT will be minted on-chain without image hosting.</span>
          </div>
        )}
        <div className="flex flex-col gap-3">
          <input className="input input-bordered" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="input input-bordered" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          <input className="file-input file-input-bordered" type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>
        <div className="modal-action">
          <button className={`btn btn-primary ${loading ? 'loading' : ''}`} onClick={onMint} disabled={loading}>
            {loading ? 'Check Phone...' : 'Mint'}
          </button>
          <button className="btn" onClick={closeModal} disabled={loading}>Close</button>
        </div>
      </form>
    </dialog>
  )
}

export default MintNFT


