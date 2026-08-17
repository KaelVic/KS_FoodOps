import { fetchRFQsServer } from "@/lib/api-server"
import { RFQsClient } from "./RFQsClient"

export const dynamic = "force-dynamic"

export default async function RFQsPage() {
  const rfqs = await fetchRFQsServer()

  return (
    <div className="p-6 md:p-8">
      <RFQsClient initialRfqs={rfqs} />
    </div>
  )
}

