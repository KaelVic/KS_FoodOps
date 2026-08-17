"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { DeliveryKanban, DeliveryOrderSummary, OrderChannel } from "@/types/orders"
import { MenuItem } from "@/types/menu"
import {
  fetchDeliveryKanbanClient,
  updateDeliveryStatusClient,
  createOrderClient,
} from "@/lib/api-client"
import {
  Bike,
  Plus,
  RefreshCw,
  Clock,
  MapPin,
  Phone,
  DollarSign,
  Package,
  CheckCircle2,
  AlertCircle,
  X,
  ChevronRight,
  MessageSquare,
  Globe,
} from "lucide-react"

interface DeliveryClientProps {
  initialKanban: DeliveryKanban | null
  menuItems: MenuItem[]
}

export function DeliveryClient({
  initialKanban,
  menuItems,
}: DeliveryClientProps) {
  const [kanban, setKanban] = useState<DeliveryKanban | null>(initialKanban)
  const [loading, setLoading] = useState(false)

  // Modal: New Delivery Order
  const [newOrderModalOpen, setNewOrderModalOpen] = useState(false)
  const [channel, setChannel] = useState<string>("DELIVERY")
  const [customerName, setCustomerName] = useState("")
  const [customerPhone, setCustomerPhone] = useState("")
  const [deliveryAddress, setDeliveryAddress] = useState("")
  const [deliveryFee, setDeliveryFee] = useState("10.00")
  const [orderNotes, setOrderNotes] = useState("")
  const [paymentMethod, setPaymentMethod] = useState("PIX")
  const [selectedItems, setSelectedItems] = useState<{
    menu_item_id: string
    name: string
    quantity: number
    unit_price: number
  }[]>([])

  // Item selector inside modal
  const [selectedMenuItemId, setSelectedMenuItemId] = useState<string>(
    menuItems.length > 0 ? menuItems[0].id : ""
  )
  const [itemQuantity, setItemQuantity] = useState<number>(1)

  const reloadKanban = async () => {
    setLoading(true)
    try {
      const data = await fetchDeliveryKanbanClient()
      setKanban(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdvanceStatus = async (orderId: string, nextStatus: string) => {
    try {
      await updateDeliveryStatusClient(orderId, nextStatus)
      await reloadKanban()
    } catch (err) {
      console.error(err)
    }
  }

  const handleAddItemToOrder = () => {
    const mi = menuItems.find((m) => m.id === selectedMenuItemId)
    if (!mi) return
    setSelectedItems([
      ...selectedItems,
      {
        menu_item_id: mi.id,
        name: mi.name,
        quantity: itemQuantity,
        unit_price: mi.sale_price,
      },
    ])
    setItemQuantity(1)
  }

  const handleCreateDeliveryOrder = async () => {
    if (!customerName.trim() || selectedItems.length === 0) {
      alert("Informe o nome do cliente e adicione ao menos um item.")
      return
    }
    try {
      const payload = {
        channel,
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim() || undefined,
        delivery_address: deliveryAddress.trim() || undefined,
        delivery_fee: parseFloat(deliveryFee) || 0,
        notes: orderNotes.trim() || undefined,
        payment_method: paymentMethod,
        items: selectedItems.map((i) => ({
          menu_item_id: i.menu_item_id,
          name: i.name,
          quantity: i.quantity,
          unit_price: i.unit_price,
        })),
      }
      await createOrderClient(payload)
      setNewOrderModalOpen(false)
      setCustomerName("")
      setCustomerPhone("")
      setDeliveryAddress("")
      setSelectedItems([])
      await reloadKanban()
    } catch (err) {
      console.error(err)
    }
  }

  const pendingList = kanban?.PENDING || []
  const preparingList = kanban?.PREPARING || []
  const readyList = kanban?.READY || []
  const outList = kanban?.OUT_FOR_DELIVERY || []
  const completedList = kanban?.COMPLETED || []

  const totalActive =
    pendingList.length + preparingList.length + readyList.length + outList.length

  const getChannelBadge = (ch: OrderChannel) => {
    switch (ch) {
      case "DELIVERY":
        return <Badge variant="amber" className="text-2xs">🛵 iFood / Delivery</Badge>
      case "WHATSAPP":
        return <Badge variant="emerald" className="text-2xs">💬 WhatsApp</Badge>
      case "QR_CODE":
        return <Badge variant="violet" className="text-2xs">📱 QR Code</Badge>
      case "TAKEOUT":
        return <Badge variant="cyan" className="text-2xs">🥡 Balcão</Badge>
      default:
        return <Badge variant="default" className="text-2xs">{ch}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassPanel className="p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">
            Pedidos Ativos no Hub
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{totalActive} pedidos</div>
          <p className="text-2xs text-slate-500 mt-1">Em produção e rota de entrega</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-amber-400 font-semibold uppercase">
            Em Cozinha / Preparo
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {preparingList.length} pedidos
          </div>
          <p className="text-2xs text-slate-500 mt-1">Sendo confeccionados pelo KDS</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-blue-400 font-semibold uppercase">
            Em Rota de Entrega
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{outList.length} entregas</div>
          <p className="text-2xs text-slate-500 mt-1">Em trânsito com motoboys</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-emerald-400 font-semibold uppercase">
            Entregues Hoje
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {completedList.length} pedidos
          </div>
          <p className="text-2xs text-slate-500 mt-1">Ciclo de entrega concluído</p>
        </GlassPanel>
      </div>

      {/* Action Bar */}
      <GlassPanel className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={reloadKanban}
            disabled={loading}
            className="h-9 px-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium flex items-center transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar Hub
          </button>
        </div>

        <button
          onClick={() => setNewOrderModalOpen(true)}
          className="h-9 px-4 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold hover:from-amber-600 hover:to-orange-600 text-xs flex items-center transition-colors shadow-lg shadow-amber-500/20"
        >
          <Plus className="h-4 w-4 mr-1.5" />
          Novo Pedido Manual (WhatsApp / Telefone)
        </button>
      </GlassPanel>

      {/* Kanban Board (4 Columns) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Column 1: PENDING & PREPARING (Cozinha) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-amber-500/30">
            <div className="flex items-center gap-1.5 font-bold text-sm text-amber-400">
              <Package className="h-4 w-4" />
              <span>1. Em Preparo ({preparingList.length + pendingList.length})</span>
            </div>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {[...pendingList, ...preparingList].length === 0 ? (
              <p className="text-xs text-slate-500 italic py-8 text-center">Nenhum pedido</p>
            ) : (
              [...pendingList, ...preparingList].map((ord) => (
                <div
                  key={ord.id}
                  className="p-3.5 rounded-xl border border-amber-500/30 bg-slate-900/90 shadow space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-100 font-mono">
                      {ord.order_number}
                    </span>
                    {getChannelBadge(ord.channel)}
                  </div>

                  <div>
                    <div className="font-semibold text-xs text-slate-200">{ord.customer_name}</div>
                    {ord.delivery_address && (
                      <div className="text-2xs text-slate-400 flex items-start gap-1 mt-0.5">
                        <MapPin className="h-3 w-3 shrink-0 text-slate-500 mt-0.5" />
                        <span className="truncate">{ord.delivery_address}</span>
                      </div>
                    )}
                  </div>

                  <div className="p-2 bg-slate-950 rounded border border-slate-800 text-2xs space-y-0.5">
                    {ord.items_summary.map((item, idx) => (
                      <div key={idx} className="text-slate-300">
                        {item}
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs">
                    <span className="font-bold text-slate-100 font-mono">
                      R$ {ord.total_amount.toFixed(2)}
                    </span>
                    <button
                      onClick={() => handleAdvanceStatus(ord.id, "READY")}
                      className="px-2.5 py-1 rounded bg-amber-500 text-slate-950 font-bold text-2xs flex items-center hover:bg-amber-600 transition-colors"
                    >
                      Pronto <ChevronRight className="h-3 w-3 ml-0.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 2: READY (Prontos p/ Despacho) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-blue-500/30">
            <div className="flex items-center gap-1.5 font-bold text-sm text-blue-400">
              <Package className="h-4 w-4" />
              <span>2. Aguardando Motoboy ({readyList.length})</span>
            </div>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {readyList.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-8 text-center">Nenhum pedido</p>
            ) : (
              readyList.map((ord) => (
                <div
                  key={ord.id}
                  className="p-3.5 rounded-xl border border-blue-500/40 bg-blue-950/10 shadow space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-100 font-mono">
                      {ord.order_number}
                    </span>
                    {getChannelBadge(ord.channel)}
                  </div>

                  <div>
                    <div className="font-semibold text-xs text-slate-200">{ord.customer_name}</div>
                    {ord.delivery_address && (
                      <div className="text-2xs text-slate-400 flex items-start gap-1 mt-0.5">
                        <MapPin className="h-3 w-3 shrink-0 text-slate-500 mt-0.5" />
                        <span className="truncate">{ord.delivery_address}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs">
                    <span className="font-bold text-slate-100 font-mono">
                      R$ {ord.total_amount.toFixed(2)}
                    </span>
                    <button
                      onClick={() => handleAdvanceStatus(ord.id, "OUT_FOR_DELIVERY")}
                      className="px-2.5 py-1 rounded bg-blue-500 text-slate-950 font-bold text-2xs flex items-center hover:bg-blue-600 transition-colors"
                    >
                      Despachar <Bike className="h-3 w-3 ml-1" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 3: OUT_FOR_DELIVERY (Em Rota) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-purple-500/30">
            <div className="flex items-center gap-1.5 font-bold text-sm text-purple-400">
              <Bike className="h-4 w-4" />
              <span>3. Em Trânsito ({outList.length})</span>
            </div>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {outList.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-8 text-center">Nenhum pedido em rota</p>
            ) : (
              outList.map((ord) => (
                <div
                  key={ord.id}
                  className="p-3.5 rounded-xl border border-purple-500/40 bg-purple-950/10 shadow space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-100 font-mono">
                      {ord.order_number}
                    </span>
                    <Badge variant="violet" className="text-2xs">
                      Em Rota
                    </Badge>
                  </div>

                  <div>
                    <div className="font-semibold text-xs text-slate-200">{ord.customer_name}</div>
                    {ord.delivery_address && (
                      <div className="text-2xs text-slate-400 flex items-start gap-1 mt-0.5">
                        <MapPin className="h-3 w-3 shrink-0 text-slate-500 mt-0.5" />
                        <span className="truncate">{ord.delivery_address}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-xs">
                    <span className="font-bold text-slate-100 font-mono">
                      R$ {ord.total_amount.toFixed(2)}
                    </span>
                    <button
                      onClick={() => handleAdvanceStatus(ord.id, "COMPLETED")}
                      className="px-2.5 py-1 rounded bg-emerald-500 text-slate-950 font-bold text-2xs flex items-center hover:bg-emerald-600 transition-colors"
                    >
                      Confirmar Entrega <CheckCircle2 className="h-3 w-3 ml-1" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 4: COMPLETED (Entregues) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-emerald-500/30">
            <div className="flex items-center gap-1.5 font-bold text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              <span>4. Concluídos ({completedList.length})</span>
            </div>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {completedList.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-8 text-center">Nenhum pedido entregue</p>
            ) : (
              completedList.slice(0, 10).map((ord) => (
                <div
                  key={ord.id}
                  className="p-3 rounded-xl border border-slate-800 bg-slate-900/60 opacity-80 space-y-1.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-300 font-mono">{ord.order_number}</span>
                    <Badge variant="emerald" className="text-2xs">
                      Entregue
                    </Badge>
                  </div>
                  <div className="font-semibold text-slate-200">{ord.customer_name}</div>
                  <div className="flex justify-between text-2xs text-slate-400 font-mono">
                    <span>Total: R$ {ord.total_amount.toFixed(2)}</span>
                    <span>Pago ({ord.payment_method})</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Modal: New Manual Delivery Order */}
      {newOrderModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Bike className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Novo Pedido Delivery (WhatsApp / Telefone)
                </h3>
              </div>
              <button
                onClick={() => setNewOrderModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Canal de Venda</label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="WHATSAPP">WhatsApp</option>
                  <option value="DELIVERY">Delivery Direto / Telefone</option>
                  <option value="TAKEOUT">Retirada no Balcão (Takeout)</option>
                  <option value="QR_CODE">Cardápio Digital Web</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Nome do Cliente</label>
                <input
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Ex: Beatriz Lima"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Telefone / WhatsApp</label>
                <input
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="Ex: (11) 98888-7777"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Taxa de Entrega (R$)</label>
                <input
                  type="number"
                  step="1.00"
                  value={deliveryFee}
                  onChange={(e) => setDeliveryFee(e.target.value)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="col-span-2 space-y-1">
                <label className="text-slate-300 font-medium">Endereço de Entrega Completo</label>
                <input
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  placeholder="Ex: Alameda dos Anapurus, 1200, Bloco B, Apto 54"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            {/* Item Selector */}
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 text-xs">
              <div className="font-semibold text-slate-300">Adicionar Pratos / Bebidas:</div>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <select
                    value={selectedMenuItemId}
                    onChange={(e) => setSelectedMenuItemId(e.target.value)}
                    className="h-9 w-full px-2 rounded border border-slate-700 bg-slate-900 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {menuItems.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} — R$ {m.sale_price.toFixed(2)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min="1"
                    value={itemQuantity}
                    onChange={(e) => setItemQuantity(parseInt(e.target.value) || 1)}
                    className="h-9 w-16 px-2 rounded border border-slate-700 bg-slate-900 text-xs text-slate-200 text-center focus:outline-none focus:border-amber-500"
                  />
                  <button
                    type="button"
                    onClick={handleAddItemToOrder}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded text-xs transition-colors"
                  >
                    +
                  </button>
                </div>
              </div>

              {selectedItems.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-800 space-y-1">
                  {selectedItems.map((it, idx) => (
                    <div key={idx} className="flex justify-between text-2xs text-slate-300">
                      <span>
                        {it.quantity}x {it.name}
                      </span>
                      <span className="font-mono text-amber-400">
                        R$ {(it.quantity * it.unit_price).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setNewOrderModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateDeliveryOrder}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold hover:from-amber-600 hover:to-orange-600 text-xs transition-colors"
              >
                Despachar para Produção
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
