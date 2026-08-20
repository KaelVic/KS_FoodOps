import { Suspense } from "react";
import { fetchProductionOrdersServer, fetchRecipesServer, fetchCatalogSkusAndUomsServer } from "@/lib/api-server";
import { ProductionOrdersClient } from "./ProductionOrdersClient";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Ordens de Produção & Commissary | KS FoodOps",
  description: "Gestão de Ordens de Produção (OPs), Bateladas de Semi-Acabados e Rendimentos",
};

export default async function ProductionOrdersPage() {
  const [orders, recipes, catalog] = await Promise.all([
    fetchProductionOrdersServer(),
    fetchRecipesServer(),
    fetchCatalogSkusAndUomsServer(),
  ]);

  return (
    <div className="space-y-6">
      <Suspense fallback={<div className="p-8 text-center text-muted-foreground animate-pulse">Carregando ordens de produção...</div>}>
        <ProductionOrdersClient
          initialOrders={orders}
          recipes={recipes}
          skus={catalog.skus}
        />
      </Suspense>
    </div>
  );
}
