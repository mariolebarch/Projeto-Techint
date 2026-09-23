import argparse, re, json, sys, os, unicodedata
from pyxlsb import open_workbook

parser = argparse.ArgumentParser(description="Extrai a aba 'RESUMO GERAL' de Relatório_Saldo_PCI_MOA.xlsb em um bundle.json para o Painel de Saúde das OS's.")
parser.add_argument("xlsb_path", help="Caminho do arquivo Relatório_Saldo_PCI_MOA.xlsb")
parser.add_argument("-o", "--output", default="bundle_saude_os.json", help="Caminho de saída do bundle.json")
args = parser.parse_args()

if not os.path.isfile(args.xlsb_path):
    sys.exit(f"Arquivo não encontrado: {args.xlsb_path}")

def clean(s):
    if s is None: return None
    return re.sub(r'\s+', ' ', str(s).strip())

def clean_periodo(s):
    """Alguns rótulos de período vêm com um apóstrofo sobrando no fim (herdado da planilha)."""
    c = clean(s)
    return c.rstrip("'") if c else c

def num(v):
    return float(v) if isinstance(v, (int, float)) else 0.0

def os_num(v):
    """Nº OS pode vir em formatos variados (44156.0, '44156', 'OS_044156',
    'OS_44156') ou como rótulo especial não numérico ('OS_PCI'/'OS_MOA')."""
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        m = re.search(r'\d+', v)
        if m:
            return int(m.group())
    return None

def os_label_for(num_val, raw_label):
    """Sempre exibe a OS no formato canônico 'OS_<número>' quando ela tem um
    número — a planilha traz essa mesma OS grafada de formas diferentes
    conforme a linha/aba (OS_044128, 44128, OS_44128), então derivamos o
    rótulo a partir do número em vez de confiar na grafia bruta da célula.
    Rótulos especiais não numéricos (ex.: 'OS_PCI'/'OS_MOA') são mantidos
    como estão."""
    if num_val is not None:
        return f"OS_{num_val}"
    return clean(raw_label)

wb = open_workbook(args.xlsb_path)
with wb.get_sheet('RESUMO GERAL') as sheet:
    rows = [{c.c: c.v for c in r} for r in sheet.rows()]

# ---------- Períodos de referência (linha 5, rótulos "PCI e MOA: ...") ----------
periodos = {
    "fads": clean_periodo(rows[5].get(30)),
    "pendencias": clean_periodo(rows[5].get(33)),
    "apropriacao": clean_periodo(rows[5].get(36)),
    "mobile": clean_periodo(rows[5].get(39)),
}

# ---------- Linhas de OS (linha 9 até a última antes do rodapé "Total Geral") ----------
header_row_idx = 7
os_list = []
total_row_idx = None
for i in range(header_row_idx + 1, len(rows)):
    d = rows[i]
    if not d:
        continue
    if d.get(8) == 'Total Geral':
        total_row_idx = i
        break
    # linha em branco no meio da tabela (ex: separador antes do rodapé)
    if d.get(8) is None and d.get(0) is None:
        continue
    # linha "(vazio)" — marcador de espaçamento herdado da tabela dinâmica de
    # origem, sem nenhum outro dado (nem HH, nem PEP) — não é uma OS real.
    if clean(d.get(8)) == '(vazio)':
        continue
    os_n = os_num(d.get(0))
    os_list.append({
        "os": os_n,
        "os_label": os_label_for(os_n, d.get(8)),
        "contrato": clean(d.get(1)),
        "pep": clean(d.get(2)),
        "lider": clean(d.get(3)),
        "fiscal": clean(d.get(4)),
        "sit_simp": clean(d.get(6)),
        "sit": clean(d.get(7)),
        "hh_previsto": num(d.get(9)),
        "hh_realizado": num(d.get(10)),
        "hh_saldo": num(d.get(11)),
        "vl_previsto": num(d.get(12)),
        "vl_realizado": num(d.get(13)),
        "vl_saldo": num(d.get(14)),
        "hh_consolidado": num(d.get(15)),
        "apropriacao_mes_hh": num(d.get(16)),
        "pendencias_hh_compact": num(d.get(17)),
        "consumo_total_hh": num(d.get(18)),
        "saldo_final_hh": num(d.get(19)),
        "pct_consumido": num(d.get(21)),
        "hh_70": num(d.get(22)),
        "fad_elab_hh": num(d.get(24)), "fad_elab_rs": num(d.get(25)),
        "fad_revisao_hh": num(d.get(26)), "fad_revisao_rs": num(d.get(27)),
        "fad_aprovacao_hh": num(d.get(28)), "fad_aprovacao_rs": num(d.get(29)),
        "fad_total_hh": num(d.get(30)), "fad_total_rs": num(d.get(31)),
        "pendencias_hh": num(d.get(33)), "pendencias_rs": num(d.get(34)),
        "apropriacao_hh": num(d.get(36)), "apropriacao_rs": num(d.get(37)),
        "mobile_hh": num(d.get(39)), "mobile_rs": num(d.get(40)),
        "saldo_geral_hh": num(d.get(42)), "saldo_geral_pct": num(d.get(43)), "saldo_geral_rs": num(d.get(44)),
    })

