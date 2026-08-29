import argparse, openpyxl, re, json, datetime, sys, os
from collections import defaultdict

parser = argparse.ArgumentParser(description="Extrai Export_BI x SGE x Interferências x Supervisores em um bundle.json para o Painel de Improdutividades.")
parser.add_argument("xlsx_path", help="Caminho do arquivo Base_Painel_de_improdutividades.xlsx")
parser.add_argument("-o", "--output", default="bundle_improd.json", help="Caminho de saída do bundle.json")
args = parser.parse_args()

if not os.path.isfile(args.xlsx_path):
    sys.exit(f"Arquivo não encontrado: {args.xlsx_path}")

wb = openpyxl.load_workbook(args.xlsx_path, data_only=True)

def clean(s):
    if s is None: return None
    return re.sub(r'\s+', ' ', str(s).strip())

def norm_key(s):
    if s is None: return None
    return re.sub(r'\s+', ' ', str(s).strip()).upper()

def norm_os(v):
    if v is None: return None
    s = str(v).strip()
    s = re.sub(r'^OS[_\s]*', '', s, flags=re.I)
    s = s.lstrip('0') or '0'
    return s

def to_iso_date(v):
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    if isinstance(v, datetime.date): return v.isoformat()
    return None

def to_hours(v):
    if isinstance(v, (int, float)): return round(float(v), 4)
    return 0.0

# ---------- Interferências (responsável) ----------
ws_int = wb['Interferências']
responsavel_by_interf = {}
interferencia_list = []
for r in range(2, ws_int.max_row+1):
    a = clean(ws_int.cell(row=r, column=1).value)
    b = clean(ws_int.cell(row=r, column=2).value)
    if a and b:
        responsavel_by_interf[norm_key(a)] = b
        interferencia_list.append({"interferencia": a, "responsavel": b})

# ---------- Supervisores ----------
ws_sup = wb['Supervisores']
supervisor_by_encarregado = {}
for r in range(2, ws_sup.max_row+1):
    a = clean(ws_sup.cell(row=r, column=1).value)
    c = clean(ws_sup.cell(row=r, column=3).value)
    if a and c:
        supervisor_by_encarregado[norm_key(a)] = c

# ---------- SGE (situação do RDC) ----------
ws_sge = wb['SGE']
situacao_by_rdc = {}
rdcs = []
for r in range(2, ws_sge.max_row+1):
    rdc_num = ws_sge.cell(row=r, column=1).value
    if rdc_num is None:
        continue
    tipo = clean(ws_sge.cell(row=r, column=2).value)
    data_ref = to_iso_date(ws_sge.cell(row=r, column=3).value)
    os_val = norm_os(ws_sge.cell(row=r, column=4).value)
    encarregado = clean(ws_sge.cell(row=r, column=6).value)
    situacao = clean(ws_sge.cell(row=r, column=7).value)
    rdc_key = clean(ws_sge.cell(row=r, column=8).value)
    if rdc_key:
        situacao_by_rdc[norm_key(rdc_key)] = situacao
    supervisor = supervisor_by_encarregado.get(norm_key(encarregado)) if encarregado else None
    rdcs.append({
        "rdc": rdc_key or (f"RDC_{rdc_num}" if rdc_num else None),
        "tipo": tipo,
        "d": data_ref,
        "os": os_val,
        "enc": encarregado,
        "sup": supervisor,
        "sit": situacao,
    })

# ---------- Export_BI: aggregate to (data, os, grupo, interferencia, encarregado) ----------
ws = wb['Export_BI']
max_row = ws.max_row

groups = {}
sit_hit = 0
total_rows = 0
unmapped_interf = set()
unmapped_sup = set()

for r in range(2, max_row+1):
    rdc = clean(ws.cell(row=r, column=3).value)
    os_val = norm_os(ws.cell(row=r, column=4).value)
    grupo = clean(ws.cell(row=r, column=6).value)
    interf = clean(ws.cell(row=r, column=7).value)
    encarregado = clean(ws.cell(row=r, column=9).value)
    data_ini = ws.cell(row=r, column=12).value
    dur = to_hours(ws.cell(row=r, column=16).value)
    plan = to_hours(ws.cell(row=r, column=17).value)
    real = to_hours(ws.cell(row=r, column=18).value)
    h_ativ = to_hours(ws.cell(row=r, column=19).value)

    if os_val is None and interf is None and encarregado is None:
        continue
    total_rows += 1

    d_iso = to_iso_date(data_ini)
    resp = responsavel_by_interf.get(norm_key(interf)) if interf else None
    if interf and resp is None:
        unmapped_interf.add(interf)
    sup = supervisor_by_encarregado.get(norm_key(encarregado)) if encarregado else None
    if encarregado and sup is None:
        unmapped_sup.add(encarregado)
    if rdc and norm_key(rdc) in situacao_by_rdc:
        sit_hit += 1

    key = (d_iso, os_val, grupo, interf, encarregado)
    if key not in groups:
        groups[key] = {
            "d": d_iso, "os": os_val, "gi": grupo, "it": interf,
            "resp": resp, "enc": encarregado, "sup": sup,
            "n": 0, "plan": 0.0, "real": 0.0, "dur": 0.0, "hAtiv": 0.0,
        }
    g = groups[key]
    g["n"] += 1
    g["plan"] += plan
    g["real"] += real
    g["dur"] += dur
    g["hAtiv"] += h_ativ

interferencias = list(groups.values())
for g in interferencias:
    g["plan"] = round(g["plan"], 3)
    g["real"] = round(g["real"], 3)
    g["dur"] = round(g["dur"], 3)
    g["hAtiv"] = round(g["hAtiv"], 3)

print("Export_BI total rows:", total_rows)
print("Aggregated interferencias groups:", len(interferencias))
print("RDC situacao match rate:", sit_hit, "/", total_rows, f"({100*sit_hit/total_rows:.2f}%)")
print("Unmapped interferencia types:", unmapped_interf)
print("Unmapped encarregados (no supervisor):", len(unmapped_sup))

datas = sorted(set(g["d"] for g in interferencias if g["d"]) | set(rc["d"] for rc in rdcs if rc["d"]))
os_list = sorted(set(g["os"] for g in interferencias if g["os"]), key=lambda x: (len(x), x))
grupos = sorted(set(g["gi"] for g in interferencias if g["gi"]))
supervisores = sorted(set(g["sup"] for g in interferencias if g["sup"]))
situacoes = sorted(set(rc["sit"] for rc in rdcs if rc["sit"]))

bundle = {
    "meta": {"empresa": "TECHINT ENGENHARIA E CONSTRUCAO SA"},
    "interferencias": interferencias,
    "rdcs": rdcs,
    "interferencia_tipos": interferencia_list,
    "datas": datas,
    "os_list": os_list,
    "grupos": grupos,
    "supervisores": supervisores,
    "situacoes": situacoes,
}

with open(args.output, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False)

print("\nDatas:", datas[0], "a", datas[-1], f"({len(datas)} datas)")
print("OS:", os_list)
print("Grupos:", grupos)
print("Supervisores:", supervisores)
print("Situacoes RDC:", situacoes)
print("RDCs:", len(rdcs))
print("Bundle size:", len(json.dumps(bundle, ensure_ascii=False)))
