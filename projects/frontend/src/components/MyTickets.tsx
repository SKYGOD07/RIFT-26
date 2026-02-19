import { useEffect, useState } from 'react'
import { Ticket, ApiService } from '../services/api'
import { useWallet } from '@txnlab/use-wallet-react'

interface MyTicketsProps {
    openModal: boolean
    closeModal: () => void
}

const MyTickets = ({ openModal, closeModal }: MyTicketsProps) => {
    const { activeAddress } = useWallet()
    const [tickets, setTickets] = useState<Ticket[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (openModal && activeAddress) {
            fetchTickets()
        }
    }, [openModal, activeAddress])

    const fetchTickets = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await ApiService.getTickets(activeAddress ?? undefined)
            setTickets(data)
        } catch (err: any) {
            console.error(err)
            setError('Failed to fetch tickets. Is the backend running?')
        } finally {
            setLoading(false)
        }
    }

    return (
        <dialog className={`modal ${openModal ? 'modal-open' : ''}`}>
            <div className="modal-box w-11/12 max-w-5xl">
                <h3 className="font-bold text-lg mb-4">My Tickets</h3>

                {loading && <div className="flex justify-center p-8"><span className="loading loading-spinner loading-lg"></span></div>}

                {error && (
                    <div className="alert alert-error mb-4">
                        <span>{error}</span>
                        <button className="btn btn-sm btn-ghost" onClick={fetchTickets}>Retry</button>
                    </div>
                )}

                {!loading && !error && tickets.length === 0 && (
                    <div className="text-center p-8 opacity-60">
                        <p className="text-xl">No tickets found.</p>
                        <p className="text-sm">Mint one to get started!</p>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tickets.map((ticket) => (
                        <div key={ticket.id} className="card bg-base-200 shadow-xl">
                            <figure className="h-48 bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                                <span className="text-6xl">🎟️</span>
                            </figure>
                            <div className="card-body">
                                <h2 className="card-title">Event #{ticket.event_id}</h2>
                                <div className="badge badge-secondary">{ticket.status}</div>
                                <p className="text-sm opacity-70">Seat: <span className="font-mono font-bold">{ticket.seat_number}</span></p>
                                <p className="text-xs break-all opacity-50 mt-2">ASA ID: {ticket.asa_id}</p>
                                <div className="card-actions justify-end mt-4">
                                    <a
                                        href={`https://testnet.explorer.perawallet.app/asset/${ticket.asa_id}/`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="btn btn-sm btn-outline"
                                    >
                                        View on Explorer
                                    </a>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="modal-action">
                    <button className="btn" onClick={closeModal}>Close</button>
                </div>
            </div>
            <form method="dialog" className="modal-backdrop">
                <button onClick={closeModal}>close</button>
            </form>
        </dialog>
    )
}

export default MyTickets
