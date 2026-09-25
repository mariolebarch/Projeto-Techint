-- Painel de Confronto — armazenamento centralizado no Supabase
--
-- Estratégia: cada importação de planilha vira uma linha (um "snapshot")
-- guardando o bundle inteiro (o mesmo JSON que hoje fica embutido no HTML)
-- numa coluna jsonb. O painel sempre lê o snapshot mais recente. Isso evita
-- ter que modelar Efetivo/Emp Semanal/Depara em tabelas relacionais
-- separadas e mantém o front-end (dashboard.html) quase inalterado — ele já
-- trabalha com esse mesmo objeto DATA.
--
-- Rode este script uma vez no SQL Editor do seu projeto Supabase. Se você já
-- rodou uma versão anterior, rode de novo — os "create policy" abaixo são
-- precedidos de "drop policy if exists", então é seguro reexecutar.

create table if not exists public.painel_snapshots (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  source_filename text,
  imported_by     text,
  bundle          jsonb not null
);

create index if not exists painel_snapshots_created_at_idx
  on public.painel_snapshots (created_at desc);

alter table public.painel_snapshots enable row level security;

-- Leitura pública: o painel usa a chave "anon" (pública) do Supabase para
-- carregar os dados no navegador de quem abrir o link, então SELECT precisa
-- ser liberado para o papel "anon".
drop policy if exists "snapshots_select_public" on public.painel_snapshots;
create policy "snapshots_select_public"
  on public.painel_snapshots
  for select
  to anon, authenticated
  using (true);

-- Escrita pública: qualquer pessoa com o link do painel consegue importar
-- uma planilha e publicar para todo mundo, sem precisar criar conta/fazer
-- login no Supabase — o time relatou confusão repetida com o modelo
-- anterior (só publicava quem estivesse logado, e sem isso a importação
-- ficava presa no navegador de quem importou, "sumindo" para os outros).
-- Isso é uma decisão consciente de trocar controle de acesso por
-- simplicidade: a chave anon já é pública por natureza (fica embutida no
-- HTML), então essa política só formaliza que qualquer um com o link já
-- podia, na prática, fazer o navegador tentar publicar — só não conseguia
-- por essa regra do banco.
drop policy if exists "snapshots_insert_authenticated" on public.painel_snapshots;
drop policy if exists "snapshots_insert_public" on public.painel_snapshots;
create policy "snapshots_insert_public"
  on public.painel_snapshots
  for insert
  to anon, authenticated
  with check (true);

-- Sem política de update/delete: o histórico de snapshots é imutável via
-- API (só dá para apagar/alterar direto no painel do Supabase ou via
-- service_role, nunca pelo navegador). Isso também serve como trilha de
-- auditoria de quando/quem importou cada planilha (a coluna imported_by
-- fica vazia quando ninguém estava logado ao importar).


-- Painel de Improdutividades — mesma estratégia de snapshot, tabela própria
-- (bundle no formato: Export_BI x SGE x Interferências x Supervisores).

create table if not exists public.improdutividade_snapshots (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  source_filename text,
  imported_by     text,
  bundle          jsonb not null
);

create index if not exists improdutividade_snapshots_created_at_idx
  on public.improdutividade_snapshots (created_at desc);

alter table public.improdutividade_snapshots enable row level security;

drop policy if exists "improd_snapshots_select_public" on public.improdutividade_snapshots;
create policy "improd_snapshots_select_public"
  on public.improdutividade_snapshots
  for select
  to anon, authenticated
  using (true);

drop policy if exists "improd_snapshots_insert_authenticated" on public.improdutividade_snapshots;
drop policy if exists "improd_snapshots_insert_public" on public.improdutividade_snapshots;
create policy "improd_snapshots_insert_public"
  on public.improdutividade_snapshots
  for insert
  to anon, authenticated
  with check (true);


-- Painel de Saúde das OS's — mesma estratégia de snapshot, tabela própria
-- (bundle no formato: aba RESUMO GERAL de Relatório_Saldo_PCI_MOA.xlsb).

create table if not exists public.saude_os_snapshots (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  source_filename text,
  imported_by     text,
  bundle          jsonb not null
);

create index if not exists saude_os_snapshots_created_at_idx
  on public.saude_os_snapshots (created_at desc);

alter table public.saude_os_snapshots enable row level security;

drop policy if exists "saude_os_snapshots_select_public" on public.saude_os_snapshots;
create policy "saude_os_snapshots_select_public"
  on public.saude_os_snapshots
  for select
  to anon, authenticated
  using (true);

drop policy if exists "saude_os_snapshots_insert_authenticated" on public.saude_os_snapshots;
drop policy if exists "saude_os_snapshots_insert_public" on public.saude_os_snapshots;
create policy "saude_os_snapshots_insert_public"
  on public.saude_os_snapshots
  for insert
  to anon, authenticated
  with check (true);
