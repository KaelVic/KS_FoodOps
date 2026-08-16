import { fetchTheoreticalVsActualServer } from "@/lib/api-server"
import VarianceClient from "./VarianceClient"

export const dynamic = "force-dynamic"

export default async function VariancePage() {
  const varianceData = await fetchTheoreticalVsActualServer()

  return <VarianceClient initialData={varianceData} />
}
