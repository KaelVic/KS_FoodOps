import { fetchLocationsServer, fetchSuppliersServer, fetchCatalogSkusAndUomsServer } from "@/lib/api-server"
import { NewRFQClient } from "./NewRFQClient"

export const dynamic = "force-dynamic"

export default async function NewRFQPage() {
  const [locations, suppliers, catalog] = await Promise.all([
    fetchLocationsServer(),
    fetchSuppliersServer(),
    fetchCatalogSkusAndUomsServer()
  ])

  return (
    <div className="p-6 md:p-8">
      <NewRFQClient locations={locations} suppliers={suppliers} catalog={catalog} />
    </div>
  )
}
