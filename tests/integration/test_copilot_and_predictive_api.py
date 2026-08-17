import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.intelligence.models import CopilotConversation, CopilotMessage, ExecutiveBriefing
from packages.tenant.models import Tenant


@pytest.mark.asyncio
async def test_copilot_interactive_chat_rag(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    # 1. Ask about Prime Cost
    r_chat1 = await async_client.post("/copilot/chat", json={
        "prompt": "Qual é o nosso Prime Cost hoje e como podemos reduzi-lo?"
    }, headers=auth_headers)
    assert r_chat1.status_code == 200, r_chat1.text
    chat1 = r_chat1.json()
    assert chat1["sender"] == "COPILOT"
    assert "Prime Cost" in chat1["content"]
    assert "conversation_id" in chat1
    conv_id = chat1["conversation_id"]

    # 2. Ask follow-up about stock rupture
    r_chat2 = await async_client.post("/copilot/chat", json={
        "conversation_id": conv_id,
        "prompt": "Quais insumos estão com risco de ruptura no estoque?"
    }, headers=auth_headers)
    assert r_chat2.status_code == 200
    chat2 = r_chat2.json()
    assert chat2["sender"] == "COPILOT"
    assert "Estoque" in chat2["content"] or "insumo" in chat2["content"].lower()

    # 3. List conversations
    r_convs = await async_client.get("/copilot/conversations", headers=auth_headers)
    assert r_convs.status_code == 200
    convs = r_convs.json()
    assert any(c["id"] == conv_id for c in convs)


@pytest.mark.asyncio
async def test_copilot_stock_alert_and_audit(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    r_audit = await async_client.get("/copilot/audit", headers=auth_headers)
    assert r_audit.status_code == 200, r_audit.text
    audit = r_audit.json()
    assert "overall_health" in audit
    assert "prime_cost_percentage" in audit
    assert "diagnostics" in audit
    assert len(audit["diagnostics"]) >= 1
    for d in audit["diagnostics"]:
        assert "pillar" in d
        assert "severity" in d
        assert "title" in d
        assert "action" in d


@pytest.mark.asyncio
async def test_copilot_executive_briefing_generation_and_dispatch(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    # 1. Get today briefing
    r_brief = await async_client.get("/copilot/briefings/today", headers=auth_headers)
    assert r_brief.status_code == 200, r_brief.text
    brief = r_brief.json()
    assert "summary_text" in brief
    assert "RESUMO EXECUTIVO" in brief["summary_text"]
    assert "PRIME COST" in brief["summary_text"]

    # 2. Dispatch briefing to WhatsApp
    r_disp = await async_client.post("/copilot/briefings/dispatch", json={
        "channel": "WHATSAPP",
        "destination": "+5511988887777"
    }, headers=auth_headers)
    assert r_disp.status_code == 200, r_disp.text
    disp = r_disp.json()
    assert disp["status"] == "DISPATCHED"
    assert disp["channel"] == "WHATSAPP"


@pytest.mark.asyncio
async def test_copilot_cross_tenant_isolation(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession
):
    t2 = Tenant(name="Tenant 2 Copilot Secret")
    owner_session.add(t2)
    await owner_session.flush()
    t2_id = t2.id

    conv_t2 = CopilotConversation(tenant_id=t2_id, title="Conversa Secreta T2")
    owner_session.add(conv_t2)
    await owner_session.flush()
    conv_t2_id_str = str(conv_t2.id)
    await owner_session.commit()

    # Query with Tenant 1
    r_convs = await async_client.get("/copilot/conversations", headers=auth_headers)
    assert r_convs.status_code == 200
    assert all(c["id"] != conv_t2_id_str for c in r_convs.json())
