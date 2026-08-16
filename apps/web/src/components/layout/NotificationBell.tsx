"use client"

import { useState, useEffect } from "react"
import { fetchNotificationsClient, markNotificationReadClient } from "@/lib/api-client"

interface Notification {
  id: string
  title: string
  message: string
  type: string
  is_read: boolean
  created_at: string
}

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isOpen, setIsOpen] = useState(false)

  const fetchNotifications = async () => {
    try {
      const data = await fetchNotificationsClient()
      setNotifications(data || [])
    } catch (e) {
      console.error("Failed to fetch notifications")
    }
  }

  const markAsRead = async (id: string) => {
    try {
      const success = await markNotificationReadClient(id)
      if (success) {
        setNotifications((prev) => prev.filter((n) => n.id !== id))
      }
    } catch (e) {
      console.error("Failed to mark as read")
    }
  }

  useEffect(() => {
    fetchNotifications()
    // Poll every minute
    const interval = setInterval(fetchNotifications, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-zinc-400 hover:text-white transition-colors focus:outline-none"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {notifications.length > 0 && (
          <span className="absolute top-1 right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-500 text-[8px] font-bold text-white">
            {notifications.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 origin-top-right rounded-xl border border-white/10 bg-zinc-900 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50 overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h3 className="text-sm font-medium text-white">Notificações</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-sm text-zinc-500 text-center">Nenhuma notificação nova</div>
            ) : (
              <ul className="divide-y divide-white/5">
                {notifications.map((n) => (
                  <li key={n.id} className="p-4 hover:bg-white/5 transition-colors group relative">
                    <div className="flex flex-col gap-1 pr-6">
                      <span className="text-xs font-semibold text-zinc-300">{n.title}</span>
                      <span className="text-xs text-zinc-400">{n.message}</span>
                    </div>
                    <button 
                      onClick={() => markAsRead(n.id)}
                      className="absolute right-4 top-4 text-zinc-500 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Marcar como lida"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
