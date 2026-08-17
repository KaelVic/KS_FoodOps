"use client";

import { useState } from "react";
import { 
  Factory, 
  Plus, 
  Play, 
  CheckCircle, 
  Clock, 
  Layers, 
  DollarSign, 
  TrendingUp, 
  Calendar, 
  AlertCircle,
  FileText,
  Boxes,
  ArrowRight
} from "lucide-react";
import { ProductionOrder } from "@/types/production";
import { RecipeListItem } from "@/types/recipes";
import { 
  createProductionOrderClient, 
  startProductionOrderClient, 
  completeProductionOrderClient 
} from "@/lib/api-client";

interface Props {
  initialOrders: ProductionOrder[];
  recipes: RecipeListItem[];
  skus: { id: string; name: string }[];
}

export function ProductionOrdersClient({ initialOrders, recipes, skus }: Props) {
  const [orders, setOrders] = useState<ProductionOrder[]>(initialOrders);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const showToast = (type: "success" | "error", text: string) => {
    setToastMessage({ type, text });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Modal States
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedRecipeId, setSelectedRecipeId] = useState("");
  const [selectedSkuId, setSelectedSkuId] = useState("");
  const [locationId, setLocationId] = useState("");
  const [plannedQty, setPlannedQty] = useState("");
  const [batchNumber, setBatchNumber] = useState("");
  const [expirationDate, setExpirationDate] = useState("");
  const [orderNotes, setOrderNotes] = useState("");

  const [isCompleteModalOpen, setIsCompleteModalOpen] = useState(false);
  const [completingOrder, setCompletingOrder] = useState<ProductionOrder | null>(null);
  const [actualQty, setActualQty] = useState("");
  const [completeBatchNumber, setCompleteBatchNumber] = useState("");
  const [completeExpDate, setCompleteExpDate] = useState("");

  // Selected Order for Detail View
  const [detailOrder, setDetailOrder] = useState<ProductionOrder | null>(null);

  // KPIs
  const activeOps = orders.filter((o) => o.status === "PLANNED" || o.status === "IN_PRODUCTION").length;
  const completedOps = orders.filter((o) => o.status === "COMPLETED").length;
  const totalProductionCost = orders
    .filter((o) => o.status === "COMPLETED")
    .reduce((acc, o) => acc + (Number(o.total_cost) || 0), 0);

  const completedWithActual = orders.filter((o) => o.status === "COMPLETED" && o.actual_quantity && o.planned_quantity);
  const avgYield = completedWithActual.length > 0
    ? (completedWithActual.reduce((acc, o) => acc + (Number(o.actual_quantity) / Number(o.planned_quantity)), 0) / completedWithActual.length) * 100
    : 100;

  // Filtered Orders
  const filteredOrders = orders.filter((o) => {
    const matchesStatus = filterStatus === "ALL" || o.status === filterStatus;
    const matchesSearch = 
      o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (o.recipe_name && o.recipe_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (o.produced_sku_name && o.produced_sku_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecipeId || !selectedSkuId || !plannedQty || Number(plannedQty) <= 0) {
      showToast("error", "Preencha a ficha técnica, SKU produzido e quantidade planejada.");
      return;
    }

    try {
      setIsSubmitting(true);
      // If location is not entered, use a fallback from existing orders or default
      const loc = locationId || (orders.length > 0 ? orders[0].location_id : "00000000-0000-0000-0000-000000000001");
      
      const newOrder = await createProductionOrderClient({
        recipe_id: selectedRecipeId,
        produced_sku_id: selectedSkuId,
        location_id: loc,
        planned_quantity: Number(plannedQty),
        batch_number: batchNumber || undefined,
        expiration_date: expirationDate ? new Date(expirationDate).toISOString() : undefined,
        notes: orderNotes || undefined,
      });

      setOrders([newOrder, ...orders]);
      setIsCreateModalOpen(false);
      setSelectedRecipeId("");
      setSelectedSkuId("");
      setPlannedQty("");
      setBatchNumber("");
      setExpirationDate("");
      setOrderNotes("");
      showToast("success", `Ordem de Produção ${newOrder.order_number} criada com sucesso!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao criar Ordem de Produção.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartOrder = async (orderId: string) => {
    try {
      setIsSubmitting(true);
      const updated = await startProductionOrderClient(orderId);
      setOrders(orders.map((o) => (o.id === orderId ? updated : o)));
      showToast("success", `Produção da OP ${updated.order_number} iniciada!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao iniciar produção.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const openCompleteModal = (order: ProductionOrder) => {
    setCompletingOrder(order);
    setActualQty(String(order.planned_quantity));
    setCompleteBatchNumber(order.batch_number || "");
    setCompleteExpDate(order.expiration_date ? order.expiration_date.split("T")[0] : "");
    setIsCompleteModalOpen(true);
  };

  const handleCompleteOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completingOrder) return;

    try {
      setIsSubmitting(true);
      const updated = await completeProductionOrderClient(completingOrder.id, {
        actual_quantity: Number(actualQty),
        batch_number: completeBatchNumber || undefined,
        expiration_date: completeExpDate ? new Date(completeExpDate).toISOString() : undefined,
      });

      setOrders(orders.map((o) => (o.id === completingOrder.id ? updated : o)));
      setIsCompleteModalOpen(false);
      setCompletingOrder(null);
      showToast("success", `Batelada da OP ${updated.order_number} concluída e movimentada no estoque!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao concluir produção.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`p-3 rounded-lg flex items-center justify-between text-sm shadow-md transition-all ${
            toastMessage.type === "success"
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
          }`}
        >
          <span>{toastMessage.text}</span>
          <button onClick={() => setToastMessage(null)} className="ml-3 hover:opacity-75">
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Factory className="h-7 w-7 text-primary" />
            Central de Produção & Commissary
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Ordens de Produção (OPs), Bateladas de Semi-Acabados (Bases, Molhos, Porcionados) e Rendimentos Reais.
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg shadow transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nova Ordem de Produção (OP)
        </button>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">OPs Ativas em Cozinha</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
              <Clock className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">{activeOps}</div>
          <p className="text-xs text-muted-foreground">Planejadas ou Em Processamento</p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Bateladas Concluídas</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
              <CheckCircle className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">{completedOps}</div>
          <p className="text-xs text-muted-foreground">Estoque semi-acabado creditado</p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Custo Total Produzido</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
              <DollarSign className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">
            {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(totalProductionCost)}
          </div>
          <p className="text-xs text-muted-foreground">Consumo real de insumos</p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Rendimento Médio %</span>
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">
            {avgYield.toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">Real vs Planejado nas bateladas</p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-card p-4 rounded-xl border">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {(["ALL", "PLANNED", "IN_PRODUCTION", "COMPLETED"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${
                filterStatus === st
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {st === "ALL" && "Todas"}
              {st === "PLANNED" && "Planejadas"}
              {st === "IN_PRODUCTION" && "Em Produção"}
              {st === "COMPLETED" && "Concluídas"}
            </button>
          ))}
        </div>

        <div className="w-full sm:w-72">
          <input
            type="text"
            placeholder="Buscar por OP, ficha ou produto..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-1.5 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {/* Production Orders Table */}
      <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-xs font-semibold text-muted-foreground uppercase border-b">
              <tr>
                <th className="px-4 py-3">Ordem / Lote</th>
                <th className="px-4 py-3">Ficha Técnica & Item</th>
                <th className="px-4 py-3">Local de Produção</th>
                <th className="px-4 py-3 text-right">Qtd Planejada</th>
                <th className="px-4 py-3 text-right">Qtd Real</th>
                <th className="px-4 py-3 text-right">Custo Unitário</th>
                <th className="px-4 py-3 text-right">Custo Total</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-muted-foreground">
                    Nenhuma ordem de produção encontrada.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">
                      <div className="font-semibold text-foreground">{order.order_number}</div>
                      {order.batch_number && (
                        <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Layers className="h-3 w-3" />
                          {order.batch_number}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-foreground">{order.recipe_name || "Ficha Técnica"}</div>
                      <div className="text-xs text-muted-foreground">{order.produced_sku_name}</div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {order.location_name || "Cozinha Central"}
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      {Number(order.planned_quantity).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {order.actual_quantity !== null && order.actual_quantity !== undefined ? (
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                          {Number(order.actual_quantity).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground">
                      {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(order.unit_cost) || 0)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-foreground">
                      {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(order.total_cost) || 0)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {order.status === "PLANNED" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-500 border border-blue-500/20">
                          Planejada
                        </span>
                      )}
                      {order.status === "IN_PRODUCTION" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20 animate-pulse">
                          Em Produção
                        </span>
                      )}
                      {order.status === "COMPLETED" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                          Concluída
                        </span>
                      )}
                      {order.status === "CANCELLED" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-500/10 text-gray-500 border border-gray-500/20">
                          Cancelada
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => setDetailOrder(order)}
                        className="px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground border rounded hover:bg-muted transition-colors"
                        title="Ver Insumos e Ficha"
                      >
                        Insumos
                      </button>

                      {order.status === "PLANNED" && (
                        <button
                          disabled={isSubmitting}
                          onClick={() => handleStartOrder(order.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded transition-colors"
                        >
                          <Play className="h-3 w-3" />
                          Iniciar
                        </button>
                      )}

                      {order.status === "IN_PRODUCTION" && (
                        <button
                          disabled={isSubmitting}
                          onClick={() => openCompleteModal(order)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded transition-colors"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Concluir Batelada
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: Criar Nova Ordem de Produção */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-lg rounded-2xl border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b flex items-center justify-between bg-muted/30">
              <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
                <Factory className="h-5 w-5 text-primary" />
                Nova Ordem de Produção (OP)
              </h3>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateOrder} className="p-5 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Ficha Técnica da Receita *</label>
                <select
                  required
                  value={selectedRecipeId}
                  onChange={(e) => setSelectedRecipeId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Selecione a ficha técnica...</option>
                  {recipes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">SKU do Item Semi-Acabado / Produzido *</label>
                <select
                  required
                  value={selectedSkuId}
                  onChange={(e) => setSelectedSkuId(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Selecione o SKU resultante...</option>
                  {skus.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Qtd Planejada / Rendimento *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="Ex: 10.00"
                    value={plannedQty}
                    onChange={(e) => setPlannedQty(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Número do Lote (Opcional)</label>
                  <input
                    type="text"
                    placeholder="Auto-gerado se vazio"
                    value={batchNumber}
                    onChange={(e) => setBatchNumber(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Data de Validade da Batelada</label>
                <input
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Observações da Batelada</label>
                <textarea
                  rows={2}
                  placeholder="Ex: Pré-preparo para o turno da noite..."
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground rounded-lg border hover:bg-muted transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg shadow transition-colors"
                >
                  {isSubmitting ? "Criando..." : "Gerar Ordem de Produção"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Concluir Batelada & Apontar Rendimento */}
      {isCompleteModalOpen && completingOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-md rounded-2xl border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b flex items-center justify-between bg-muted/30">
              <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-emerald-500" />
                Concluir Batelada {completingOrder.order_number}
              </h3>
              <button
                onClick={() => setIsCompleteModalOpen(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCompleteOrder} className="p-5 space-y-4">
              <div className="rounded-lg bg-muted/50 p-3 border text-xs space-y-1">
                <div className="text-muted-foreground">Produto Produzido:</div>
                <div className="font-semibold text-foreground text-sm">{completingOrder.produced_sku_name}</div>
                <div className="text-muted-foreground mt-1">
                  Quantidade Planejada: <strong>{Number(completingOrder.planned_quantity).toFixed(2)}</strong>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Rendimento Real Obtido (Qtd Produzida) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={actualQty}
                  onChange={(e) => setActualQty(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Identificação do Lote</label>
                <input
                  type="text"
                  value={completeBatchNumber}
                  onChange={(e) => setCompleteBatchNumber(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Data de Validade</label>
                <input
                  type="date"
                  value={completeExpDate}
                  onChange={(e) => setCompleteExpDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-600 dark:text-amber-400">
                Ao confirmar, o sistema dará baixa nos insumos consumidos e creditará o produto semi-acabado com custo unitário real recalculado no livro-razão de estoque.
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setIsCompleteModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground rounded-lg border hover:bg-muted transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow transition-colors"
                >
                  {isSubmitting ? "Postando..." : "Confirmar & Postar no Estoque"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Detalhes dos Insumos da OP */}
      {detailOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-xl rounded-2xl border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b flex items-center justify-between bg-muted/30">
              <div>
                <h3 className="font-semibold text-lg text-foreground">
                  Insumos da {detailOrder.order_number}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {detailOrder.recipe_name} → {detailOrder.produced_sku_name}
                </p>
              </div>
              <button
                onClick={() => setDetailOrder(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/50 uppercase font-semibold text-muted-foreground border-b">
                    <tr>
                      <th className="px-3 py-2">Insumo</th>
                      <th className="px-3 py-2 text-right">Qtd Prevista</th>
                      <th className="px-3 py-2 text-right">Custo Unitário</th>
                      <th className="px-3 py-2 text-right">Total Linha</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {detailOrder.ingredients && detailOrder.ingredients.length > 0 ? (
                      detailOrder.ingredients.map((ing) => (
                        <tr key={ing.id} className="hover:bg-muted/20">
                          <td className="px-3 py-2 font-medium text-foreground">{ing.sku_name}</td>
                          <td className="px-3 py-2 text-right font-semibold">
                            {Number(ing.planned_quantity).toFixed(3)}
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">
                            {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(ing.unit_cost))}
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-foreground">
                            {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(ing.total_cost))}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-3 py-4 text-center text-muted-foreground">
                          Nenhum insumo detalhado gravado.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between items-center bg-muted/40 p-3 rounded-lg border text-sm">
                <span className="font-semibold text-foreground">Custo Total Previsto da Batelada:</span>
                <span className="font-bold text-primary text-base">
                  {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(detailOrder.total_cost))}
                </span>
              </div>
            </div>

            <div className="p-4 border-t bg-muted/20 flex justify-end">
              <button
                onClick={() => setDetailOrder(null)}
                className="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-lg transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
