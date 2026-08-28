import argparse, openpyxl, re, json, datetime, sys, os
from collections import defaultdict, Counter

parser = argparse.ArgumentParser(description="Extrai Efetivo x Emp Semanal x Depara_Função em um bundle.json para o painel.")
parser.add_argument("xlsx_path", help="Caminho do arquivo Apontamento_x_Empilhamento.xlsx")
parser.add_argument("-o", "--output", default="bundle.json", help="Caminho de saída do bundle.json (padrão: bundle.json)")
args = parser.parse_args()

if not os.path.isfile(args.xlsx_path):
    sys.exit(f"Arquivo não encontrado: {args.xlsx_path}")

wb = openpyxl.load_workbook(args.xlsx_path, data_only=True)

def norm(s):
    if s is None: return None
    return re.sub(r'\s+', ' ', str(s).strip()).lower()

def clean(s):
    if s is None: return None
    return re.sub(r'\s+', ' ', str(s).strip())

PCI_OS = {35732, 37131, 37132, 37581}
def contrato_of(os_key):
    if os_key == 'Apoio': return 'MOA'
    try:
        return 'PCI' if int(os_key) in PCI_OS else 'MOA'
    except (ValueError, TypeError):
        return 'MOA'

# ---------- Depara_Função ----------
ws_dp = wb['Depara_Função']
depara = {}
depara_pairs = []
for r in range(2, ws_dp.max_row+1):
    a = ws_dp.cell(row=r, column=1).value
    b = ws_dp.cell(row=r, column=2).value
    if a and b:
        depara[norm(a)] = clean(b)
        depara_pairs.append({"emp_semanal": clean(a), "efetivo": clean(b)})

# ---------- Efetivo ----------
ws_ef = wb['Efetivo']
efetivo_rows = []
ef_cargos_set = set()
for r in range(2, ws_ef.max_row+1):
    sap = ws_ef.cell(row=r, column=1).value
    if sap is None:
        continue
    matr_usm = ws_ef.cell(row=r, column=2).value
    matr_tct = ws_ef.cell(row=r, column=3).value
    nome = clean(ws_ef.cell(row=r, column=4).value)
    cargo = clean(ws_ef.cell(row=r, column=5).value)
    status = clean(ws_ef.cell(row=r, column=6).value)
    disciplina = clean(ws_ef.cell(row=r, column=7).value)
    encarregado = clean(ws_ef.cell(row=r, column=8).value)
    superv_efetivo = clean(ws_ef.cell(row=r, column=9).value)
    supervisor = clean(ws_ef.cell(row=r, column=10).value)
    custo = clean(ws_ef.cell(row=r, column=11).value)
    facil = ws_ef.cell(row=r, column=12).value
    sge = ws_ef.cell(row=r, column=13).value
    os_val = ws_ef.cell(row=r, column=14).value
    data_val = ws_ef.cell(row=r, column=15).value

    facil_n = facil if isinstance(facil, (int, float)) else 0
    sge_n = sge if isinstance(sge, (int, float)) else 0
    presente = (facil_n > 0) or (sge_n > 0)

    if isinstance(os_val, str) and os_val.strip() == '-':
        os_key = 'Apoio'
    elif os_val is None:
        os_key = None
    else:
        os_key = int(os_val)

    data_iso = data_val.date().isoformat() if isinstance(data_val, datetime.datetime) else (data_val.isoformat() if isinstance(data_val, datetime.date) else None)

    if cargo: ef_cargos_set.add(cargo)

    efetivo_rows.append({
        "sap": sap, "matr_usm": matr_usm, "matr_tct": matr_tct, "nome": nome,
        "cargo": cargo, "status": status, "disciplina": disciplina,
        "encarregado": encarregado, "superv_efetivo": superv_efetivo, "supervisor": supervisor,
        "custo": custo, "facil": facil_n, "sge": sge_n, "presente": presente,
        "os": os_key, "data": data_iso,
        "contrato": contrato_of(os_key) if os_key is not None else None,
    })

print("Efetivo rows:", len(efetivo_rows))
print("Datas Efetivo:", sorted(set(r['data'] for r in efetivo_rows if r['data'])))
print("OS Efetivo:", sorted(set(str(r['os']) for r in efetivo_rows if r['os'] is not None)))

# ---------- Emp Semanal ----------
ws_es = wb['Emp Semanal']
max_row = ws_es.max_row

week_blocks = []
c = 1
while c <= 40:
    v2 = ws_es.cell(row=2, column=c).value
    if isinstance(v2, str) and v2.startswith('Sem'):
        wk = int(re.search(r'\d+', v2).group())
        days = {}
        for dc in range(c, c+7):
            dname = ws_es.cell(row=5, column=dc).value
            days[dname] = dc
        week_blocks.append((wk, days))
        c += 8
    else:
        c += 1

