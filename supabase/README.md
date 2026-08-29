# Configurando o Supabase para o painel

Isso torna os dados **centralizados**: alguém importa a planilha uma vez e
todo mundo que abre o link do painel vê a mesma base, sem precisar importar
de novo localmente.

## 1. Criar o projeto (se ainda não tiver um)

Em [supabase.com](https://supabase.com) → New Project. Guarde a senha do
banco em local seguro (só é usada para acesso direto ao Postgres, não é
usada pelo painel).

## 2. Rodar o schema

No projeto, abra **SQL Editor** → cole o conteúdo de
[`schema.sql`](./schema.sql) → **Run**. Isso cria as duas tabelas de
snapshot — `painel_snapshots` (painel Efetivo) e `improdutividade_snapshots`
(Painel de Improdutividades) — com as mesmas políticas de acesso (leitura
pública, escrita só para usuários autenticados). Se o projeto já tinha
`painel_snapshots` de antes, rodar o script de novo é seguro: os `create
table if not exists` só criam o que ainda falta.

## 3. Criar pelo menos um usuário para importar dados

Em **Authentication → Users**, crie um usuário (e-mail/senha) para cada
pessoa que vai ter permissão de importar planilhas novas — normalmente você
mesmo. Sem estar autenticado como esse usuário, a inserção de um novo
snapshot é bloqueada pela política de RLS (isso é proposital: a chave
pública do painel não pode ter permissão de escrita).

## 4. Pegar a URL e a chave anon (pública)

Em **Project Settings → API**:
- **Project URL** (algo como `https://xxxxxxxx.supabase.co`)
- **anon public key** (é seguro expor essa chave no front-end — é assim que
  o Supabase foi projetado para funcionar; a segurança vem das políticas de
  RLS do passo 2, não do sigilo dessa chave)

## 5. Conectar essas credenciais ao painel

Me passe a Project URL e a anon key (aqui na conversa, ou em qualquer lugar
seguro) que eu conecto os dois painéis a elas: adiciono o cliente
`@supabase/supabase-js` (via CDN, mesmo padrão do SheetJS que já é usado
para importação local), faço cada painel carregar automaticamente o
snapshot mais recente da sua tabela ao abrir, e faço a importação pela
engrenagem também gravar o resultado no Supabase (após você logar com o
usuário criado no passo 3).

Nunca cole a chave `service_role` em nenhum lugar do front-end — só a
`anon public key` deve ir no `dashboard.html` / `improdutividades.html`.
