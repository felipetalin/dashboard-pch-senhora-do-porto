# Sistema de Estoque de Leite Materno

Este guia descreve um modelo simples e prático para você controlar **entrada**, **saída**, **validade** e **planejamento de uso** do estoque de leite materno com foco no retorno da mãe ao trabalho.

## 1) Estrutura mínima do sistema

Use uma planilha (Google Sheets/Excel) ou app de banco simples com 4 tabelas:

1. **Lotes (estoque por frasco/saco)**
2. **Entradas (ordenhas)**
3. **Saídas (ofertas para o bebê)**
4. **Planejamento semanal**

---

## 2) Campos recomendados

### 2.1 Tabela de Lotes
Cada linha representa um frasco/saco congelado.

- `id_lote` (ex: LM-2026-02-001)
- `data_ordenha`
- `hora_ordenha` (opcional)
- `volume_ml`
- `local` (geladeira/freezer)
- `status` (disponível, reservado, consumido, vencido)
- `validade` (calculada)
- `observacoes`

> Regra principal: aplicar **PEPS/FIFO** (primeiro que entra, primeiro que sai), respeitando validade.

### 2.2 Tabela de Entradas
Registro por evento de ordenha.

- `id_entrada`
- `data_hora`
- `volume_total_ml`
- `qtd_frascos`
- `volume_por_frasco_ml`
- `lotes_gerados` (lista de IDs)

### 2.3 Tabela de Saídas
Registro de consumo.

- `id_saida`
- `data_hora`
- `lote_utilizado`
- `volume_retirado_ml`
- `volume_descartado_ml` (se houver)
- `responsavel`
- `motivo_descarte` (opcional)

### 2.4 Tabela de Planejamento Semanal
Aqui está o “cérebro” para organizar a rotina de trabalho.

- `semana`
- `demanda_dia_ml` (quanto o bebê consome em média por dia)
- `demanda_semanal_ml = demanda_dia_ml * 7`
- `entrada_prevista_semanal_ml` (estimativa de ordenha)
- `saldo_inicial_ml`
- `saldo_final_previsto_ml = saldo_inicial + entrada_prevista - demanda_semanal`
- `dias_cobertos = estoque_atual_ml / demanda_dia_ml`
- `alerta` (ok, atenção, crítico)

---

## 3) Regras de negócio essenciais

1. **Validade por ambiente**
   - Defina e fixe no sistema regras adotadas pelo pediatra/banco de leite de referência.
   - O sistema deve calcular automaticamente a validade ao criar o lote.

2. **Uso por prioridade**
   - Consumir primeiro lotes com menor validade restante.

3. **Reserva mínima de segurança**
   - Exemplo: manter no mínimo `3 dias` de consumo médio.
   - Se `dias_cobertos < 3`, alerta crítico.

4. **Meta de produção semanal**
   - `meta_ordenha_semana = demanda_semanal - entrada_base + margem`
   - Ajustar conforme rotina real da sua esposa após retorno ao trabalho.

5. **Rastreabilidade**
   - Todo consumo deve apontar exatamente qual lote foi utilizado.

---

## 4) Indicadores que mais ajudam na prática

- **Estoque atual (ml)**
- **Dias de cobertura**
- **Volume a vencer em 7 dias**
- **Taxa de descarte (%)**
- **Déficit/superávit semanal previsto**

Com esses 5 indicadores vocês conseguem decidir rapidamente se precisam:
- aumentar ordenhas em dias específicos,
- ajustar volumes por frasco,
- antecipar uso de lotes próximos do vencimento.

---

## 5) Exemplo de rotina operacional

### Diário
- Registrar ordenhas (entradas).
- Registrar mamadas com leite estocado (saídas).
- Conferir alerta de validade próxima.

### Semanal (30 min)
- Atualizar média de consumo diário do bebê.
- Revisar previsão de entrada para a próxima semana.
- Simular cenário: “se ordenar menos 20%, ainda cobre quantos dias?”

### Mensal
- Revisar taxa de descarte e causas.
- Ajustar tamanho dos frascos para reduzir sobra/descarte.

---

## 6) Planejamento para retorno ao trabalho (passo a passo)

1. **Mapear consumo real por faixa horária** (manhã/tarde/noite).
2. **Definir demanda durante expediente** (quanto precisa ficar disponível para o cuidador).
3. **Criar meta de estoque-alvo** antes da volta (ex: 10 a 14 dias de cobertura).
4. **Planejar ordenhas fixas por dia útil** (com alarmes).
5. **Revisar semanalmente o saldo previsto** e corrigir cedo.

---

## 7) Estrutura rápida para começar hoje (planilha)

Crie 3 abas mínimas:

1. `Estoque_lotes`
2. `Movimentacoes` (entrada/saída)
3. `Planejamento`

Fórmulas-chave:

- `estoque_atual_ml = SOMA(volume dos lotes com status = disponível)`
- `dias_cobertos = estoque_atual_ml / consumo_medio_diario_ml`
- `vencer_7_dias = SOMA(lotes com validade <= hoje+7 e status = disponível)`

---

## 8) Observação importante de segurança

As **regras de armazenamento, descongelamento, transporte e validade** devem seguir orientação de **pediatra e/ou banco de leite humano**. O sistema ajuda no controle, mas não substitui orientação clínica.

---

## 9) Próximo passo recomendado

Se você quiser, podemos transformar este modelo em:

- uma **planilha pronta** com fórmulas e alertas visuais, ou
- um **mini sistema web** (dashboard) com cadastro de lotes, alertas de vencimento e previsão automática de cobertura.

