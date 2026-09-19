import argparse, re, json, sys, os
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
    """Nº OS pode vir como número (44156.0) ou rótulo especial ('OS_PCI'/'OS_MOA')."""
    if isinstance(v, (int, float)):
        return int(v)
    return None

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
    os_list.append({
        "os": os_num(d.get(0)),
        "os_label": clean(d.get(8)),
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

bundle = {
    "meta": {"empresa": "TECHINT ENGENHARIA E CONSTRUCAO SA"},
    "periodos": periodos,
    "os_list": os_list,
    "totais": totais,
    "contratos": contratos,
    "lideres": lideres,
    "fiscais": fiscais,
    "situacoes": situacoes,
}

with open(args.output, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False)

print("OS rows:", len(os_list))
print("Períodos:", periodos)
print("Contratos:", contratos)
print("Situações:", situacoes)
print("Totais:", totais)
print("Bundle size:", len(json.dumps(bundle, ensure_ascii=False)))
