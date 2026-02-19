import axios from 'axios'

// Configure base URL (default to localhost for development)
// In production, this should point to the deployed backend URL
const API_BASE_URL = 'http://localhost:8000/api'

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

export interface Ticket {
    id: number
    event_id: number
    seat_number: string
    asa_id: number
    ticket_price: number
    status: string
    current_owner_wallet: string
    txn_id?: string
    minted_at: string
}

export interface Event {
    id: number
    name: string
    description: string
    venue: string
    event_date: string
    total_seats: number
    max_resale_price: number
    organizer_wallet: string
    app_id: number
    status: string
    created_at: string
}

export const convertDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    })
}

export const ApiService = {
    getEvents: async (): Promise<Event[]> => {
        const response = await api.get<Event[]>('/events')
        return response.data
    },

    getTickets: async (owner?: string): Promise<Ticket[]> => {
        // Note: Backend needs to support ?owner=... filter
        const response = await api.get<Ticket[]>('/tickets', {
            params: { owner }
        })
        return response.data
    },

    mintTicket: async (eventId: number, seatNumber: string, price: number): Promise<Ticket> => {
        const response = await api.post<Ticket>('/tickets/mint', {
            event_id: eventId,
            seat_number: seatNumber,
            ticket_price: price,
        })
        return response.data
    }
}
