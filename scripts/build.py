import argparse, json, os, sys

parser = argparse.ArgumentParser(description="Injeta um bundle.json no template dashboard.html, gerando um HTML autocontido.")
parser.add_argument("bundle_path", help="Caminho do bundle.json (gerado por etl/etl.py)")
parser.add_argument("-t", "--template", default=os.path.join(os.path.dirname(__file__), "..", "dashboard.html"), help="Caminho do template dashboard.html")
parser.add_argument("-o", "--output", default="dashboard_final.html", help="Caminho de saída do HTML final (padrão: dashboard_final.html)")
args = parser.parse_args()

if not os.path.isfile(args.bundle_path):
    sys.exit(f"Bundle não encontrado: {args.bundle_path}")
if not os.path.isfile(args.template):
    sys.exit(f"Template não encontrado: {args.template}")

with open(args.bundle_path, encoding="utf-8") as f:
    bundle = json.load(f)

data_json = json.dumps(bundle, ensure_ascii=False).replace("</script>", "<\\/script>")

with open(args.template, encoding="utf-8") as f:
    template = f.read()

if "__DATA_JSON__" not in template:
    sys.exit("Placeholder __DATA_JSON__ não encontrado no template.")

out = template.replace("__DATA_JSON__", data_json)

with open(args.output, "w", encoding="utf-8") as f:
    f.write(out)

print(f"Gerado {args.output} ({len(out):,} bytes)")
