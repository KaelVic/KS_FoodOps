"use client"

import { useRef } from "react"
import { Printer, ChefHat, Scale, Clock, AlertCircle } from "lucide-react"
import { RecipeDetailItem } from "@/types/recipes"

interface RecipeKitchenSheetProps {
  recipe: RecipeDetailItem
  onClose: () => void
}

export function RecipeKitchenSheet({ recipe, onClose }: RecipeKitchenSheetProps) {
  const printRef = useRef<HTMLDivElement>(null)

  const handlePrint = () => {
    // In a real app we could use react-to-print or a custom print stylesheet
    // For now, we trigger window.print() and hide other elements via CSS class if needed
    window.print()
  }

  // Calculate total gross weight from ingredients
  const totalGrossWeight = recipe.ingredients.reduce((sum, ing) => sum + ing.quantity, 0)
  
  // Simulated preparation time and instructions for demo
  const prepTime = "45 min"
  const instructions = [
    "Higienizar todos os vegetais e mise en place.",
    "Cortar os ingredientes conforme o padrão estabelecido na ficha.",
    "Aquecer a base de molho em fogo brando (se aplicável).",
    "Adicionar os ingredientes principais e cozinhar até atingir o ponto.",
    "Resfriar rapidamente ou manter aquecido na praça de serviço."
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-50 w-full max-w-3xl rounded-xl shadow-2xl relative text-slate-900 my-8">
        
        {/* Actions (Not Printed) */}
        <div className="absolute top-4 right-4 flex items-center gap-2 print:hidden">
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Printer className="h-4 w-4" />
            <span className="font-medium text-sm">Imprimir</span>
          </button>
          <button
            onClick={onClose}
            className="p-2 text-slate-500 hover:text-slate-700 bg-slate-200 hover:bg-slate-300 rounded-lg transition-colors"
          >
            Fechar
          </button>
        </div>

        {/* Printable Area */}
        <div ref={printRef} className="p-10 print:p-0">
          <div className="border-b-2 border-slate-900 pb-6 mb-6">
            <div className="flex items-center gap-3 text-slate-900 mb-2">
              <ChefHat className="h-8 w-8" />
              <h1 className="text-3xl font-bold uppercase tracking-tight">{recipe.name}</h1>
            </div>
            <div className="flex items-center gap-6 text-slate-600 font-medium">
              <span>Cód: {recipe.pos_code || "N/A"}</span>
              <span>•</span>
              <span>Tipo: {recipe.type === "MENU_ITEM" ? "Prato de Menu" : "Pré-Preparo / Base"}</span>
              <span>•</span>
              <span>Versão: v{recipe.version_number || 1}</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="bg-slate-200/50 p-4 rounded-lg border border-slate-300">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <Scale className="h-4 w-4" />
                <span className="text-sm font-bold uppercase">Rendimento</span>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {recipe.yield_quantity || 1} <span className="text-base font-normal text-slate-600">porções</span>
              </p>
            </div>
            <div className="bg-slate-200/50 p-4 rounded-lg border border-slate-300">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <Scale className="h-4 w-4" />
                <span className="text-sm font-bold uppercase">Tam. Porção</span>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {recipe.portion_size || 1}
              </p>
            </div>
            <div className="bg-slate-200/50 p-4 rounded-lg border border-slate-300">
              <div className="flex items-center gap-2 text-slate-500 mb-1">
                <Clock className="h-4 w-4" />
                <span className="text-sm font-bold uppercase">Tempo Prep.</span>
              </div>
              <p className="text-2xl font-bold text-slate-900">
                {prepTime}
              </p>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-xl font-bold border-b border-slate-300 pb-2 mb-4 uppercase">
              Ingredientes & Gramaturas
            </h2>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-800 text-white">
                  <th className="py-3 px-4 font-bold uppercase text-sm">Ingrediente</th>
                  <th className="py-3 px-4 font-bold uppercase text-sm w-32 text-right">Qtde Líquida</th>
                  <th className="py-3 px-4 font-bold uppercase text-sm w-32 text-right">Qtde Bruta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-300">
                {recipe.ingredients.map((ing, idx) => {
                  // Net quantity is what goes into the plate. Gross is what is taken from inventory (factoring loss).
                  // quantity stored is usually gross in inventory systems, or we can treat `ing.quantity` as net and apply loss to find gross.
                  // For this view, we'll assume `ing.quantity` is gross (what the chef needs to pick up),
                  // and net is after loss.
                  const lossFactor = ing.loss_percentage / 100
                  const netQuantity = ing.quantity * (1 - lossFactor)

                  return (
                    <tr key={idx} className="hover:bg-slate-100">
                      <td className="py-3 px-4 font-medium text-slate-900">{ing.sku_name}</td>
                      <td className="py-3 px-4 text-right tabular-nums">
                        {netQuantity.toFixed(3)} {ing.uom_symbol}
                      </td>
                      <td className="py-3 px-4 text-right font-bold tabular-nums">
                        {ing.quantity.toFixed(3)} {ing.uom_symbol}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot className="bg-slate-200">
                <tr>
                  <td className="py-3 px-4 font-bold text-right uppercase text-sm">Peso Total Bruto:</td>
                  <td colSpan={2} className="py-3 px-4 font-bold text-right tabular-nums">
                    {totalGrossWeight.toFixed(3)}
                  </td>
                </tr>
              </tfoot>
            </table>
            {recipe.ingredients.some(i => i.loss_percentage > 0) && (
               <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                 <AlertCircle className="h-3 w-3" />
                 Qtde Bruta inclui fatores de correção (perdas de limpeza/cocção). Use a Qtde Bruta para separação.
               </p>
            )}
          </div>

          <div>
            <h2 className="text-xl font-bold border-b border-slate-300 pb-2 mb-4 uppercase">
              Modo de Preparo
            </h2>
            <ol className="list-decimal list-outside ml-5 space-y-3 text-slate-800 text-lg">
              {instructions.map((step, idx) => (
                <li key={idx} className="pl-2 leading-relaxed">{step}</li>
              ))}
            </ol>
          </div>
          
          <div className="mt-12 pt-6 border-t border-slate-300 text-center text-slate-500 text-sm">
            Ficha Técnica Operacional Interna - Emitida em {new Date().toLocaleDateString('pt-BR')}
          </div>
        </div>
      </div>
      
      {/* Print styles */}
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          body * {
            visibility: hidden;
          }
          .fixed {
            position: absolute !important;
            inset: auto !important;
            display: block !important;
            background: white !important;
            padding: 0 !important;
          }
          .bg-slate-50 {
            box-shadow: none !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
          }
          .print\\:hidden {
            display: none !important;
          }
          .print\\:p-0 {
            padding: 0 !important;
            visibility: visible !important;
          }
          .print\\:p-0 * {
            visibility: visible !important;
          }
        }
      `}} />
    </div>
  )
}
