# App de Estoque de Leite Materno

Este diretório é dedicado ao novo aplicativo de estoque de leite materno.

Objetivo: manter o desenvolvimento separado do projeto da dashboard Porto Estrela, evitando poluição no diretório raiz.

## Escopo deste app

- Controle de **entrada** e **saída** por lote
- Controle de **data de vencimento**
- Planejamento de uso baseado na rotina de retorno ao trabalho

## Modelo funcional inicial

### 1) Estrutura mínima do sistema

Use uma planilha (Google Sheets/Excel) ou app de banco simples com 4 tabelas:

1. **Lotes (estoque por frasco/saco)**
2. **Entradas (ordenhas)**
3. **Saídas (ofertas para o bebê)**
4. **Planejamento semanal**

### 2) Campos recomendados

#### 2.1 Tabela de Lotes
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

#### 2.2 Tabela de Entradas
Registro por evento de ordenha.

- `id_entrada`
- `data_hora`
- `volume_total_ml`
- `qtd_frascos`
- `volume_por_frasco_ml`
- `lotes_gerados` (lista de IDs)

#### 2.3 Tabela de Saídas
Registro de consumo.

- `id_saida`
- `data_hora`
- `lote_utilizado`
- `volume_retirado_ml`
- `volume_descartado_ml` (se houver)
- `responsavel`
- `motivo_descarte` (opcional)

#### 2.4 Tabela de Planejamento Semanal
Aqui está o “cérebro” para organizar a rotina de trabalho.

- `semana`
- `demanda_dia_ml` (quanto o bebê consome em média por dia)
- `demanda_semanal_ml = demanda_dia_ml * 7`
- `entrada_prevista_semanal_ml` (estimativa de ordenha)
- `saldo_inicial_ml`
- `saldo_final_previsto_ml = saldo_inicial + entrada_prevista - demanda_semanal`
- `dias_cobertos = estoque_atual_ml / demanda_dia_ml`
- `alerta` (ok, atenção, crítico)

### 3) Regras de negócio essenciais

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
   - Ajustar conforme rotina real após retorno ao trabalho.

5. **Rastreabilidade**
   - Todo consumo deve apontar exatamente qual lote foi utilizado.

### 4) Indicadores principais

- **Estoque atual (ml)**
- **Dias de cobertura**
- **Volume a vencer em 7 dias**
- **Taxa de descarte (%)**
- **Déficit/superávit semanal previsto**

### 5) Observação importante

As regras de armazenamento, descongelamento, transporte e validade devem seguir orientação de pediatra e/ou banco de leite humano.

