import { algo, AlgorandClient } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet-react'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import { handleTxnError } from '../utils/handleTxnError'

interface TransactInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
}

const Transact = ({ openModal, setModalState }: TransactInterface) => {
  const [loading, setLoading] = useState<boolean>(false)
  const [receiverAddress, setReceiverAddress] = useState<string>('')

  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algorand = AlgorandClient.fromConfig({ algodConfig })

  const { enqueueSnackbar } = useSnackbar()

  const { transactionSigner, activeAddress } = useWallet()

  const handleSubmitAlgo = async () => {
    setLoading(true)

    if (!transactionSigner || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    try {
      enqueueSnackbar('Please check your phone to sign the transaction!', { variant: 'info', autoHideDuration: 6000 })
      const result = await algorand.send.payment({
        signer: transactionSigner,
        sender: activeAddress,
        receiver: receiverAddress,
        amount: algo(1),
      })
      enqueueSnackbar(`✅ Transaction sent: ${result.txIds[0]}`, { variant: 'success' })
      setReceiverAddress('')
    } catch (e) {
      handleTxnError(e, enqueueSnackbar)
    }

    setLoading(false)
  }

  return (
    <dialog id="transact_modal" className={`modal ${openModal ? 'modal-open' : ''}`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Send payment transaction</h3>
        <p className="text-sm opacity-60 mt-1">Send 1 ALGO to any Algorand address.</p>
        <br />
        <input
          type="text"
          data-test-id="receiver-address"
          placeholder="Paste receiver wallet address (58 characters)"
          className="input input-bordered w-full"
          value={receiverAddress}
          onChange={(e) => {
            setReceiverAddress(e.target.value)
          }}
        />
        <p className="text-xs opacity-40 mt-1">Address must be exactly 58 characters (e.g. F2FO26EDZ...)</p>
        <div className="modal-action ">
          <button className="btn" onClick={() => setModalState(!openModal)}>
            Close
          </button>
          <button
            data-test-id="send-algo"
            className={`btn ${receiverAddress.length === 58 ? 'btn-primary' : 'btn-disabled'}`}
            onClick={handleSubmitAlgo}
          >
            {loading ? <span className="loading loading-spinner" /> : 'Send 1 Algo'}
          </button>
        </div>
      </form>
    </dialog>
  )
}

export default Transact