if total_row_idx is None:
    sys.exit("Não encontrei a linha 'Total Geral' em RESUMO GERAL — layout da planilha pode ter mudado.")

t = rows[total_row_idx]
totais = {
    "hh_previsto": num(t.get(9)), "hh_realizado": num(t.get(10)), "hh_saldo": num(t.get(11)),
    "vl_previsto": num(t.get(12)), "vl_realizado": num(t.get(13)), "vl_saldo": num(t.get(14)),
    "fad_elab_hh": num(t.get(24)), "fad_elab_rs": num(t.get(25)),
    "fad_revisao_hh": num(t.get(26)), "fad_revisao_rs": num(t.get(27)),
    "fad_aprovacao_hh": num(t.get(28)), "fad_aprovacao_rs": num(t.get(29)),
    "fad_total_hh": num(t.get(30)), "fad_total_rs": num(t.get(31)),
    "pendencias_hh": num(t.get(33)), "pendencias_rs": num(t.get(34)),
    "apropriacao_hh": num(t.get(36)), "apropriacao_rs": num(t.get(37)),
    "mobile_hh": num(t.get(39)), "mobile_rs": num(t.get(40)),
    "saldo_geral_hh": num(t.get(42)), "saldo_geral_pct": num(t.get(43)), "saldo_geral_rs": num(t.get(44)),
}

contratos = sorted(set(r["contrato"] for r in os_list if r["contrato"]))
lideres = sorted(set(r["lider"] for r in os_list if r["lider"]))
fiscais = sorted(set(r["fiscal"] for r in os_list if r["fiscal"]))
situacoes = sorted(set(r["sit"] for r in os_list if r["sit"]))

# ---------- Legenda Contrato (PEP -> rótulo PCI/MOA/UNIGAL), lida da aba
# " 8 - SALDO_FUNÇÃO X OS" (linhas 0-2, colunas 13-14) ----------
contrato_labels = {}
try:
    with wb.get_sheet(' 8 - SALDO_FUNÇÃO X OS') as sheet_areas:
        legend_rows = [{c.c: c.v for c in r} for r in sheet_areas.rows()][:3]
    for row in legend_rows:
        pep = clean(row.get(13))
        label = clean(row.get(14))
        if pep and label:
            contrato_labels[pep] = label
except Exception:
    pass

# ---------- Saldo por Função dentro de cada OS, lido da aba
# "1 - PLAN SALDO_OSs DET." — cada linha é uma combinação OS x Função. O
# "Saldo" e "Realizado" (HH e R$) batem exatamente com o total da OS em
# RESUMO GERAL; o "Consolidado" por função pode não somar ao "HH Previsto"
# da OS (parte do orçamento pode estar alocada sem detalhamento por função),
# então tratamos Consolidado como informativo, não como um "previsto" oficial.
funcoes_por_os = {}
with wb.get_sheet('1 - PLAN SALDO_OSs DET.') as sheet_det:
    det_rows = [{c.c: c.v for c in r} for r in sheet_det.rows()]

