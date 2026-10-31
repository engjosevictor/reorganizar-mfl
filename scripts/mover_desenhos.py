# coding: utf-8
"""Move os desenhos referenciados pelas plantas (.CPL) para a pasta do pavimento novo e reescreve os .CPL.
Desenho usado por pavimentos diferentes e COPIADO pra cada um. Desenho sem planta nao e tocado.
Uso:
  python -I mover_desenhos.py "<pasta do edificio>" "LAZ=LAZER,GUA=GUARITA"            (simula)
  python -I mover_desenhos.py "<pasta do edificio>" "LAZ=LAZER,GUA=GUARITA" --gravar   (grava)
So arquivos (sem API do TQS). Rode com o TQS FECHADO e numa DUPLICACAO do edificio.
Backup dos .CPL fica FORA do edificio (o caminho e impresso no fim)."""
import sys, os, re, shutil, time

CP = "cp1252"
S = chr(92)
PRE = ".." + S
REGEX_PADRAO = "-([A-Z]{3})" + S + ".CPL$"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
raiz, mapa = args[0], dict(p.split("=", 1) for p in args[1].split(","))
gravar = "--gravar" in sys.argv
rx = re.compile(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--sigla-regex=")), REGEX_PADRAO))

for p in mapa.values():
    assert os.path.isdir(os.path.join(raiz, p)), f"falta a pasta do pavimento {p} (crie no Gerenciador do TQS)"

cpls = sorted(f for f in os.listdir(os.path.join(raiz, "PLANTAS")) if f.upper().endswith(".CPL"))
novos, acoes, destinos, origens = {}, [], {}, set()

for f in cpls:
    pav = mapa[rx.search(f.upper()).group(1)]
    linhas = open(os.path.join(raiz, "PLANTAS", f), encoding=CP, newline="").read().split("\n")
    i = 0
    while i < len(linhas):
        ln = linhas[i].rstrip("\r")
        if ln.startswith(PRE) and not ln.startswith(PRE + "PLANTAS" + S):
            eol = "\r" if linhas[i].endswith("\r") else ""
            pasta, nome = ln[3:].split(S, 1)
            linhas[i] = PRE + pav + S + nome + eol
            d = linhas[i + 1]
            suf = " - " + pasta
            e2 = "\r" if d.endswith("\r") else ""
            if d.rstrip("\r").endswith(suf):        # a descricao termina com " - <pasta antiga>"
                linhas[i + 1] = d.rstrip("\r")[:-len(suf)] + " - " + pav + e2
            k = linhas[i + 3]                        # 4a linha do bloco = nome da pasta
            e3 = "\r" if k.endswith("\r") else ""
            assert k.rstrip("\r") == pasta, f"formato inesperado em {f}: {nome}"
            linhas[i + 3] = pav + e3
            org = os.path.join(raiz, pasta, nome + ".DWG")
            dst = os.path.join(raiz, pav, nome + ".DWG")
            assert os.path.exists(org), org
            assert destinos.get(dst, org) == org, f"colisao de nome em {dst}"
            destinos[dst] = org
            origens.add(org)
            acoes.append((org, dst))
            i += 3
        i += 1
    novos[f] = "\n".join(linhas)

unicas = sorted(set(acoes))
print(f"{len(cpls)} plantas, {len(unicas)} arquivos a levar, {len(origens)} origens distintas")
for org, dst in unicas:
    if os.path.exists(dst):
        print("JA EXISTE no destino:", dst)
if not gravar:
    for org, dst in unicas[:6]:
        print("  ex.:", os.path.relpath(org, raiz), "->", os.path.relpath(dst, raiz))
    sys.exit("simulacao, nada gravado")

bk = os.path.join(os.path.expanduser("~"), "reorganizar-mfl-backup", time.strftime("%Y%m%d-%H%M%S"))
os.makedirs(bk)
for f, txt in novos.items():
    cam = os.path.join(raiz, "PLANTAS", f)
    shutil.copy2(cam, os.path.join(bk, f))
    open(cam, "w", encoding=CP, newline="").write(txt)
for org, dst in unicas:
    shutil.copy2(org, dst)
for org in origens:
    os.remove(org)

# conferencia: toda referencia dos .CPL novos existe
falt = 0
for f in cpls:
    for ln in open(os.path.join(raiz, "PLANTAS", f), encoding=CP, newline=""):
        ln = ln.rstrip("\r\n")
        if ln.startswith(PRE) and not os.path.exists(os.path.normpath(os.path.join(raiz, "PLANTAS", ln)) + ".DWG"):
            falt += 1
            print("FALTA", ln)
print(f"gravado. backup dos .CPL em {bk}. referencias faltando: {falt}")
