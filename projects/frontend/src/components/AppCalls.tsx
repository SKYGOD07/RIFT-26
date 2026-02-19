import { useWallet } from '@txnlab/use-wallet-react'
import { useSnackbar } from 'notistack'
import { useEffect, useState } from 'react'
import { CounterClient } from '../contracts/Counter'
import { getAlgodConfigFromViteEnvironment, getIndexerConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'
import { AlgorandClient } from '@algorandfoundation/algokit-utils'
import { handleTxnError } from '../utils/handleTxnError'

interface AppCallsInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
}

const AppCalls = ({ openModal, setModalState }: AppCallsInterface) => {
  const [loading, setLoading] = useState<boolean>(false)
  // Fixed deployed application ID so users don't need to deploy repeatedly
  const FIXED_APP_ID = 747652603
  const [appId, setAppId] = useState<number | null>(FIXED_APP_ID)
  const [currentCount, setCurrentCount] = useState<number>(0)
  const { enqueueSnackbar } = useSnackbar()
  const { activeAccount, activeAddress, transactionSigner: TransactionSigner } = useWallet()

  const algodConfig = getAlgodConfigFromViteEnvironment()
  const indexerConfig = getIndexerConfigFromViteEnvironment()
  const algorand = AlgorandClient.fromConfig({
    algodConfig,
    indexerConfig,
  })


  algorand.setDefaultSigner(TransactionSigner)

  // Separate function to fetch current count
  const fetchCount = async (appId: number): Promise<number> => {
    try {
      const counterClient = new CounterClient({
        appId: BigInt(appId),
        algorand,
        defaultSigner: TransactionSigner,
      })
      const state = await counterClient.appClient.getGlobalState()
      return typeof state.count.value === 'bigint'
        ? Number(state.count.value)
        : parseInt(state.count.value, 10)
    } catch (e) {
      enqueueSnackbar(`Error fetching count: ${(e as Error).message}`, { variant: 'error' })
      return 0
    }
  }

  // Deploy function kept for future use; commented out per request
  // const [deploying, setDeploying] = useState<boolean>(false)
  // const deployContract = async () => {
  //   setDeploying(true)
  //   try {
  //     const factory = new CounterFactory({
  //       defaultSender: activeAddress ?? undefined,
  //       algorand,
  //     })
  //     // Deploy multiple addresses with the same contract
  //     const deployResult = await factory.send.create.bare()
  //     // If you want idempotent deploy from one address
  //     // const deployResult = await factory.deploy({
  //     //   onSchemaBreak: OnSchemaBreak.AppendApp,
  //     //   onUpdate: OnUpdate.AppendApp,
  //     // })
  //     const deployedAppId = Number(deployResult.appClient.appId)
  //     setAppId(deployedAppId)
  //     const count = await fetchCount(deployedAppId)
  //     setCurrentCount(count)
  //     enqueueSnackbar(`Contract deployed with App ID: ${deployedAppId}. Initial count: ${count}`, { variant: 'success' })
  //   } catch (e) {
  //     enqueueSnackbar(`Error deploying contract: ${(e as Error).message}`, { variant: 'error' })
  //   } finally {
  //     setDeploying(false)
  //   }
  // }

  // Auto-load current count for the fixed app ID (only when wallet is connected)
  useEffect(() => {
    const load = async () => {
      if (appId && activeAddress) {
        const count = await fetchCount(appId)
        setCurrentCount(count)
      }
    }
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appId, TransactionSigner, activeAddress])

  const incrementCounter = async () => {
    if (!appId) {
      enqueueSnackbar('Missing App ID', { variant: 'error' })
      return
    }

    setLoading(true)
    try {
      const counterClient = new CounterClient({
        appId: BigInt(appId),
        algorand,
        defaultSigner: TransactionSigner,
      })

      enqueueSnackbar('Please check your phone to sign the transaction!', { variant: 'info', autoHideDuration: 6000 })

      // Increment the counter
      await counterClient.send.incrCounter({ args: [], sender: activeAddress ?? undefined })

      // Fetch and set updated count
      const count = await fetchCount(appId)
      setCurrentCount(count)

      enqueueSnackbar(`✅ Counter incremented! New count: ${count}`, {
        variant: 'success'
      })
    } catch (e) {
      handleTxnError(e, enqueueSnackbar)
    } finally {
      setLoading(false)
    }
  }

  return (
    <dialog id="appcalls_modal" className={`modal ${openModal ? 'modal-open' : ''}`}>
      <form method="dialog" className="modal-box">
        <h3 className="font-bold text-lg">Counter Contract</h3>
        <p className="text-sm opacity-60 mt-1">Interact with the on-chain counter smart contract (App ID: {appId}).</p>
        <br />

        <div className="flex flex-col gap-4">
          {appId && (
            <div className="alert alert-info flex flex-col gap-1">
              <span>Current App ID: {appId}</span>
              <span>Current Count: {currentCount}</span>
            </div>
          )}

          <div className="flex flex-col gap-2">
            <button
              className={`btn btn-secondary ${loading ? 'loading' : ''}`}
              onClick={incrementCounter}
              disabled={loading || !appId}
            >
              {loading ? 'Check Phone...' : 'Increment Counter'}
            </button>
            <p className="text-sm opacity-50">Each click adds 1 to the on-chain counter.</p>
          </div>

          <div className="modal-action">
            <button
              className="btn"
              onClick={() => setModalState(false)}
              disabled={loading}
            >
              Close
            </button>
          </div>
        </div>
      </form>
    </dialog>
  )
}

export default AppCalls