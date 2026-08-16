import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

class ReportExporter:
    """
    Utility for exporting financial and inventory reports to tabular and accounting formats.
    """
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], fieldnames: List[str], headers_map: Optional[Dict[str, str]] = None) -> str:
        """
        Exports a list of dictionaries to a CSV string with optional human-readable headers.
        """
        if not data:
            return ""
            
        output = io.StringIO()
        
        # If headers map is provided, write custom human-friendly headers
        if headers_map:
            display_headers = [headers_map.get(f, f) for f in fieldnames]
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow(display_headers)
            
            for row in data:
                formatted_row = [str(row.get(f, '')) for f in fieldnames]
                writer.writerow(formatted_row)
        else:
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            for row in data:
                formatted_row = {k: str(v) for k, v in row.items() if k in fieldnames}
                writer.writerow(formatted_row)
            
        return output.getvalue()

    @staticmethod
    def export_inventory_valuation_csv(items: List[Dict[str, Any]]) -> str:
        """
        Generates standard Portuguese Excel-compatible CSV for Inventory Valuation.
        """
        fieldnames = ["sku_id", "sku_name", "category_name", "uom_symbol", "total_quantity", "unit_cost", "total_value"]
        headers_map = {
            "sku_id": "Codigo_SKU",
            "sku_name": "Insumo",
            "category_name": "Categoria",
            "uom_symbol": "Unidade",
            "total_quantity": "Quantidade_Estoque",
            "unit_cost": "Custo_Unitario_Medio_R$",
            "total_value": "Valor_Total_Estoque_R$"
        }
        
        # Format decimals nicely for financial spreadsheets (2 decimal places for money, 3 for quantities)
        formatted_items = []
        for it in items:
            qty = Decimal(str(it.get("total_quantity", 0)))
            cost = Decimal(str(it.get("unit_cost", 0)))
            val = Decimal(str(it.get("total_value", 0)))
            formatted_items.append({
                "sku_id": it.get("sku_id", ""),
                "sku_name": it.get("sku_name", ""),
                "category_name": it.get("category_name", ""),
                "uom_symbol": it.get("uom_symbol", ""),
                "total_quantity": f"{qty:.3f}",
                "unit_cost": f"{cost:.4f}",
                "total_value": f"{val:.2f}"
            })
            
        return ReportExporter.export_to_csv(formatted_items, fieldnames, headers_map)

    @staticmethod
    def export_to_sped_bloco_h(items: List[Dict[str, Any]], inventory_date: Optional[datetime] = None) -> str:
        """
        Generates standard SPED Fiscal Bloco H (Inventário Físico/Financeiro).
        Conforme Guia Prático da EFD-ICMS/IPI.
        """
        inv_dt = (inventory_date or datetime.now()).strftime("%d%m%Y")
        lines = []
        
        # Registro H001: Abertura do Bloco H (0 = Bloco com dados informados)
        lines.append("|H001|0|")
        
        total_inventario = Decimal('0')
        h010_records = []
        
        for item in items:
            qty = Decimal(str(item.get("total_quantity", 0)))
            val = Decimal(str(item.get("total_value", 0)))
            
            if qty <= Decimal('0') or val <= Decimal('0'):
                continue
                
            unit_cost = val / qty
            total_inventario += val
            
            cod_item = str(item.get("sku_id", ""))[:60]
            unid = str(item.get("uom_symbol", "UN"))[:6]
            qtd_str = f"{qty:.3f}".replace('.', ',')
            vl_unit_str = f"{unit_cost:.6f}".replace('.', ',')
            vl_item_str = f"{val:.2f}".replace('.', ',')
            
            # |H010|COD_ITEM|UNID|QTD|VL_UNIT|VL_ITEM|IND_PROP|COD_PART|TXT_COMPL|COD_CTA|VL_ITEM_IR|
            # IND_PROP: 0 = Item de propriedade do informante e em seu poder
            h010_line = f"|H010|{cod_item}|{unid}|{qtd_str}|{vl_unit_str}|{vl_item_str}|0|||||"
            h010_records.append(h010_line)
            
        # Registro H005: Totais do Inventário
        # |H005|DT_INV|VL_INV|MOT_INV|
        # MOT_INV: 01 = No encerramento do exercício
        vl_inv_str = f"{total_inventario:.2f}".replace('.', ',')
        lines.append(f"|H005|{inv_dt}|{vl_inv_str}|01|")
        
        lines.extend(h010_records)
        
        # Registro H990: Encerramento do Bloco H (contando H001, H005, H010s e o próprio H990)
        qtd_linhas_h = len(lines) + 1
        lines.append(f"|H990|{qtd_linhas_h}|")
        
        return "\r\n".join(lines) + "\r\n"
