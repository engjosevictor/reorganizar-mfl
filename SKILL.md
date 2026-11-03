---
name: reorganizar-mfl
description: |
  Reorganiza um MFL do TQS (modelo só de desenhos, com pastas 001 a 999 por tipo de desenho) separando os desenhos por estrutura: um pavimento por estrutura (ex. Lazer, Guarita, Piscina), movendo os DWG referenciados nas plantas (.CPL) e reescrevendo os caminhos nos .CPL. Use quando alguém disser "separar o MFL por estrutura", "criar pavimento pra cada anexo", "jogar os desenhos de cada estrutura numa pasta", "reorganizar o MFL", "tirar os desenhos das pastas A a P", ou quiser saber o que cada planta (.CPL) referencia e onde está cada desenho. Também serve só pra listar as referências de um .CPL, sem mover nada.
---

# Skill: reorganizar um MFL por estrutura

Caso de teste: um MFL com 9 plantas (.CPL) em 6 estruturas, 122 desenhos levados pra 6 pavimentos novos. As 9 plantas abriram no TQS depois, sem referência perdida.

## O que a skill faz

Cada planta (.CPL) lista os desenhos que ela referencia, num caminho relativo (`..\<pasta>\<desenho>`). A skill agrupa as plantas por **sigla** (as 3 letras antes de `.CPL`, ex. `...-001-LAZ.CPL` = LAZ), liga cada sigla a um pavimento novo, move os DWG pra pasta desse pavimento e reescreve no .CPL o caminho, o texto da descrição e o nome da pasta de cada desenho.

- Desenho usado por plantas de pavimentos diferentes (ex. um detalhe padrão) é **copiado** pra cada um.
- Desenho que nenhuma planta referencia **não é tocado** (a skill só lista).
- **Nada é renomeado.** Se o pessoal quiser padronizar nomes, é outra etapa, depois.
- Só mexe em arquivos (DWG e .CPL). Não usa a API do TQS.

## Antes de começar (combine com a pessoa)

1. **Trabalhe numa duplicação, nunca no MFL original.** A pessoa duplica o edifício **pelo TQS** (Gerenciador). Cópia pelo Windows não serve: os `EDIFICIO.PAV` e o `EDIFICIO.BDE` continuam apontando pro edifício original. Peça o nome da pasta da duplicação.
2. **Os pavimentos novos a pessoa cria no Gerenciador do TQS**, na duplicação (nome e altura qualquer; a classe do piso não importa). Não tente criar por script: a API do TQS (`TQSBuild`) abre o edifício, mas o `Save` grava um **edifício novo em `C:\TQS\<nome>`** com os critérios padrão do TQS, em vez de gravar no edifício real. Se já tiver criado esse lixo, apague a pasta nova em `C:\TQS`.
3. **TQS fechado** durante a movimentação (Gerenciador e Modelador).
4. Os scripts rodam com o Python que tem o TQS instalado (`python -I`). Se o `pip.exe` estiver bloqueado na máquina, use `python -m pip`.
5. Peça a **lista de pavimentos desejados** e quais siglas vão pra qual. Os nomes dos pavimentos podem ter espaço (ex. `CASA DE BOMBAS`).

## Passo a passo

Os scripts estão em `~/.claude/skills/reorganizar-mfl/scripts/`. `<edificio>` é o caminho completo da pasta do edifício duplicado.

1. **Ver as siglas** (só leitura):
   `python -I plano_mfl.py "<edificio>"`
   Lista cada sigla e as plantas dela. Se o nome das plantas não termina em 3 letras antes de `.CPL`, passe `--sigla-regex=<regex com um grupo>`.

2. **Montar o mapa** sigla → pavimento com a pessoa, ex. `"LAZ=LAZER,GUA=GUARITA,LIX=LIXEIRA,GLP=GLP,PIS=PISCINA,CDB=CASA DE BOMBAS"`.

3. **Ver o plano** (só leitura):
   `python -I plano_mfl.py "<edificio>" "<mapa>"`
   Mostra quantos desenhos movem, quais serão **copiados** pra vários pavimentos, se algum referenciado não existe, e a lista dos **desenhos sem planta** (as mesmas pastas, mas nenhuma planta usa). Mostre isso à pessoa. **Pergunte o que fazer com os sem-planta**: por padrão ficam onde estão, e é o certo se não souber. Nunca mova sem ela decidir.

4. **Simular** (não grava nada):
   `python -I mover_desenhos.py "<edificio>" "<mapa>"`
   Confere os totais e se algum destino já existe ou algum nome colide.

5. **Gravar**, com o TQS fechado:
   `python -I mover_desenhos.py "<edificio>" "<mapa>" --gravar`
   Faz backup dos .CPL em `~/reorganizar-mfl-backup/<data-hora>/` (fora do edifício; **não** deixa `.antes` na pasta `PLANTAS`, porque o Gerenciador lista tudo de lá como se fossem plantas), copia os desenhos, remove os originais e confere se toda referência dos .CPL novos existe.

6. **A pessoa confere no TQS**: reabrir o TQS, abrir uma planta de cada pavimento e ver se os desenhos aparecem no lugar. Se algo estiver errado, os .CPL originais estão no backup.

## Só quer saber o que uma planta referencia?

Os `.CPL` são texto (codificação cp1252). Cada desenho referenciado é um bloco de 4 linhas: o caminho (`..\pasta\nome`), a descrição (`nome / tipo - pasta`), as coordenadas e o nome da pasta. A descrição já diz o tipo (Armação de pilares, de sapatas, de vigas, Planta de formas, Corte do edifício, Armação negativa/positiva de lajes etc.). Leia sem gravar; resolva o caminho a partir da pasta `PLANTAS` e confira se o DWG existe.

## Armadilhas e limites

- **Cópia pelo Windows** do edifício aponta pro edifício original (veja "Antes de começar").
- **Não renomeie a pasta do edifício** direto no Windows: o TQS deixa de rodar o edifício. Renomeie dentro do TQS.
- Os `.TXT` de revisão emitida (ex. `...-R00.TXT`) guardam `PAVIMENTO,<pasta antiga>`. É histórico da emissão, não referência a arquivo. A skill não mexe e não precisa.
- Os `_CR.DWG` e `_TB.DWG` (carimbo e tabela de ferros) ficam em `PLANTAS`, não se movem.
- **Não foi verificado** se os próprios DWG têm referências externas (xref) por caminho. Numa amostra, não apareceu nenhuma. Se algum desenho aparecer em branco no TQS, esse é o primeiro lugar a olhar.
- O formato assumido do .CPL (bloco de 4 linhas por desenho) é o do formato `---V14.0---` (cabeçalho dos .CPL do TQS V25). Se o script acusar "formato inesperado", pare e mostre à pessoa em vez de forçar.
- Se a pessoa ajustar o layout de uma planta no TQS e salvar, o `.CPL` passa a divergir do gerado pelo script (posições dos desenhos). É esperado.
