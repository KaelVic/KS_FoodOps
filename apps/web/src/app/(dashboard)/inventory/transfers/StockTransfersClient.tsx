"use client";

import { useState } from "react";
import { 
  ArrowLeftRight, 
  Plus, 
  Send, 
  CheckCircle, 
  Clock, 
  Truck, 
  Trash2, 
  Package,
  Layers,
  MapPin
} from "lucide-react";
import { StockTransfer } from "@/types/inventory";
import { 
  createStockTransferClient, 
  dispatchStockTransferClient, 
  receiveStockTransferClient 
} from "@/lib/api-client";

interface Props {
  initialTransfers: StockTransfer[];
  skus: { id: string; name: string }[];
}

export function StockTransfersClient({ initialTransfers, skus }: Props) {
  const [transfers, setTransfers] = useState<StockTransfer[]>(initialTransfers);
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
  const [originLocationId, setOriginLocationId] = useState("");
  const [destinationLocationId, setDestinationLocationId] = useState("");
  const [transferNotes, setTransferNotes] = useState("");
  const [items, setItems] = useState<{ sku_id: string; quantity_sent: string }[]>([
    { sku_id: "", quantity_sent: "1" }
  ]);

  // Detail Modal State
  const [detailTransfer, setDetailTransfer] = useState<StockTransfer | null>(null);

  // KPIs
  const inTransitCount = transfers.filter((t) => t.status === "IN_TRANSIT").length;
  const draftCount = transfers.filter((t) => t.status === "DRAFT").length;
  const receivedCount = transfers.filter((t) => t.status === "RECEIVED").length;

  const filteredTransfers = transfers.filter((t) => {
    const matchesStatus = filterStatus === "ALL" || t.status === filterStatus;
    const matchesSearch = 
      t.transfer_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (t.origin_location_name && t.origin_location_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (t.destination_location_name && t.destination_location_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  const addItemRow = () => {
    setItems([...items, { sku_id: "", quantity_sent: "1" }]);
  };

  const removeItemRow = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const updateItemRow = (index: number, field: "sku_id" | "quantity_sent", value: string) => {
    const next = [...items];
    next[index][field] = value;
    setItems(next);
  };

  const handleCreateTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    const validItems = items.filter((i) => i.sku_id && Number(i.quantity_sent) > 0);
    if (validItems.length === 0) {
      showToast("error", "Adicione ao menos um insumo para transferir.");
      return;
    }

    // Default IDs if not specified
    const orig = originLocationId || "00000000-0000-0000-0000-000000000001";
    const dest = destinationLocationId || "00000000-0000-0000-0000-000000000002";

    try {
      setIsSubmitting(true);
      const newTrf = await createStockTransferClient({
        origin_location_id: orig,
        destination_location_id: dest,
        items: validItems.map((i) => ({
          sku_id: i.sku_id,
          quantity_sent: Number(i.quantity_sent),
        })),
        notes: transferNotes || undefined,
      });

      setTransfers([newTrf, ...transfers]);
      setIsCreateModalOpen(false);
      setOriginLocationId("");
      setDestinationLocationId("");
      setTransferNotes("");
      setItems([{ sku_id: "", quantity_sent: "1" }]);
      showToast("success", `Transferência ${newTrf.transfer_number} criada em Rascunho!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao criar transferência.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDispatch = async (transferId: string) => {
    try {
      setIsSubmitting(true);
      const updated = await dispatchStockTransferClient(transferId);
      setTransfers(transfers.map((t) => (t.id === transferId ? updated : t)));
      showToast("success", `Transferência ${updated.transfer_number} despachada (Em Trânsito)!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao despachar transferência.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReceive = async (transferId: string) => {
    try {
      setIsSubmitting(true);
      const updated = await receiveStockTransferClient(transferId);
      setTransfers(transfers.map((t) => (t.id === transferId ? updated : t)));
      showToast("success", `Transferência ${updated.transfer_number} recebida e estoque atualizado nos dois locais!`);
    } catch (err: any) {
      showToast("error", err.message || "Erro ao receber transferência.");
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
            <ArrowLeftRight className="h-7 w-7 text-primary" />
            Transferências entre Locais & Estoques
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Controle de remessas e transferências de insumos e semi-acabados entre Cozinha Central, Depósito e Lojas.
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-primary-foreground bg-primary hover:bg-primary/90 rounded-lg shadow transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nova Transferência
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Em Trânsito</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
              <Truck className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">{inTransitCount}</div>
          <p className="text-xs text-muted-foreground">Aguardando recebimento no destino</p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Rascunhos / Pendentes</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
              <Clock className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">{draftCount}</div>
          <p className="text-xs text-muted-foreground">Prontos para separação e despacho</p>
        </div>

        <div className="rounded-xl border bg-card p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Concluídas / Recebidas</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
              <CheckCircle className="h-5 w-5" />
            </div>
          </div>
          <div className="text-2xl font-bold tracking-tight text-foreground">{receivedCount}</div>
          <p className="text-xs text-muted-foreground">Estoque debitado na origem e creditado no destino</p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-card p-4 rounded-xl border">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          {(["ALL", "DRAFT", "IN_TRANSIT", "RECEIVED"] as const).map((st) => (
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
              {st === "DRAFT" && "Rascunho"}
              {st === "IN_TRANSIT" && "Em Trânsito"}
              {st === "RECEIVED" && "Recebidas"}
            </button>
          ))}
        </div>

        <div className="w-full sm:w-72">
          <input
            type="text"
            placeholder="Buscar por número ou local..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-1.5 text-sm rounded-lg border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 text-xs font-semibold text-muted-foreground uppercase border-b">
              <tr>
                <th className="px-4 py-3">Número</th>
                <th className="px-4 py-3">Origem → Destino</th>
                <th className="px-4 py-3 text-center">Itens</th>
                <th className="px-4 py-3">Despacho</th>
                <th className="px-4 py-3">Recebimento</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredTransfers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Nenhuma transferência encontrada.
                  </td>
                </tr>
              ) : (
                filteredTransfers.map((trf) => (
                  <tr key={trf.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-foreground">
                      {trf.transfer_number}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                        <span className="text-muted-foreground">{trf.origin_location_name || "Origem"}</span>
                        <span>→</span>
                        <span className="text-primary font-semibold">{trf.destination_location_name || "Destino"}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-muted font-medium text-muted-foreground">
                        {trf.items ? trf.items.length : trf.items_count || 1} itens
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {trf.dispatched_at ? new Date(trf.dispatched_at).toLocaleString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {trf.received_at ? new Date(trf.received_at).toLocaleString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {trf.status === "DRAFT" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-500 border border-blue-500/20">
                          Rascunho
                        </span>
                      )}
                      {trf.status === "IN_TRANSIT" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20 animate-pulse">
                          Em Trânsito
                        </span>
                      )}
                      {trf.status === "RECEIVED" && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                          Recebida
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button
                        onClick={() => setDetailTransfer(trf)}
                        className="px-2 py-1 text-xs font-medium text-muted-foreground hover:text-foreground border rounded hover:bg-muted transition-colors"
                      >
                        Ver Itens
                      </button>

                      {trf.status === "DRAFT" && (
                        <button
                          disabled={isSubmitting}
                          onClick={() => handleDispatch(trf.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded transition-colors"
                        >
                          <Send className="h-3 w-3" />
                          Despachar
                        </button>
                      )}

                      {trf.status === "IN_TRANSIT" && (
                        <button
                          disabled={isSubmitting}
                          onClick={() => handleReceive(trf.id)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded transition-colors"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Receber Carga
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

      {/* MODAL: Nova Transferência */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-xl rounded-2xl border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b flex items-center justify-between bg-muted/30">
              <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
                <ArrowLeftRight className="h-5 w-5 text-primary" />
                Nova Transferência de Estoque
              </h3>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTransfer} className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Local de Origem</label>
                  <input
                    type="text"
                    placeholder="Depósito / Cozinha Central"
                    value={originLocationId}
                    onChange={(e) => setOriginLocationId(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Local de Destino</label>
                  <input
                    type="text"
                    placeholder="Loja / Salão / Ponto de Venda"
                    value={destinationLocationId}
                    onChange={(e) => setDestinationLocationId(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              {/* Itens list */}
              <div className="space-y-2 pt-2 border-t">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-muted-foreground">Insumos & Quantidades *</label>
                  <button
                    type="button"
                    onClick={addItemRow}
                    className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    Adicionar Item
                  </button>
                </div>

                <div className="space-y-2">
                  {items.map((it, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <select
                        required
                        value={it.sku_id}
                        onChange={(e) => updateItemRow(idx, "sku_id", e.target.value)}
                        className="flex-1 px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:ring-2 focus:ring-primary/20"
                      >
                        <option value="">Selecione o insumo / produto...</option>
                        {skus.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>

                      <input
                        type="number"
                        step="0.01"
                        required
                        placeholder="Qtd"
                        value={it.quantity_sent}
                        onChange={(e) => updateItemRow(idx, "quantity_sent", e.target.value)}
                        className="w-24 px-3 py-2 text-sm rounded-lg border bg-background text-foreground text-right focus:ring-2 focus:ring-primary/20"
                      />

                      {items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItemRow(idx)}
                          className="p-2 text-muted-foreground hover:text-red-500 rounded-lg hover:bg-muted"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Observações / Motivo da Transferência</label>
                <textarea
                  rows={2}
                  placeholder="Ex: Abastecimento de fim de semana..."
                  value={transferNotes}
                  onChange={(e) => setTransferNotes(e.target.value)}
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
                  {isSubmitting ? "Criando..." : "Criar Transferência"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Ver Itens da Transferência */}
      {detailTransfer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-lg rounded-2xl border shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-5 border-b flex items-center justify-between bg-muted/30">
              <div>
                <h3 className="font-semibold text-lg text-foreground">
                  Itens da {detailTransfer.transfer_number}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {detailTransfer.origin_location_name} → {detailTransfer.destination_location_name}
                </p>
              </div>
              <button
                onClick={() => setDetailTransfer(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/50 uppercase font-semibold text-muted-foreground border-b">
                    <tr>
                      <th className="px-3 py-2">Item / SKU</th>
                      <th className="px-3 py-2 text-right">Qtd Enviada</th>
                      <th className="px-3 py-2 text-right">Qtd Recebida</th>
                      <th className="px-3 py-2 text-right">Custo Médio</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {detailTransfer.items && detailTransfer.items.length > 0 ? (
                      detailTransfer.items.map((it) => (
                        <tr key={it.id} className="hover:bg-muted/20">
                          <td className="px-3 py-2 font-medium text-foreground">{it.sku_name}</td>
                          <td className="px-3 py-2 text-right font-semibold">
                            {Number(it.quantity_sent).toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-right">
                            {it.quantity_received !== null && it.quantity_received !== undefined ? (
                              <span className="font-semibold text-emerald-600">
                                {Number(it.quantity_received).toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>
                          <td className="px-3 py-2 text-right text-muted-foreground">
                            {new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(it.unit_cost) || 0)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-3 py-4 text-center text-muted-foreground">
                          Nenhum item detalhado disponível.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-4 border-t bg-muted/20 flex justify-end">
              <button
                onClick={() => setDetailTransfer(null)}
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
