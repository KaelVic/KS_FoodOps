import { notFound } from "next/navigation"
import { fetchRFQDetailsServer, fetchRFQComparisonServer, fetchSuppliersServer } from "@/lib/api-server"
import { RFQDetailClient } from "./RFQDetailClient"

export const dynamic = "force-dynamic"

interface RFQPageProps {
  params: Promise<{
    id: string
  }>
}

export default async function RFQDetailPage({ params }: RFQPageProps) {
  const { id } = await params

  const [rfq, comparison, suppliers] = await Promise.all([
    fetchRFQDetailsServer(id),
    fetchRFQComparisonServer(id),
    fetchSuppliersServer()
  ])

  if (!rfq) {
    notFound()
  }

  return (
    <div className="p-6 md:p-8">
      <RFQDetailClient
        rfq={rfq}
        initialComparison={comparison}
        allSuppliers={suppliers}
      />
    </div>
  )
}
