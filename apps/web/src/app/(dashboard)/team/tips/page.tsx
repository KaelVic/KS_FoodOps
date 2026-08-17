import { Metadata } from "next"
import { TipsClient } from "./TipsClient"

export const metadata: Metadata = {
  title: "Rateio de Gorjetas & Taxa de Serviço | KS FoodOps",
  description: "Apuração e Repasse de Gorjetas (Lei 13.419/2017)",
}

export const dynamic = "force-dynamic"

export default function TipsPage() {
  return (
    <div className="p-6 md:p-8">
      <TipsClient />
    </div>
  )
}
