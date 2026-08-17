import json
import uuid
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from modules.intelligence.models import (
    CopilotConversation, CopilotMessage, ExecutiveBriefing, InventoryPolicy, OperationalAlert
)
from modules.financial.models import ReceivableInvoice, PayableBill
from modules.sales.models import SaleLine
from modules.inventory.models import StockBalanceProjection, StockLedgerEntry
from modules.catalog.models import SKU
from modules.menu.models import MenuItem
from modules.production.models import ProductionOrder
from modules.orders.models import Order
from modules.team.labor_service import LaborService


class CopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tenant_context_rag(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Synthesizes real-time operational metrics across Sales, Financials, Inventory, Labor and Menu.
        """
        labor_service = LaborService(self.db)
        prime_cost_data = await labor_service.get_prime_cost_analysis(tenant_id)

        from modules.catalog.models import UOM
        # 1. Critical Inventory Stockouts
        stock_stmt = (
            select(SKU.name, UOM.symbol, StockBalanceProjection.quantity, InventoryPolicy.min_stock, InventoryPolicy.abc_class)
            .join(StockBalanceProjection, SKU.id == StockBalanceProjection.sku_id)
            .join(UOM, SKU.base_uom_id == UOM.id)
            .outerjoin(InventoryPolicy, (InventoryPolicy.sku_id == SKU.id) & (InventoryPolicy.tenant_id == tenant_id))
            .where(StockBalanceProjection.tenant_id == tenant_id)
        )


        stock_rows = (await self.db.execute(stock_stmt)).all()
        
        critical_skus = []
        for name, uom, balance, min_stock, abc in stock_rows:
            bal_num = float(balance or 0)
            min_num = float(min_stock or 0)
            if min_num > 0 and bal_num <= min_num:
                critical_skus.append({
                    "name": name,
                    "unit": uom,
                    "balance": bal_num,
                    "min_stock": min_num,
                    "abc_class": abc or "B"
                })

        # 2. Menu Dogs / Underperforming items
        menu_stmt = select(MenuItem).where(MenuItem.tenant_id == tenant_id, MenuItem.is_active == True)
        menu_items = (await self.db.execute(menu_stmt)).scalars().all()
        
        # 3. Active Production Orders
        op_stmt = select(ProductionOrder).where(ProductionOrder.tenant_id == tenant_id, ProductionOrder.status.in_(["PLANNED", "IN_PRODUCTION"]))
        active_ops = (await self.db.execute(op_stmt)).scalars().all()

        # 4. Pending / Preparing Orders in KDS
        kds_stmt = select(Order).where(Order.tenant_id == tenant_id, Order.status.in_(["RECEIVED", "PREPARING"]))
        kds_orders = (await self.db.execute(kds_stmt)).scalars().all()

        return {
            "prime_cost": prime_cost_data,
            "critical_stock_count": len(critical_skus),
            "critical_skus": critical_skus[:5],
            "active_menu_items": len(menu_items),
            "active_production_orders": len(active_ops),
            "kds_in_flight_orders": len(kds_orders)
        }

    async def audit_restaurant_360(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Runs a 360-degree diagnostic audit on restaurant operations with actionable insights.
        """
        rag = await self.get_tenant_context_rag(tenant_id)
        pc = rag["prime_cost"]

        diagnostics = []

        # Prime cost audit
        pc_pct = float(pc.get("prime_cost_percentage", 0))
        if pc_pct > 68.0:
            diagnostics.append({
                "pillar": "FINANCEIRO & PRIME COST",
                "severity": "CRITICAL",
                "title": "Prime Cost em Nível Crítico (> 68%)",
                "detail": f"O Prime Cost atual está em {pc_pct:.1f}% da receita líquida. A margem de contribuição residual está insuficiente para cobrir Opex e gerar lucro líquido.",
                "action": "Auditar ficha técnica dos 5 pratos mais vendidos e revisar escala de folga/turnos do salão e cozinha."
            })
        elif pc_pct > 65.0:
            diagnostics.append({
                "pillar": "FINANCEIRO & PRIME COST",
                "severity": "WARNING",
                "title": "Prime Cost Acima da Meta Saudável (65% a 68%)",
                "detail": f"Prime Cost apurado em {pc_pct:.1f}%. Recomendável ajustar preços de venda ou negociar insumos Classe A.",
                "action": "Abrir cotação B2B (RFQ) para proteínas e laticínios a fim de reduzir o CMV em 2 a 3 pontos percentuais."
            })
        else:
            diagnostics.append({
                "pillar": "FINANCEIRO & PRIME COST",
                "severity": "HEALTHY",
                "title": "Prime Cost em Nível Saudável",
                "detail": f"Prime Cost em {pc_pct:.1f}%, dentro dos padrões de excelência operacional do food-service.",
                "action": "Manter disciplina de compras e controle diário de sobras e desperdício."
            })

        # Inventory audit
        if rag["critical_stock_count"] > 0:
            crit_names = ", ".join([s["name"] for s in rag["critical_skus"][:3]])
            diagnostics.append({
                "pillar": "ESTOQUE & SUPRIMENTOS",
                "severity": "WARNING" if rag["critical_stock_count"] <= 3 else "CRITICAL",
                "title": f"{rag['critical_stock_count']} Insumo(s) com Risco Iminente de Ruptura",
                "detail": f"Itens abaixo do estoque de segurança: {crit_names}.",
                "action": "Emitir Pedido de Compra de emergência ou acionar fornecedores homologados via RFQ."
            })
        else:
            diagnostics.append({
                "pillar": "ESTOQUE & SUPRIMENTOS",
                "severity": "HEALTHY",
                "title": "Níveis de Estoque Estáveis",
                "detail": "Nenhum insumo chave operando abaixo do ponto de ressuprimento.",
                "action": "Prosseguir com rotina padrão de inventário semanal."
            })

        # KDS & Production audit
        if rag["kds_in_flight_orders"] > 15:
            diagnostics.append({
                "pillar": "OPERAÇÃO & COZINHA",
                "severity": "WARNING",
                "title": f"Cozinha Sob Alta Carga ({rag['kds_in_flight_orders']} pedidos em preparo)",
                "detail": "Risco de estouro no tempo padrão de entrega (SLA) de pratos.",
                "action": "Realocar cumins para apoio na expedição de pratos ou pausar temporariamente canais de delivery com maior tempo de preparo."
            })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": "EXCELLENT" if pc_pct < 55 else ("HEALTHY" if pc_pct <= 65 else ("WARNING" if pc_pct <= 68 else "CRITICAL")),
            "prime_cost_percentage": pc_pct,
            "net_revenue": float(pc.get("net_revenue", 0)),
            "food_cost_cmv": float(pc.get("food_cost_cmv", 0)),
            "labor_cost_cmo": float(pc.get("total_labor_cost_cmo", 0)),
            "diagnostics": diagnostics
        }

    async def generate_executive_briefing(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Generates a daily executive summary formatted for instant WhatsApp/Slack/Webhook delivery.
        """
        rag = await self.get_tenant_context_rag(tenant_id)
        pc = rag["prime_cost"]
        today_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")

        revenue = float(pc.get("net_revenue", 0))
        cmv_val = float(pc.get("food_cost_cmv", 0))
        cmv_pct = float(pc.get("cmv_percentage", 0))
        cmo_val = float(pc.get("total_labor_cost_cmo", 0))
        cmo_pct = float(pc.get("cmo_percentage", 0))
        pc_val = float(pc.get("prime_cost_amount", 0))
        pc_pct = float(pc.get("prime_cost_percentage", 0))

        # Format WhatsApp ready text with Markdown/Bold
        whatsapp_msg = (
            f"📊 *RESUMO EXECUTIVO DIÁRIO — KS FOODOPS*\n"
            f"📅 *Data:* {today_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Receita Líquida:* R$ {revenue:,.2f}\n"
            f"🍽️ *CMV Real (Insumos):* R$ {cmv_val:,.2f} ({cmv_pct:.1f}%)\n"
            f"👥 *CMO Real (Pessoal):* R$ {cmo_val:,.2f} ({cmo_pct:.1f}%)\n"
            f"🔥 *PRIME COST (CMV+CMO):* R$ {pc_val:,.2f} (*{pc_pct:.1f}%*)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 *Status de Estoque:* {rag['critical_stock_count']} itens em nível de alerta\n"
            f"👨‍🍳 *Ordens de Produção Ativas:* {rag['active_production_orders']} lotes\n"
            f"🛎️ *Pedidos em Andamento (KDS):* {rag['kds_in_flight_orders']} comandas\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Diretriz do Copilot:* "
            + ("Manter operação com foco em giro dos itens mais rentáveis." if pc_pct <= 65 else "Atenção ao Prime Cost elevado: auditar porcionamento e perdas da cozinha.")
            + "\n_Gerado automaticamente pelo FoodOps Copilot IA_"
        )

        briefing = ExecutiveBriefing(
            tenant_id=tenant_id,
            briefing_date=datetime.now(timezone.utc),
            channel="DASHBOARD",
            status="GENERATED",
            summary_text=whatsapp_msg,
            metrics_payload=json.dumps({
                "revenue": revenue,
                "cmv_percentage": cmv_pct,
                "cmo_percentage": cmo_pct,
                "prime_cost_percentage": pc_pct,
                "critical_stock_count": rag["critical_stock_count"]
            })
        )
        self.db.add(briefing)
        await self.db.commit()

        return {
            "id": str(briefing.id),
            "date": today_str,
            "summary_text": whatsapp_msg,
            "metrics": {
                "revenue": revenue,
                "cmv_percentage": cmv_pct,
                "cmo_percentage": cmo_pct,
                "prime_cost_percentage": pc_pct,
                "critical_stock_count": rag["critical_stock_count"]
            }
        }

    async def process_user_message(
        self,
        tenant_id: UUID,
        user_id: Optional[UUID],
        conversation_id: Optional[UUID],
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        RAG AI message handler for interactive management dialogue.
        """
        # 1. Get or create conversation
        if conversation_id:
            conv_stmt = select(CopilotConversation).where(
                CopilotConversation.id == conversation_id,
                CopilotConversation.tenant_id == tenant_id
            )
            conv = (await self.db.execute(conv_stmt)).scalar_one_or_none()
            if not conv:
                conv = CopilotConversation(tenant_id=tenant_id, user_id=user_id, title=user_prompt[:50])
                self.db.add(conv)
                await self.db.flush()
        else:
            conv = CopilotConversation(tenant_id=tenant_id, user_id=user_id, title=user_prompt[:50])
            self.db.add(conv)
            await self.db.flush()

        # 2. Save user message
        user_msg = CopilotMessage(
            tenant_id=tenant_id,
            conversation_id=conv.id,
            sender="USER",
            content=user_prompt,
            intent="GENERAL"
        )
        self.db.add(user_msg)

        # 3. Analyze intent and pull RAG context
        prompt_lower = user_prompt.lower()
        rag = await self.get_tenant_context_rag(tenant_id)
        pc = rag["prime_cost"]

        intent = "GENERAL"
        reply_content = ""

        if "prime cost" in prompt_lower or "cmo" in prompt_lower or "mão de obra" in prompt_lower:
            intent = "PRIME_COST"
            pc_pct = float(pc.get("prime_cost_percentage", 0))
            cmv_pct = float(pc.get("cmv_percentage", 0))
            cmo_pct = float(pc.get("cmo_percentage", 0))
            reply_content = (
                f"### 📊 Diagnóstico de Prime Cost (CMV + CMO)\n\n"
                f"O seu **Prime Cost Real** apurado no período é de **{pc_pct:.1f}%** da Receita Líquida.\n\n"
                f"- **CMV Real (Food Cost):** R$ {float(pc.get('food_cost_cmv', 0)):,.2f} ({cmv_pct:.1f}%)\n"
                f"- **CMO Real (Labor Cost):** R$ {float(pc.get('total_labor_cost_cmo', 0)):,.2f} ({cmo_pct:.1f}% com encargos)\n"
                f"- **Receita Líquida:** R$ {float(pc.get('net_revenue', 0)):,.2f}\n\n"
                f"#### 🎯 Recomendação Estratégica:\n"
                + ("✅ Seu Prime Cost está dentro da faixa de excelência (< 65%). Mantenha o monitoramento semanal de perdas." if pc_pct <= 65 else "⚠️ **Atenção:** Seu Prime Cost ultrapassou 65%. Sugiro: (1) abrir tomada de preços B2B para insumos de alto giro via módulo RFQ; (2) checar ociosidade na escala de turnos nos dias de menor movimento (segunda/terça).")
            )
        elif "estoque" in prompt_lower or "ruptura" in prompt_lower or "comprar" in prompt_lower or "falta" in prompt_lower:
            intent = "STOCK_ALERT"
            crit_count = rag["critical_stock_count"]
            if crit_count > 0:
                crit_list = "\n".join([f"- **{s['name']}**: Saldo atual `{s['balance']} {s['unit']}` (Mínimo: `{s['min_stock']} {s['unit']}`) [Classe {s['abc_class']}]" for s in rag["critical_skus"]])
                reply_content = (
                    f"### 🚨 Alerta de Ruptura de Estoque\n\n"
                    f"Detectamos **{crit_count} insumo(s)** operando abaixo do estoque de segurança:\n\n"
                    f"{crit_list}\n\n"
                    f"#### 💡 Ação Imediata:\n"
                    f"Acesse o módulo de **Cotações B2B (RFQ)** ou **Pedidos de Compra** para disparar reposição com os fornecedores homologados."
                )
            else:
                reply_content = "### ✅ Níveis de Estoque Saudáveis\n\nTodos os insumos cadastrados estão operando com saldo acima da margem de segurança configurada. Nenhuma ruptura iminente detectada hoje."
        elif "whatsapp" in prompt_lower or "resumo" in prompt_lower or "briefing" in prompt_lower:
            intent = "SALES_SUMMARY"
            briefing = await self.generate_executive_briefing(tenant_id)
            reply_content = (
                f"### 📲 Resumo Executivo Diário Gerado\n\n"
                f"Aqui está a mensagem formatada para envio ao WhatsApp da diretoria:\n\n"
                f"```text\n{briefing['summary_text']}\n```\n\n"
                f"Você pode clicar no botão **Copiar para WhatsApp** no painel lateral para despachar."
            )
        else:
            reply_content = (
                f"### 🤖 FoodOps Copilot em Prontidão\n\n"
                f"Analisei a base operacional do restaurante neste momento:\n\n"
                f"- **Receita Líquida:** R$ {float(pc.get('net_revenue', 0)):,.2f}\n"
                f"- **Prime Cost Consolidado:** {float(pc.get('prime_cost_percentage', 0)):.1f}%\n"
                f"- **Itens Críticos de Estoque:** {rag['critical_stock_count']} insumo(s)\n"
                f"- **Pedidos no KDS:** {rag['kds_in_flight_orders']} comanda(s) ativas\n\n"
                f"Como posso ajudar a otimizar a sua operação hoje? Você pode me perguntar sobre **auditoria de CMV**, **análise de Prime Cost**, **risco de falta de insumos** ou pedir o **resumo do dia**."
            )

        # 4. Save copilot response
        copilot_msg = CopilotMessage(
            tenant_id=tenant_id,
            conversation_id=conv.id,
            sender="COPILOT",
            content=reply_content,
            intent=intent,
            data_payload=json.dumps({"rag_summary": rag}, default=str)
        )
        self.db.add(copilot_msg)
        await self.db.commit()


        return {
            "conversation_id": str(conv.id),
            "message_id": str(copilot_msg.id),
            "sender": "COPILOT",
            "content": reply_content,
            "intent": intent,
            "created_at": copilot_msg.created_at.isoformat() if copilot_msg.created_at else datetime.now(timezone.utc).isoformat()
        }

    async def list_conversations(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        stmt = select(CopilotConversation).where(CopilotConversation.tenant_id == tenant_id).order_by(CopilotConversation.created_at.desc())
        convs = (await self.db.execute(stmt)).scalars().all()
        return [{"id": str(c.id), "title": c.title, "created_at": c.created_at} for c in convs]
