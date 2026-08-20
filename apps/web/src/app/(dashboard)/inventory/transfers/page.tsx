import { Suspense } from "react";
import { fetchStockTransfersServer, fetchCatalogSkusAndUomsServer } from "@/lib/api-server";
import { StockTransfersClient } from "./StockTransfersClient";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Transferências entre Locais & Estoques | KS FoodOps",
  description: "Movimentação e transferências de mercadorias entre Matriz, Filiais, Cozinha Central e Pontos de Venda",
};

export default async function StockTransfersPage() {
  const [transfers, catalog] = await Promise.all([
    fetchStockTransfersServer(),
    fetchCatalogSkusAndUomsServer(),
  ]);

  return (
    <div className="space-y-6">
      <Suspense fallback={<div className="p-8 text-center text-muted-foreground animate-pulse">Carregando transferências...</div>}>
        <StockTransfersClient
          initialTransfers={transfers}
          skus={catalog.skus}
        />
      </Suspense>
    </div>
  );
}