FUNC_PREFIX_RE = re.compile(r'^\d+\s*-\s*')
for d in det_rows[3:]:
    if not d:
        continue
    os_val = d.get(12)
    if not isinstance(os_val, (int, float)) or os_val == 0:
        continue
    sub_item = clean(d.get(3))
    if not sub_item:
        continue
    funcao = FUNC_PREFIX_RE.sub('', sub_item)
    key = str(int(os_val))
    bucket = funcoes_por_os.setdefault(key, {})
    f = bucket.setdefault(funcao, {"consolidado": 0.0, "realizado": 0.0, "saldo": 0.0, "vl_realizado": 0.0, "vl_saldo": 0.0})
    f["consolidado"] += num(d.get(7)) or num(d.get(6))
    f["realizado"] += num(d.get(8))
    f["saldo"] += num(d.get(9))
    f["vl_realizado"] += num(d.get(10))
    f["vl_saldo"] += num(d.get(11))
    # Valor unitário (R$/HH) da função, coluna E — usado para converter
    # Saldo Final de HH para R$. É uma taxa, não uma quantidade, então não
    # soma entre linhas: guarda a última leitura não-zero encontrada.
    valor_unit = num(d.get(4))
    if valor_unit:
        f["valor_unitario"] = valor_unit

# ---------- HH "em validação" (ainda não decretado no sistema) por OS x
# Função, lido das abas "4 - APROPRIAÇÃO", "5 - PLAN SGE_MOBILE" e
# "3 - PENDÊNCIAS", e somado ao Realizado por função acima. As três abas têm
# colunas fixas conhecidas (informadas pelo usuário) — nenhuma adivinhação de
# cabeçalho é necessária; se a aba não existir ou algo falhar, simplesmente
# não somamos nada dessa aba (nunca interrompe a extração).
def _fold(s):
    c = clean(s)
    if not c:
        return ''
    return unicodedata.normalize('NFD', c).encode('ascii', 'ignore').decode().strip().lower()

# Cada linha soma pro total da OS (by_os) sempre que tiver OS+HH válidos, e
# ADICIONALMENTE pro total por função (by_func) quando a função também bate
# com uma função conhecida da aba 1. O total por OS não depende de achar a
# função — uma linha sem função reconhecida (ou com o nome da função
# grafado diferente da aba 1) ainda entra no total da OS, só não aparece
# quebrada por função na tabela.
def scan_fixed_cols(sheet_name, os_col, func_col, hh_col):
    by_func, by_os = {}, {}
    if not sheet_name:
        return by_func, by_os
    try:
        with wb.get_sheet(sheet_name) as sheet:
            rows = [{c.c: c.v for c in r} for r in sheet.rows()]
    except Exception:
        return by_func, by_os
    for d in rows:
        if not d:
            continue
        os_val = os_num(d.get(os_col))
        if os_val is None:
            continue
        hh_val = num(d.get(hh_col))
        if not hh_val:
            continue
        by_os[os_val] = by_os.get(os_val, 0.0) + hh_val
        func_raw = clean(d.get(func_col))
        if func_raw:
            funcao = FUNC_PREFIX_RE.sub('', func_raw)
            key = (os_val, funcao)
            by_func[key] = by_func.get(key, 0.0) + hh_val
    return by_func, by_os

# "4 - APROPRIAÇÃO": OS=col L(idx11), HH=col T(idx19), Função=col AD(idx29)
prov_apropriacao, prov_apropriacao_por_os = scan_fixed_cols('4 - APROPRIAÇÃO', 11, 29, 19)
# "5 - PLAN SGE_MOBILE": OS=col S(idx18), HH=col J(idx9), Função=col AE(idx30)
prov_mobile, prov_mobile_por_os = scan_fixed_cols('5 - PLAN SGE_MOBILE', 18, 30, 9)

# O nome exato da aba "3 - PENDÊNCIAS" é localizado por busca tolerante
# (acento/caixa/espaço), já que outras abas do relatório vêm com grafia
# inconsistente (ex.: a aba 8 tem um espaço a mais no início do nome).
def find_sheet_name(substr_folded):
    try:
        names = wb.sheets
    except Exception:
        return None
    matches = [n for n in names if substr_folded in _fold(n).replace(' ', '')]
    if not matches:
        return None
    matches.sort(key=lambda n: (not _fold(n).strip().startswith('3'), n))
    return matches[0]

