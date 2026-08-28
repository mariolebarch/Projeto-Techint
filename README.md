# Painel de Confronto — Efetivo × Empilhamento Semanal

Painel operacional em HTML único (sem build, sem backend) que cruza três abas de
`Apontamento_x_Empilhamento.xlsx`:

- **Efetivo** — apontamento diário real (presença via colunas Facil/SGE).
- **Emp Semanal** — planejamento semanal de mão de obra por OS e cargo.
- **Depara_Função** — normalização de nomenclatura de cargos entre as duas abas.

> ⚠️ Este repositório é **público**. Por isso ele contém só código — nenhuma
> planilha, nenhum `bundle.json` e nenhum HTML já com dados embutidos é
> versionado aqui (veja `.gitignore`). Nomes, matrículas e escalas de
> colaboradores nunca devem ser commitados.

## Como o painel recebe dados

Tem duas formas, e não são excludentes:

1. **Importação local (sempre disponível)** — no painel, clique na engrenagem
   → "Atualizar dados" → selecione o `.xlsx`. Todo o ETL roda no navegador
   (usa a biblioteca [SheetJS](https://sheetjs.com/) via CDN) e os dados
   ficam só na sessão de quem importou.
2. **Supabase (dados centralizados)** — `dashboard.html` já vem conectado ao
   projeto Supabase `dqomnopaigdikkesbbvj` (URL e chave `anon` estão no
   próprio arquivo — isso é seguro, ver `supabase/README.md`). Ao abrir o
   painel, ele tenta carregar automaticamente o snapshot mais recente do
   banco; se não conseguir (rede bloqueada, banco vazio), cai para os dados
   locais/embutidos sem quebrar. Fazendo login (Authentication → Users no
   Supabase) pela engrenagem, uma nova importação de planilha também é
   publicada no banco para todo mundo que abrir o link depois.

## Estrutura

```
dashboard.html        Template do painel (HTML+CSS+JS, um arquivo só).
                       Contém o placeholder __DATA_JSON__ e também o ETL
                       inteiro portado para JS (importação local de .xlsx).
etl/etl.py             Mesmo ETL, em Python, para gerar um bundle.json fora
                       do navegador (útil para automatizar/agendar).
etl/requirements.txt
scripts/build.py       Injeta um bundle.json no template -> dashboard_final.html
                       (um HTML autocontido, pronto para abrir/publicar).
supabase/schema.sql    Schema + RLS para hospedar os dados no Supabase.
```

## Uso local (sem Supabase)

```bash
pip install -r etl/requirements.txt
python etl/etl.py "Apontamento_x_Empilhamento.xlsx" -o bundle.json
python scripts/build.py bundle.json -o dashboard_final.html
```

Abra `dashboard_final.html` no navegador — funciona offline, sem servidor.
Ou abra `dashboard.html` puro e importe a planilha pela engrenagem.

## Supabase (dados centralizados)

Projeto: `dqomnopaigdikkesbbvj`. Ver `supabase/README.md` para o passo a
passo (rodar `schema.sql`, criar usuários autorizados a importar). O painel
só lê automaticamente; para publicar uma planilha nova para todo mundo, é
preciso estar logado (painel → engrenagem → "Entrar para publicar dados").

Importante: dentro do preview do Artifact (claude.ai/code/artifact/...) a
conexão com o Supabase pode ser bloqueada pelo sandbox da plataforma — o
painel cai para os dados locais automaticamente nesse caso. A conexão real
funciona ao abrir o `dashboard_final.html` (ou este `dashboard.html`) direto
no navegador, fora do preview.
