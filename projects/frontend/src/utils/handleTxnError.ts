import { OptionsObject, SnackbarKey, SnackbarMessage } from 'notistack'

type EnqueueFn = (message: SnackbarMessage, options?: OptionsObject) => SnackbarKey

/**
 * Shared transaction error handler for all blockchain components.
 * Detects network-mismatch, overspend, and other common errors,
 * then shows a user-friendly snackbar message.
 */
export function handleTxnError(e: unknown, enqueueSnackbar: EnqueueFn): void {
    const msg = (e as Error).message || String(e)
    const lower = msg.toLowerCase()

    if (lower.includes('network mismatch') || msg.includes('4100')) {
        enqueueSnackbar(
            '⚠️ Network Mismatch! Open Pera Wallet → Settings → Developer Settings → Node Settings → Select "Testnet"',
            { variant: 'error', autoHideDuration: 10000 },
        )
    } else if (lower.includes('overspend')) {
        enqueueSnackbar(
            '💸 Insufficient funds! Get free Testnet ALGO from the Lora faucet first.',
            { variant: 'error', autoHideDuration: 8000 },
        )
    } else if (lower.includes('below min')) {
        enqueueSnackbar(
            '⚠️ Cannot send — your balance would fall below the minimum (0.1 ALGO). Fund your wallet first.',
            { variant: 'error', autoHideDuration: 8000 },
        )
    } else if (lower.includes('rejected') || lower.includes('cancelled') || lower.includes('canceled')) {
        enqueueSnackbar('Transaction cancelled by user.', { variant: 'warning' })
    } else {
        enqueueSnackbar(msg.length > 200 ? msg.slice(0, 200) + '…' : msg, { variant: 'error' })
    }
}