# Função=col G(idx6), HH=col I(idx8), OS=col J(idx9)
pend_sheet_name = find_sheet_name('pendenc')
pendencias_por_func, pendencias_por_os = scan_fixed_cols(pend_sheet_name, 9, 6, 8)

# Detalhamento linha a linha da aba "3 - PENDÊNCIAS" para a aba
# "Suplementação Pendência" do painel: cada linha pendente com seu motivo
# (coluna T) e valor (coluna Q), sem agregação — para o usuário resolver
# pendência por pendência. Colunas informadas pelo usuário: OS=J(idx9),
# Código=F(idx5), Função=G(idx6) (Item = "Código - Função"), HH=I(idx8),
# Valor R$=Q(idx16), Motivo=T(idx19).
pendencias_detalhe = []
if pend_sheet_name:
    try:
        with wb.get_sheet(pend_sheet_name) as sheet_pend:
            pend_rows = [{c.c: c.v for c in r} for r in sheet_pend.rows()]
    except Exception:
        pend_rows = []
    for d in pend_rows:
        if not d:
            continue
        os_val = os_num(d.get(9))
        if os_val is None:
            continue
        hh_val = num(d.get(8))
        if not hh_val:
            continue
        codigo = clean(d.get(5))
        funcao_r = clean(d.get(6))
        item = ' - '.join(p for p in (codigo, funcao_r) if p)
        pendencias_detalhe.append({
            "id": f"p{len(pendencias_detalhe)}",
            "os": os_val,
            "os_label": os_label_for(os_val, None),
            "item": item,
            "hh": round(hh_val, 3),
            "valor_rs": round(num(d.get(16)), 3),
            "motivo": clean(d.get(19)),
        })

# Totais por OS (não filtrados por função) — usados nos cartões do Resumo
# da OS e no Saldo Final, para nunca perder HH pendente/em projeção só
# porque o nome da função não bateu com a aba 1.
prov_total_por_os = {}
for os_val, hh in prov_apropriacao_por_os.items():
    prov_total_por_os[os_val] = prov_total_por_os.get(os_val, 0.0) + hh
for os_val, hh in prov_mobile_por_os.items():
    prov_total_por_os[os_val] = prov_total_por_os.get(os_val, 0.0) + hh
for r in os_list:
    if r["os"] is None:
        continue
    r["pend_total_hh"] = pendencias_por_os.get(r["os"], 0.0)
    r["prov_total_hh"] = prov_total_por_os.get(r["os"], 0.0)

# achata em listas ordenadas por saldo desc, pronto para exibição
for key, bucket in funcoes_por_os.items():
    os_int = int(key)
    items = []
    for funcao, vals in bucket.items():
        if not (vals["consolidado"] or vals["realizado"] or vals["saldo"]):
            continue
        prov = prov_apropriacao.get((os_int, funcao), 0.0) + prov_mobile.get((os_int, funcao), 0.0)
        pend = pendencias_por_func.get((os_int, funcao), 0.0)
        item = {"funcao": funcao, **vals}
        if prov:
            item["prov_hh"] = prov
        if pend:
            item["pend_hh"] = pend
        items.append(item)
    funcoes_por_os[key] = sorted(items, key=lambda x: -x["saldo"])

bundle = {
    "meta": {"empresa": "TECHINT ENGENHARIA E CONSTRUCAO SA"},
    "periodos": periodos,
    "os_list": os_list,
    "totais": totais,
    "contratos": contratos,
    "contrato_labels": contrato_labels,
    "lideres": lideres,
    "fiscais": fiscais,
    "situacoes": situacoes,
    "funcoes_por_os": funcoes_por_os,
    "pendencias_detalhe": pendencias_detalhe,
}

with open(args.output, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False)

print("OS rows:", len(os_list))
print("Pendências detalhe rows:", len(pendencias_detalhe))
print("Períodos:", periodos)
print("Contratos:", contratos)
print("Situações:", situacoes)
print("Totais:", totais)
print("Bundle size:", len(json.dumps(bundle, ensure_ascii=False)))
