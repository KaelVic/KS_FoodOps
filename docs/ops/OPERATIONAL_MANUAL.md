# Manual Operacional do Restaurante — KS FoodOps

Guia prático para a equipe do restaurante operar o sistema no dia a dia.

---

## 🍽️ 1. Primeiro Acesso & Configuração (Pilar B)
1. **Onboarding**: Ao criar a conta de acesso, acesse `/onboarding` e informe o **Nome do Restaurante**.
2. **Locais de Estoque (`/locations`)**:
   - Cadastre os almoxarifados físicos onde as mercadorias ficam guardadas:
     - *Estoque Seco*, *Câmara Fria*, *Bar*, *Cozinha Quente*, *Salão*.
3. **Equipe (`/team`)**:
   - Convide seus colaboradores e atribua os papéis:
     - **Admin / Gerente Geral**: Acesso irrestrito a custos, compras e fechamentos.
     - **Chef / Cozinheiro**: Acesso às fichas técnicas e registro de perdas de produção.
     - **Estoquista / Comprador**: Acesso ao recebimento de mercadorias e contagem de estoque.

---

## 📦 2. Catálogo & Compras (Pilar A)
1. **Insumos (`/catalog`)**:
   - Cadastre itens comprados manualmente (ex: hortifrúti de feira sem XML).
   - Defina a unidade de medida base (kg, litro, unidade).
   - Configure o fator de conversão de compras (Ex: 1 Caixa com 12 garrafas de 750ml = 9.000 ml).
2. **Entrada de NF-e via XML (`/purchasing`)**:
   - Arraste o arquivo XML da nota do fornecedor.
   - O sistema extrai automaticamente itens, fornecedor, quantidade e custos unitários.
   - O estoque é alimentado no Ledger assim que o recebimento for aprovado.

---

## 📱 3. Chão de Loja: Contagem Física Mobile (Pilar D)
1. **Iniciar Inventário Semanal/Mensal (`/inventory-sessions`)**:
   - O gerente clica em **"Iniciar Nova Sessão de Contagem"**.
2. **Contagem no Celular/Tablet pelo Estoquista**:
   - O estoquista abre a tela no celular.
   - Utiliza os botões rápidos (`-1`, `+1`, `+5`, `+10`) ou digita o valor com teclado numérico.
   - A barra de progresso no topo indica quantos itens faltam para concluir a contagem.
   - O sistema salva automaticamente cada item digitado.
3. **Fechamento Cego**:
   - Ao concluir, o gerente clica em **"Finalizar Contagem"**.
   - O sistema compara o estoque físico contado com o estoque teórico das vendas e apura divergências imediatamente.

---

## 📊 4. Fechamento de Mês & Contabilidade (Pilar C)
1. **DRE Operacional (`/reports/closing`)**:
   - Visualização de **Faturamento**, **CMV Real (%)**, **CMV Teórico**, **Perdas Registradas** e **Divergência Oculta**.
2. **Exportações para Contabilidade**:
   - Clique em **"Exportar Inventário (CSV)"** para baixar a planilha valorizada para conciliação bancária/contábil.
   - Clique em **"SPED Bloco H (.txt)"** para enviar ao contador o arquivo fiscal oficial do inventário.
