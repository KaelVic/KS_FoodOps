"use client"

import React, { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { DiningTable, TableStatus, Order, OrderItem } from "@/types/orders"
import { MenuItem } from "@/types/menu"
import { BankAccount, PaymentAcquirer } from "@/types/financial"
import {
  fetchDiningTablesClient,
  createDiningTableClient,
  updateDiningTableStatusClient,
  fetchOrderDetailClient,
  createOrderClient,
  addItemsToOrderClient,
  closeAndPayOrderClient,
} from "@/lib/api-client"
import {
  Plus,
  Search,
  RefreshCw,
  Users,
  UtensilsCrossed,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertCircle,
  X,
  CreditCard,
  ChefHat,
  Receipt,
  FilePlus,
  Sparkles,
  Warehouse,
} from "lucide-react"

interface TablesClientProps {
  initialTables: DiningTable[]
  menuItems: MenuItem[]
  bankAccounts: BankAccount[]
  acquirers: PaymentAcquirer[]
}

interface Toast {
  message: string
  type: "success" | "error" | "info"
}

export function TablesClient({
  initialTables,
  menuItems,
  bankAccounts,
  acquirers,
}: TablesClientProps) {
  const [tables, setTables] = useState<DiningTable[]>(initialTables)
  const [loading, setLoading] = useState(false)

  // Filters
  const [selectedSection, setSelectedSection] = useState<string>("ALL")
  const [statusFilter, setStatusFilter] = useState<string>("ALL")

  // Active Selected Table & Order
  const [selectedTable, setSelectedTable] = useState<DiningTable | null>(null)
  const [activeOrder, setActiveOrder] = useState<Order | null>(null)
  const [loadingOrder, setLoadingOrder] = useState(false)

  // Open Order Modal (for free table)
  const [openOrderModal, setOpenOrderModal] = useState(false)
  const [waiterName, setWaiterName] = useState("")
  const [customerName, setCustomerName] = useState("")
  const [initialOrderItems, setInitialOrderItems] = useState<{
    menu_item_id: string
    name: string
    quantity: number
    unit_price: number
    preparation_notes: string
    production_station: string
  }[]>([])
  const [isOpeningOrder, setIsOpeningOrder] = useState(false)

  // Add Item to existing order modal
  const [addItemModalOpen, setAddItemModalOpen] = useState(false)
  const [selectedMenuItemId, setSelectedMenuItemId] = useState<string>(
    menuItems.length > 0 ? menuItems[0].id : ""
  )
  const [itemQuantity, setItemQuantity] = useState<number>(1)
  const [itemNotes, setItemNotes] = useState<string>("")
  const [isAddingItem, setIsAddingItem] = useState(false)

  // Close & Pay Modal
  const [payModalOpen, setPayModalOpen] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState<string>("CREDIT_CARD")
  const [selectedAcquirerId, setSelectedAcquirerId] = useState<string>(
    acquirers.length > 0 ? acquirers[0].id : ""
  )
  const [selectedBankAccountId, setSelectedBankAccountId] = useState<string>(
    bankAccounts.length > 0 ? bankAccounts[0].id : ""
  )
  const [isPaying, setIsPaying] = useState(false)
  const [isCreatingTable, setIsCreatingTable] = useState(false)

  // Create Table Modal
  const [createTableModalOpen, setCreateTableModalOpen] = useState(false)
  const [newTableNumber, setNewTableNumber] = useState("")
  const [newTableCapacity, setNewTableCapacity] = useState(4)
  const [newTableSection, setNewTableSection] = useState("Salão Principal")
  
  // Toast
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = (message: string, type: Toast["type"] = "info") => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const reloadTables = async () => {
    setLoading(true)
    try {
      const data = await fetchDiningTablesClient(
        selectedSection === "ALL" ? undefined : selectedSection,
        statusFilter === "ALL" ? undefined : statusFilter
      )
      setTables(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleTableClick = async (table: DiningTable) => {
    setSelectedTable(table)
    if (table.active_order_id) {
      setLoadingOrder(true)
      try {
        const ord = await fetchOrderDetailClient(table.active_order_id)
        setActiveOrder(ord)
      } catch (err) {
        console.error(err)
      } finally {
        setLoadingOrder(false)
      }
    } else {
      setActiveOrder(null)
    }
  }

  const handleOpenNewOrder = async () => {
    if (!selectedTable) return
    if (initialOrderItems.length === 0) {
      showToast("Adicione ao menos um item à comanda.", "error")
      return
    }
    setIsOpeningOrder(true)
    try {
      const payload = {
        channel: "DINE_IN",
        table_id: selectedTable.id,
        waiter_name: waiterName || "Atendente",
        customer_name: customerName || selectedTable.table_number,
        items: initialOrderItems.map((i) => ({
          menu_item_id: i.menu_item_id,
          name: i.name,
          quantity: i.quantity,
          unit_price: i.unit_price,
          preparation_notes: i.preparation_notes || undefined,
          production_station: i.production_station,
        })),
      }
      const ord = await createOrderClient(payload)
      setActiveOrder(ord)
      setOpenOrderModal(false)
      setInitialOrderItems([])
      setWaiterName("")
      setCustomerName("")
      showToast("Comanda aberta com sucesso!", "success")
      await reloadTables()
    } catch (err) {
      console.error(err)
      showToast("Erro ao abrir comanda. Tente novamente.", "error")
    } finally {
      setIsOpeningOrder(false)
    }
  }

  const handleAddInitialItem = () => {
    const mi = menuItems.find((m) => m.id === selectedMenuItemId)
    if (!mi) return
    setInitialOrderItems([
      ...initialOrderItems,
      {
        menu_item_id: mi.id,
        name: mi.name,
        quantity: itemQuantity,
        unit_price: mi.sale_price,
        preparation_notes: itemNotes,
        production_station: mi.category_name?.toUpperCase().includes("BEBIDA")
          ? "BAR"
          : "KITCHEN",
      },
    ])
    setItemNotes("")
    setItemQuantity(1)
  }

  const handleAddItemsToActiveOrder = async () => {
    if (!activeOrder) return
    const mi = menuItems.find((m) => m.id === selectedMenuItemId)
    if (!mi) return
    if (itemQuantity <= 0) {
      showToast("Quantidade deve ser maior que zero.", "error")
      return
    }
    setIsAddingItem(true)
    try {
      const itemsPayload = [
        {
          menu_item_id: mi.id,
          name: mi.name,
          quantity: itemQuantity,
          unit_price: mi.sale_price,
          preparation_notes: itemNotes || undefined,
          production_station: mi.category_name?.toUpperCase().includes("BEBIDA")
            ? "BAR"
            : "KITCHEN",
        },
      ]
      const updatedOrd = await addItemsToOrderClient(activeOrder.id, itemsPayload)
      setActiveOrder(updatedOrd)
      setAddItemModalOpen(false)
      setItemNotes("")
      setItemQuantity(1)
      showToast("Item enviado para o KDS!", "success")
      await reloadTables()
    } catch (err) {
      console.error(err)
      showToast("Erro ao adicionar item. Tente novamente.", "error")
    } finally {
      setIsAddingItem(false)
    }
  }

  const handleCloseAndPay = async () => {
    if (!activeOrder) return
    setIsPaying(true)
    try {
      await closeAndPayOrderClient(activeOrder.id, {
        payment_method: paymentMethod,
        acquirer_id: selectedAcquirerId || undefined,
        bank_account_id: selectedBankAccountId || undefined,
      })
      setPayModalOpen(false)
      setActiveOrder(null)
      setSelectedTable(null)
      showToast("Conta fechada e pagamento registrado!", "success")
      await reloadTables()
    } catch (err) {
      console.error(err)
      showToast("Erro ao fechar conta. Tente novamente.", "error")
    } finally {
      setIsPaying(false)
    }
  }

  const handleCreateTable = async () => {
    if (!newTableNumber.trim()) {
      showToast("Informe o número/nome da mesa.", "error")
      return
    }
    setIsCreatingTable(true)
    try {
      await createDiningTableClient({
        table_number: newTableNumber.trim(),
        capacity: newTableCapacity,
        section: newTableSection,
        status: "AVAILABLE",
      })
      setNewTableNumber("")
      setCreateTableModalOpen(false)
      showToast("Mesa criada com sucesso!", "success")
      await reloadTables()
    } catch (err) {
      console.error(err)
      showToast("Erro ao criar mesa. Tente novamente.", "error")
    } finally {
      setIsCreatingTable(false)
    }
  }

  // Sections
  const sections = Array.from(new Set(tables.map((t) => t.section)))

  // Quick stats
  const totalTables = tables.length
  const occupiedTables = tables.filter((t) => t.status === "OCCUPIED").length
  const availableTables = tables.filter((t) => t.status === "AVAILABLE").length
  const billRequested = tables.filter((t) => t.status === "BILL_REQUESTED").length

  return (
    <div className="space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassPanel className="p-4">
          <div className="text-xs text-slate-400 font-semibold uppercase">Total de Mesas</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{totalTables} mesas</div>
          <p className="text-2xs text-slate-500 mt-1">Capacidade total do salão</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-blue-400 font-semibold uppercase">Mesas Ocupadas</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{occupiedTables} mesas</div>
          <p className="text-2xs text-slate-500 mt-1">
            {totalTables > 0 ? ((occupiedTables / totalTables) * 100).toFixed(0) : 0}% de ocupação
          </p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-emerald-400 font-semibold uppercase">Mesas Livres</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{availableTables} mesas</div>
          <p className="text-2xs text-slate-500 mt-1">Prontas para receber clientes</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="text-xs text-amber-400 font-semibold uppercase">Conta Solicitada</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{billRequested} mesas</div>
          <p className="text-2xs text-slate-500 mt-1">Aguardando fechamento e pagamento</p>
        </GlassPanel>
      </div>

      {/* Action Bar & Section Tabs */}
      <GlassPanel className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setSelectedSection("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedSection === "ALL"
                ? "bg-amber-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            Todos os Setores ({totalTables})
          </button>
          {sections.map((sec) => (
            <button
              key={sec}
              onClick={() => setSelectedSection(sec)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                selectedSection === sec
                  ? "bg-amber-500 text-slate-950 font-bold"
                  : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
              }`}
            >
              {sec} ({tables.filter((t) => t.section === sec).length})
            </button>
          ))}

          <button
            onClick={reloadTables}
            disabled={loading}
            className="p-1.5 ml-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCreateTableModalOpen(true)}
            className="h-9 px-4 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold hover:from-amber-600 hover:to-orange-600 text-xs flex items-center transition-colors shadow-lg shadow-amber-500/20"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Adicionar Mesa
          </button>
        </div>
      </GlassPanel>

      {/* Main Content: Tables Grid + Order Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tables Grid (2 Cols on lg) */}
        <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {tables
            .filter(
              (t) =>
                (selectedSection === "ALL" || t.section === selectedSection) &&
                (statusFilter === "ALL" || t.status === statusFilter)
            )
            .map((table) => {
              const isOccupied = table.status === "OCCUPIED"
              const isBill = table.status === "BILL_REQUESTED"
              const isReserved = table.status === "RESERVED"
              const isSelected = selectedTable?.id === table.id

              let statusBg = "border-emerald-500/30 bg-emerald-950/10 hover:border-emerald-500/60"
              let statusBadgeVariant: "emerald" | "cyan" | "amber" | "violet" | "default" = "emerald"
              let statusLabel = "Livre"

              if (isOccupied) {
                statusBg = "border-blue-500/40 bg-blue-950/20 hover:border-blue-500/80 shadow-lg shadow-blue-500/5"
                statusBadgeVariant = "cyan"
                statusLabel = "Ocupada"
              } else if (isBill) {
                statusBg = "border-amber-500/40 bg-amber-950/20 hover:border-amber-500/80 animate-pulse"
                statusBadgeVariant = "amber"
                statusLabel = "Pediu Conta"
              } else if (isReserved) {
                statusBg = "border-purple-500/40 bg-purple-950/20 hover:border-purple-500/80"
                statusBadgeVariant = "violet"
                statusLabel = "Reservada"
              }

              return (
                <div
                  key={table.id}
                  onClick={() => handleTableClick(table)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between min-h-[140px] ${statusBg} ${
                    isSelected ? "ring-2 ring-amber-400" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-base text-slate-100">
                      {table.table_number}
                    </span>
                    <Badge variant={statusBadgeVariant} className="text-2xs">
                      {statusLabel}
                    </Badge>
                  </div>

                  <div className="py-2">
                    <div className="text-2xs text-slate-400 flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      <span>{table.capacity} lugares</span>
                      <span>•</span>
                      <span>{table.section}</span>
                    </div>

                    {isOccupied && (
                      <div className="mt-2 text-xs font-semibold text-blue-300 flex items-center justify-between">
                        <span>Consumo:</span>
                        <span className="font-mono text-emerald-400 font-bold">Comanda aberta</span>
                      </div>
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-2xs text-slate-400">
                    <span>Clique p/ gerenciar</span>
                    <UtensilsCrossed className="h-3.5 w-3.5 text-slate-500" />
                  </div>
                </div>
              )
            })}
        </div>

        {/* Selected Table / Order Management Drawer */}
        <div className="lg:col-span-1">
          {selectedTable ? (
            <GlassPanel className="p-5 space-y-4 sticky top-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg">
                    <UtensilsCrossed className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-100">
                      {selectedTable.table_number}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {selectedTable.section} • Capacidade para {selectedTable.capacity} pessoas
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedTable(null)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* State 1: Table is AVAILABLE */}
              {selectedTable.status === "AVAILABLE" && (
                <div className="space-y-4 py-4 text-center">
                  <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
                    <div className="text-sm font-semibold text-slate-200">Mesa Livre</div>
                    <p className="text-xs text-slate-400">
                      Nenhum cliente alocado no momento. Deseja abrir uma comanda de atendimento?
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      setOpenOrderModal(true)
                      setInitialOrderItems([])
                    }}
                    className="w-full py-2.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold hover:from-emerald-600 hover:to-teal-600 text-xs flex items-center justify-center transition-colors shadow-lg shadow-emerald-500/20"
                  >
                    <Plus className="h-4 w-4 mr-1.5" />
                    Abrir Comanda nesta Mesa
                  </button>

                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        await updateDiningTableStatusClient(selectedTable.id, "RESERVED")
                        showToast("Mesa marcada como reservada.", "success")
                        await reloadTables()
                        setSelectedTable(null)
                      }}
                      className="flex-1 py-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30 text-2xs font-semibold transition-colors"
                    >
                      Marcar Reservada
                    </button>
                    <button
                      onClick={async () => {
                        await updateDiningTableStatusClient(selectedTable.id, "CLEANING")
                        showToast("Mesa marcada para higienização.", "success")
                        await reloadTables()
                        setSelectedTable(null)
                      }}
                      className="flex-1 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-2xs font-semibold transition-colors"
                    >
                      Em Higienização
                    </button>
                  </div>
                </div>
              )}

              {/* State 2: Table is OCCUPIED or BILL_REQUESTED with active order */}
              {(selectedTable.status === "OCCUPIED" || selectedTable.status === "BILL_REQUESTED") && (
                <div className="space-y-4">
                  {loadingOrder ? (
                    <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" /> Carregando comanda...
                    </div>
                  ) : activeOrder ? (
                    <>
                      <div className="p-3 bg-slate-900/90 rounded-lg border border-slate-800 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-200">
                            Comanda: {activeOrder.order_number}
                          </span>
                          <Badge variant="cyan" className="text-2xs">
                            {activeOrder.status}
                          </Badge>
                        </div>
                        <div className="text-2xs text-slate-400 flex justify-between">
                          <span>Garçom: {activeOrder.waiter_name || "Atendente"}</span>
                          <span>Cliente: {activeOrder.customer_name || "Mesa"}</span>
                        </div>
                      </div>

                      {/* Items List */}
                      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Itens Lançados ({activeOrder.items.length})
                        </div>
                        {activeOrder.items.length === 0 ? (
                          <p className="text-xs text-slate-500 italic py-3 text-center">
                            Nenhum item lançado ainda.
                          </p>
                        ) : (
                          activeOrder.items.map((item) => (
                            <div
                              key={item.id}
                              className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 flex items-center justify-between text-xs"
                            >
                              <div>
                                <div className="font-semibold text-slate-200">
                                  {item.quantity}x {item.name}
                                </div>
                                {item.preparation_notes && (
                                  <div className="text-2xs text-amber-400 italic">
                                    obs: {item.preparation_notes}
                                  </div>
                                )}
                                <div className="text-2xs text-slate-500 mt-0.5 flex gap-1">
                                  <span>{item.production_station}</span>
                                  <span>•</span>
                                  <span
                                    className={
                                      item.status === "READY"
                                        ? "text-emerald-400 font-bold"
                                        : item.status === "PREPARING"
                                        ? "text-amber-400"
                                        : "text-slate-400"
                                    }
                                  >
                                    {item.status}
                                  </span>
                                </div>
                              </div>
                              <div className="font-mono font-semibold text-slate-200">
                                R$ {item.total_price.toFixed(2)}
                              </div>
                            </div>
                          ))
                        )}
                      </div>

                      {/* Financial Total */}
                      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1 text-xs">
                        <div className="flex justify-between text-slate-400">
                          <span>Subtotal:</span>
                          <span className="font-mono">R$ {activeOrder.subtotal.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-base font-bold text-slate-100 pt-1 border-t border-slate-800">
                          <span>Total da Conta:</span>
                          <span className="font-mono text-emerald-400">
                            R$ {activeOrder.total_amount.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="space-y-2 pt-2">
                        <button
                          onClick={() => setAddItemModalOpen(true)}
                          className="w-full py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center transition-colors"
                        >
                          <Plus className="h-4 w-4 mr-1.5 text-amber-400" />
                          Lançar Novos Pratos / Bebidas
                        </button>

                        <button
                          onClick={() => setPayModalOpen(true)}
                          className="w-full py-2.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold hover:from-emerald-600 hover:to-teal-600 text-xs flex items-center justify-center transition-colors shadow-lg shadow-emerald-500/20"
                        >
                          <CreditCard className="h-4 w-4 mr-1.5" />
                          Fechar Conta & Receber Pagamento
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="py-6 text-center text-xs text-slate-500">
                      Nenhuma comanda vinculada.
                    </div>
                  )}
                </div>
              )}
            </GlassPanel>
          ) : (
            <GlassPanel className="p-8 text-center text-slate-500 space-y-3">
              <UtensilsCrossed className="h-10 w-10 mx-auto text-slate-600" />
              <div className="text-sm font-semibold text-slate-400">Nenhuma mesa selecionada</div>
              <p className="text-xs text-slate-500">
                Clique em qualquer mesa do mapa ao lado para abrir comanda, adicionar itens ou fechar conta.
              </p>
            </GlassPanel>
          )}
        </div>
      </div>

      {/* Modal: Open New Order */}
      {openOrderModal && selectedTable && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <UtensilsCrossed className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Abrir Atendimento — {selectedTable.table_number}
                </h3>
              </div>
              <button onClick={() => setOpenOrderModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Garçom / Atendente</label>
                <input
                  value={waiterName}
                  onChange={(e) => setWaiterName(e.target.value)}
                  placeholder="Ex: Carlos"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Nome do Cliente (opcional)</label>
                <input
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Ex: Família Souza"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            {/* Quick Add First Item */}
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-2 text-xs">
              <div className="font-semibold text-slate-300">Lançar Primeiro Pedido:</div>
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
                <div>
                  <input
                    type="number"
                    min="1"
                    value={itemQuantity}
                    onChange={(e) => setItemQuantity(parseInt(e.target.value) || 1)}
                    className="h-9 w-full px-2 rounded border border-slate-700 bg-slate-900 text-xs text-slate-200 text-center focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  value={itemNotes}
                  onChange={(e) => setItemNotes(e.target.value)}
                  placeholder="Observação (Ex: Sem cebola, gelo e limão)"
                  className="h-8 flex-1 px-2 rounded border border-slate-700 bg-slate-900 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
                <button
                  type="button"
                  onClick={handleAddInitialItem}
                  className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded text-xs transition-colors"
                >
                  Adicionar
                </button>
              </div>

              {initialOrderItems.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-800 space-y-1">
                  {initialOrderItems.map((it, idx) => (
                    <div key={idx} className="flex justify-between text-2xs text-slate-300">
                      <span>
                        {it.quantity}x {it.name} {it.preparation_notes ? `(${it.preparation_notes})` : ""}
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
                onClick={() => setOpenOrderModal(false)}
                disabled={isOpeningOrder}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleOpenNewOrder}
                disabled={isOpeningOrder || initialOrderItems.length === 0}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold hover:from-emerald-600 hover:to-teal-600 text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isOpeningOrder ? "Abrindo..." : "Confirmar Abertura de Mesa"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add Items to active order */}
      {addItemModalOpen && activeOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ChefHat className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Lançar Item — {activeOrder.order_number}
                </h3>
              </div>
              <button onClick={() => setAddItemModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Selecione o Prato / Bebida</label>
                <select
                  value={selectedMenuItemId}
                  onChange={(e) => setSelectedMenuItemId(e.target.value)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  {menuItems.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} — R$ {m.sale_price.toFixed(2)} ({m.category_name || "Geral"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Quantidade</label>
                <input
                  type="number"
                  min="1"
                  value={itemQuantity}
                  onChange={(e) => setItemQuantity(parseInt(e.target.value) || 1)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Notas de Preparo para a Cozinha / Bar</label>
                <input
                  value={itemNotes}
                  onChange={(e) => setItemNotes(e.target.value)}
                  placeholder="Ex: Ponto da carne mal passada, sem pimenta"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setAddItemModalOpen(false)}
                disabled={isAddingItem}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddItemsToActiveOrder}
                disabled={isAddingItem || itemQuantity <= 0}
                className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAddingItem ? "Enviando..." : "Enviar para o KDS"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Close & Pay Order */}
      {payModalOpen && activeOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">
                  Fechar Conta — {activeOrder.order_number}
                </h3>
              </div>
              <button onClick={() => setPayModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-center space-y-1">
              <span className="text-2xs text-slate-400 uppercase tracking-wider font-semibold">
                Valor Total a Cobrar
              </span>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                R$ {activeOrder.total_amount.toFixed(2)}
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Forma de Pagamento</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="CREDIT_CARD">Cartão de Crédito</option>
                  <option value="DEBIT_CARD">Cartão de Débito</option>
                  <option value="PIX">PIX Dinâmico</option>
                  <option value="CASH">Dinheiro em Espécie</option>
                  <option value="VOUCHER_VR">Voucher Refeição (VR / VA)</option>
                </select>
              </div>

              {paymentMethod.includes("CARD") && (
                <div className="space-y-1">
                  <label className="text-slate-300 font-medium">Maquininha / Adquirente (MDR)</label>
                  <select
                    value={selectedAcquirerId}
                    onChange={(e) => setSelectedAcquirerId(e.target.value)}
                    className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    {acquirers.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name} ({a.credit_1x_fee_percentage}% Crédito / {a.debit_fee_percentage}% Débito)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Creditar na Conta Bancária / Caixa</label>
                <select
                  value={selectedBankAccountId}
                  onChange={(e) => setSelectedBankAccountId(e.target.value)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  {bankAccounts.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} (Saldo: R$ {b.current_balance.toFixed(2)})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setPayModalOpen(false)}
                disabled={isPaying}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCloseAndPay}
                disabled={isPaying}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isPaying ? "Processando..." : "Confirmar & Liberar Mesa"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Create Dining Table */}
      {createTableModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <UtensilsCrossed className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Nova Mesa</h3>
              </div>
              <button onClick={() => setCreateTableModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Número / Nome da Mesa</label>
                <input
                  value={newTableNumber}
                  onChange={(e) => setNewTableNumber(e.target.value)}
                  placeholder="Ex: Mesa 14, Bar 03, Varanda 02"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Capacidade de Pessoas</label>
                <input
                  type="number"
                  min="1"
                  value={newTableCapacity}
                  onChange={(e) => setNewTableCapacity(parseInt(e.target.value) || 4)}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-300 font-medium">Setor do Salão</label>
                <input
                  value={newTableSection}
                  onChange={(e) => setNewTableSection(e.target.value)}
                  placeholder="Ex: Salão Principal, Varanda, Deck, Bar"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setCreateTableModalOpen(false)}
                disabled={isCreatingTable}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateTable}
                disabled={isCreatingTable || !newTableNumber.trim()}
                className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingTable ? "Salvando..." : "Salvar Mesa"}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-md transition-all"
          style={{
            backgroundColor: toast.type === "success" ? "rgba(16, 185, 129, 0.2)" : toast.type === "error" ? "rgba(239, 68, 68, 0.2)" : "rgba(6, 182, 212, 0.2)",
            borderColor: toast.type === "success" ? "#10b981" : toast.type === "error" ? "#ef4444" : "#06b6d4",
            color: toast.type === "success" ? "#10b981" : toast.type === "error" ? "#ef4444" : "#06b6d4"
          }}
        >
          {toast.type === "success" && <CheckCircle2 className="h-5 w-5" />}
          {toast.type === "error" && <AlertCircle className="h-5 w-5" />}
          {toast.type === "info" && <Warehouse className="h-5 w-5" />}
          <span className="font-medium text-sm">{toast.message}</span>
        </motion.div>
      )}
    </div>
  )
}
