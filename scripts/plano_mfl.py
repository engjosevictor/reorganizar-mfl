# coding: utf-8
"""Plano de reorganizacao de um MFL (SO LEITURA).
Agrupa os desenhos referenciados em cada planta (.CPL) por pavimento novo.
Uso:
  python -I plano_mfl.py "<pasta do MFL>"                          (lista as siglas encontradas)
  python -I plano_mfl.py "<pasta do MFL>" "LAZ=LAZER,GUA=GUARITA"  (mostra o plano)
A sigla sao as 3 letras antes de .CPL no nome da planta (ex. ...-001-LAZ.CPL).
Outro formato de nome: --sigla-regex=<regex com um grupo de captura>."""
import sys, os, re
from collections import defaultdict

CP = "cp1252"
S = chr(92)          # barra invertida
PRE = ".." + S       # prefixo das referencias nos .CPL
REGEX_PADRAO = "-([A-Z]{3})" + S + ".CPL$"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
raiz = args[0]
mapa_txt = args[1] if len(args) > 1 else ""
rx = re.compile(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--sigla-regex=")), REGEX_PADRAO))


def sigla_de(nome):
    m = rx.search(nome.upper())
    return m.group(1) if m else None


def referencias(caminho_cpl):
    """Devolve (pasta, nome) de cada desenho referenciado, sem os da pasta PLANTAS."""
    for ln in open(caminho_cpl, encoding=CP, newline=""):
        ln = ln.rstrip("\r\n")
        if ln.startswith(PRE) and not ln.startswith(PRE + "PLANTAS" + S):
            pasta, nome = ln[3:].split(S, 1)
            yield pasta, nome


cpls = sorted(f for f in os.listdir(os.path.join(raiz, "PLANTAS")) if f.upper().endswith(".CPL"))
siglas = defaultdict(list)
for f in cpls:
    siglas[sigla_de(f)].append(f)

if not mapa_txt:
    print("Siglas encontradas (plantas):")
    for s, fs in siglas.items():
        print(f"  {s}: {len(fs)} planta(s) -> {', '.join(fs)}")
    print('\nRode de novo passando o mapa, ex.: "LAZ=LAZER,GUA=GUARITA"')
    sys.exit()

mapa = dict(p.split("=", 1) for p in mapa_txt.split(","))
faltam = [s for s in siglas if s not in mapa]
if faltam:
    sys.exit(f"Siglas sem pavimento no mapa: {faltam}")

refs = defaultdict(set)
for f in cpls:
    pav = mapa[sigla_de(f)]
    for pasta, nome in referencias(os.path.join(raiz, "PLANTAS", f)):
        refs[(pasta, nome)].add(pav)

mover, copiar, faltando = [], [], []
for (pasta, nome), pavs in sorted(refs.items()):
    if not os.path.exists(os.path.join(raiz, pasta, nome + ".DWG")):
        faltando.append(pasta + S + nome)
        continue
    (copiar if len(pavs) > 1 else mover).append((pasta + S + nome + ".DWG", sorted(pavs)))

usados = {(p.lower(), n.lower()) for (p, n) in refs}
pastas_origem = sorted({p for (p, n) in refs})
orfaos = []
for pasta in pastas_origem:
    cam = os.path.join(raiz, pasta)
    if os.path.isdir(cam):
        for f in sorted(os.listdir(cam)):
            if f.upper().endswith(".DWG") and (pasta.lower(), f[:-4].lower()) not in usados:
                orfaos.append(pasta + S + f)

print(f"Mover (so 1 pavimento usa): {len(mover)}")
print(f"Copiar pra varios pavimentos: {len(copiar)}")
for org, pavs in copiar:
    print("  ", org, "->", ", ".join(pavs))
print(f"Referenciados no CPL mas sem DWG na pasta: {len(faltando)}", faltando)
print(f"Sem planta, nas mesmas pastas (nao serao tocados): {len(orfaos)}")
for o in orfaos:
    print("  ", o)
