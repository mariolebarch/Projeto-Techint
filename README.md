# Painéis de Confronto — Techint

Dois painéis operacionais em HTML único (sem build, sem backend), interligados
por uma página inicial (`index.html`) que deixa escolher qual abrir:

- **Efetivo × Empilhamento Semanal** (`dashboard.html`) — cruza apontamento
  diário de presença com o planejamento semanal de mão de obra, a partir de
  `Apontamento_x_Empilhamento.xlsx` (abas Efetivo, Emp Semanal, Depara_Função).
- **Painel de Improdutividades** (`improdutividades.html`) — cruza as
  interferências registradas com a situação dos RDCs, a responsabilidade
  (Techint × Usiminas) e o supervisor de cada encarregado, a partir de
  `Base_Painel_de_improdutividades.xlsx` (abas Export_BI, SGE, Interferências,
  Supervisores). Traz controle de SLA (previsto × real), curva S e insights
  gerenciais automáticos.

> ⚠️ Este repositório é **público**. Por isso ele contém só código — nenhuma
> planilha, nenhum `bundle.json` e nenhum HTML já com dados embutidos é
> versionado aqui (veja `.gitignore`). Nomes, matrículas e escalas de
> colaboradores nunca devem ser commitados.

## Como cada painel recebe dados

Tem duas formas, e não são excludentes — cada painel guarda seu próprio
histórico, de forma independente:

1. **Importação local (sempre disponível)** — no painel, clique na engrenagem
   → "Atualizar dados" → selecione o `.xlsx` no padrão daquele painel. Todo o
   ETL roda no navegador (usa a biblioteca [SheetJS](https://sheetjs.com/) via
   CDN) e os dados ficam só na sessão de quem importou.
2. **Supabase (dados centralizados)** — cada painel já vem conectado ao
   projeto Supabase `dqomnopaigdikkesbbvj` (URL e chave `anon` estão no
   próprio arquivo — isso é seguro, ver `supabase/README.md`), cada um numa
   tabela própria (`painel_snapshots` para o Efetivo, `improdutividade_snapshots`
   para o Improdutividades). Ao abrir o painel, ele tenta carregar
   automaticamente o snapshot mais recente do banco; se não conseguir (rede
   bloqueada, banco vazio), cai para os dados locais/embutidos sem quebrar.
   Fazendo login (Authentication → Users no Supabase) pela engrenagem, uma
   nova importação de planilha também é publicada no banco para todo mundo
   que abrir o link depois.

## Estrutura

```
index.html                  Página inicial: escolhe entre os dois painéis.
dashboard.html               Template do painel Efetivo x Empilhamento
                              (HTML+CSS+JS, um arquivo só). Contém o
                              placeholder __DATA_JSON__ e o ETL inteiro
                              portado para JS (importação local de .xlsx).
improdutividades.html        Template do Painel de Improdutividades, mesmo
                              esquema (__DATA_JSON__ + ETL em JS).
etl/etl.py                   ETL em Python do painel Efetivo, para gerar um
                              bundle.json fora do navegador.
etl/etl_improd.py            ETL em Python do Painel de Improdutividades.
etl/requirements.txt
scripts/build.py             Injeta um bundle.json em qualquer um dos dois
                              templates -> HTML autocontido, pronto para
                              abrir/publicar (aceita -t para escolher o
                              template).
supabase/schema.sql          Schema + RLS das duas tabelas de snapshot.
docs/                        Build pública (GitHub Pages) dos dois painéis,
                              com bundle vazio — ver seção abaixo.
```

## Uso local (sem Supabase)

Painel Efetivo:

```bash
pip install -r etl/requirements.txt
python etl/etl.py "Apontamento_x_Empilhamento.xlsx" -o bundle.json
python scripts/build.py bundle.json -t dashboard.html -o dashboard_final.html
```

Painel de Improdutividades:

```bash
python etl/etl_improd.py "Base_Painel_de_improdutividades.xlsx" -o bundle_improd.json
python scripts/build.py bundle_improd.json -t improdutividades.html -o improdutividades_final.html
```

Abra o `_final.html` gerado no navegador — funciona offline, sem servidor.
Ou abra o template puro (`dashboard.html` / `improdutividades.html`) e
importe a planilha pela engrenagem.

## Supabase (dados centralizados)

Projeto: `dqomnopaigdikkesbbvj`. Ver `supabase/README.md` para o passo a
passo (rodar `supabase/schema.sql`, que cria as duas tabelas de snapshot, e
criar usuários autorizados a importar). Cada painel só lê automaticamente;
para publicar uma planilha nova para todo mundo, é preciso estar logado
(painel → engrenagem → "Entrar para publicar dados").

Importante: dentro do preview do Artifact (claude.ai/code/artifact/...) a
conexão com o Supabase pode ser bloqueada pelo sandbox da plataforma — o
painel cai para os dados locais automaticamente nesse caso. A conexão real
funciona ao abrir o HTML final (ou o template) direto no navegador, fora do
preview.

## Link público (GitHub Pages)

`docs/index.html` é a página inicial pública, que leva a `docs/efetivo.html`
e `docs/improdutividades.html` — as mesmas builds dos dois templates, mas com
o bundle embutido **vazio** (sem nenhum dado de colaborador) — funcionam
porque cada uma carrega os dados de verdade direto da sua tabela no Supabase
assim que abre. Isso dá um link público estável, sem depender de enviar um
arquivo `.html` toda vez que os dados mudam.

Para ativar (só precisa fazer uma vez):

1. Neste repositório no GitHub → **Settings → Pages**.
2. Em **Source**, selecione **Deploy from a branch**.
3. Branch: `claude/painel-confronto-dados-civpok` — pasta: **/docs**.
4. **Save**.

Depois de alguns minutos os painéis ficam disponíveis em:
`https://mariolebarch.github.io/Projeto-Techint/`

Esse link não muda mesmo quando os dados no Supabase são atualizados —
só reflete a base mais recente automaticamente, sem precisar republicar
nada.