DAY_ISO = {'Seg':1,'Ter':2,'Qua':3,'Qui':4,'Sex':5,'Sáb':6,'Dom':7}
def week_day_to_date(week, day_name, year=2026):
    return datetime.date.fromisocalendar(year, week, DAY_ISO[day_name])
assert week_day_to_date(34, 'Qui') == datetime.date(2026,8,20)

blocks = []
cur_os = None; cur_start = None
for r in range(28, max_row+1):
    b = ws_es.cell(row=r, column=2).value
    if b != cur_os:
        if cur_os is not None:
            blocks.append((cur_os, cur_start, r-1))
        cur_os = b; cur_start = r
blocks.append((cur_os, cur_start, max_row))

emp_semanal_plan = []
os_meta = {}
unmapped_cargos = set()

for os_val, s, e in blocks:
    if os_val is None:
        continue
    header_row = s
    titulo = clean(ws_es.cell(row=header_row, column=3).value)
    status_os = clean(ws_es.cell(row=header_row, column=4).value)
    disciplina = clean(ws_es.cell(row=header_row, column=5).value)
    os_key = 'Apoio' if os_val == 'Apoio' else int(os_val)
    os_meta[str(os_key)] = {"titulo": titulo, "status": status_os, "disciplina": disciplina, "contrato": contrato_of(os_key)}

    for r in range(s+1, e+1):
        cargo_raw = clean(ws_es.cell(row=r, column=5).value)
        if not cargo_raw:
            continue
        n = norm(cargo_raw)
        if n in depara:
            cargo_corrigido = depara[n]; via = 'depara'
        elif cargo_raw in ef_cargos_set:
            cargo_corrigido = cargo_raw; via = 'direto'
        else:
            cargo_corrigido = cargo_raw; via = 'NAO_MAPEADO'
            unmapped_cargos.add(cargo_raw)

        for wk, days in week_blocks:
            for dname, col in days.items():
                qtd = ws_es.cell(row=r, column=col).value
                qtd = qtd if isinstance(qtd, (int, float)) else 0
                if qtd == 0:
                    continue
                dt = week_day_to_date(wk, dname)
                emp_semanal_plan.append({
                    "os": os_key, "cargo_raw": cargo_raw, "cargo": cargo_corrigido,
                    "mapped_via": via, "semana": wk, "dia": dname,
                    "data": dt.isoformat(), "qtd_planejada": qtd
                })

print("\nEmp Semanal plan records (qtd>0):", len(emp_semanal_plan))
print("Unmapped cargos:", unmapped_cargos)

ef_os_disc = defaultdict(Counter)
for row in efetivo_rows:
    if row['os'] is not None:
        key = str(row['os'])
        if row['disciplina']:
            ef_os_disc[key][row['disciplina']] += 1
for key, counter in ef_os_disc.items():
    if key not in os_meta:
        top_disc = counter.most_common(1)[0][0] if counter else None
        os_key_parsed = key if key == 'Apoio' else int(key)
        os_meta[key] = {"titulo": None, "status": None, "disciplina": top_disc, "somente_efetivo": True, "contrato": contrato_of(os_key_parsed)}

week_info = [{"semana": wk, "inicio": week_day_to_date(wk,'Seg').isoformat(), "fim": week_day_to_date(wk,'Dom').isoformat()} for wk,_ in week_blocks]
datas_apontamento = sorted(set(r['data'] for r in efetivo_rows if r['data']))
dias_grid = []
for wk, days in week_blocks:
    for dname in ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']:
        dt = week_day_to_date(wk, dname)
        dias_grid.append({"semana": wk, "dia": dname, "data": dt.isoformat()})

cargo_corrigido_all = sorted(set(r["cargo"] for r in emp_semanal_plan) | set(r["cargo"] for r in efetivo_rows if r["cargo"]))

bundle = {
    "efetivo": efetivo_rows,
    "emp_semanal": emp_semanal_plan,
    "os_meta": os_meta,
    "depara": depara_pairs,
    "semanas": week_info,
    "datas_apontamento": datas_apontamento,
    "dias_grid": dias_grid,
    "cargos": cargo_corrigido_all,
}
with open(args.output, "w") as f:
    json.dump(bundle, f, ensure_ascii=False)

print("\nWeek info:", week_info)
print("Datas apontamento:", datas_apontamento)
print("Bundle size:", len(json.dumps(bundle, ensure_ascii=False)))
print("\nOS meta (contrato):")
for k,v in sorted(os_meta.items()):
    print(" ", k, v.get('contrato'), v.get('titulo') or v.get('disciplina'))
