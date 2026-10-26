"""Consolidate original runs and targeted retests without counting duplicates."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_catalog_matrix import ROOT, PAIRS, INSTALLED, validate

RESULTS = ROOT / "tests" / "results"


def merge(*names):
    records = {}
    for name in names:
        file = RESULTS / name
        tree = ET.parse(file)
        for test in tree.iter("testcase"):
            key = (test.attrib["classname"], test.attrib["name"])
            records[key] = dict(
                name=test.attrib["name"],
                evidence=name,
                state="failed"
                if test.find("failure") is not None or test.find("error") is not None
                else "skipped"
                if test.find("skipped") is not None
                else "passed",
            )
    return records


matrix = merge(
    "matrix-full-20261026.xml",
    "matrix-final-recheck-20261026.xml",
    "matrix-tsv-fixed-20261026.xml",
)
regression = merge("regression-20261026.xml", "regression-calibre-20261026.xml")
edges = merge("matrix-edges-20261026.xml", "matrix-resize-20261026.xml")
fixes = merge("worker-fixes-20261026.xml")
groups = dict(matrix=matrix, regression=regression, edges=edges, fixes=fixes)
assert len(matrix) == len(PAIRS) == 323
assert len(regression) == 91 and len(edges) == 8 and len(fixes) == 7
failures = [
    r for records in groups.values() for r in records.values() if r["state"] != "passed"
]
assert not failures, failures
sources = RESULTS / "matrix-20261026" / "entradas-ação0"
hashes = json.loads((sources / "sha256.json").read_text())
assert all(
    hashlib.sha256((sources / ("amostra." + ext)).read_bytes()).hexdigest() == digest
    for ext, digest in hashes.items()
)
worker_hash = hashlib.sha256((ROOT / "worker" / "convert.py").read_bytes()).hexdigest()
assert (
    worker_hash
    == hashlib.sha256((INSTALLED / "worker" / "convert.py").read_bytes()).hexdigest()
)
numeric_checks = []
for category, ext, target in PAIRS:
    if category != "planilha" or target in ("zip", "7z"):
        continue
    record = next(
        r
        for r in matrix.values()
        if r["name"] == f"test_catalog_pair[{ext}-to-{target}]"
    )
    folder = (
        RESULTS
        / Path(record["evidence"]).stem
        / f"test_catalog_pair_{ext}_to_{target}_0"
        / "saída"
    )
    outputs = list(folder.glob("*." + target))
    assert len(outputs) == 1, (ext, target, outputs)
    validate(outputs[0], target, sources / ("amostra." + ext), category)
    numeric_checks.append(
        dict(source=ext, target=target, output=str(outputs[0]), passed=True)
    )
assert len(numeric_checks) == 21
(RESULTS / "numeric-checks-20261026.json").write_text(
    json.dumps(numeric_checks, ensure_ascii=False, indent=2), encoding="utf-8"
)
category_names = dict(
    imagem="Imagens",
    pdf="PDF",
    texto="Texto / Word",
    planilha="Planilhas",
    slides="Apresentações",
    video="Vídeo e extração de áudio",
    audio="Áudio",
    livro="E-books",
    arquivo="Compactados",
    fonte="Fontes",
    cad="CAD",
)
counts = Counter(category for category, _, _ in PAIRS)
rows = "\n".join(f"| {category_names[k]} | {v} | {v} |" for k, v in counts.items())
report = f"""# Validação ampliada do Conversor — 26/10/2026

## Resultado consolidado

**429 casos distintos aprovados**, após correções e repetições direcionadas:

- 323 pares do catálogo, com 50 extensões de entrada e componentes da instalação final.
- 91 testes anteriores de integração, conteúdo básico, cancelamento, corrupção e conflitos.
- 8 variações adicionais: transparência, redimensionamento, vídeo sem áudio, restauração de OTF/CFF e compactação de extensões desconhecidas.
- 7 regressões específicas para TAR, links e bloqueios temporários/permanentes ao publicar resultados.

| Categoria | Pares testados | Aprovados |
|---|---:|---:|
{rows}

ZIP e 7Z aparecem também nas categorias que podem ser compactadas. A matriz é extraída de `Catalog.cs`, excluindo a conversão para a própria extensão, como faz a interface. A junção de PDFs, operação com vários arquivos, está na suíte anterior.

## Como foram conferidos

As conversões usaram processos reais dos componentes instalados. Imagens foram reabertas e suas dimensões verificadas; PDFs foram reabertos e renderizados com PDFium; saídas de Office tiveram conteúdo básico conferido; áudio e vídeo foram analisados por ffprobe e decodificados integralmente com FFmpeg. Compactados foram testados e extraídos com comparação byte a byte; fontes tiveram mapas de caracteres e glifos comparados; DWG retornou a DXF para conferir entidades.

Os 50 arquivos de entrada da matriz conservaram seus hashes. Cada conversão também compara o hash da entrada antes e depois. As amostras são sintéticas e locais; nenhum arquivo pessoal foi usado nesta rodada.

## Falhas encontradas e tratamento

A primeira matriz terminou com 315 aprovações e 8 falhas. Quatro falhas de publicação no Office foram `WinError 5` ao renomear o arquivo temporário para o nome reservado. Uma repetição fora do isolamento também reproduziu esse erro em XLSX → CSV; portanto não foi atribuído apenas ao sandbox. Foi acrescentada uma repetição limitada para bloqueios temporários do Windows (até 1,55 segundo de espera no total), mantendo cancelamento, limpeza e preservação de arquivos existentes. Não foi determinado qual processo externo provocou os bloqueios.

Três falhas de e-book → PDF ocorreram porque o calibre tentou gravar configuração no AppData fora da área permitida do terminal. O verificador passou a fornecer uma pasta própria de configuração. As três conversões foram repetidas nessa condição.

A extração de TAR tinha um defeito real: campos vazios `Symbolic Link` e `Hard Link` eram tratados como links existentes. A correção permite campos vazios e mantém a rejeição de links com destino e modos de link. A extração real de TAR e dos demais compactados foi repetida.

Uma conferência adicional dos números revelou um segundo defeito que os testes básicos não detectavam: a importação automática de TSV separava o decimal `123,45` como outra coluna. Foi definido explicitamente o filtro de importação tabulado UTF-8, conforme a [documentação do LibreOffice](https://help.libreoffice.org/latest/pt-BR/text/shared/guide/csv_params.html). Todas as seis saídas oferecidas para TSV foram repetidas; as quatro conversões de planilha agora verificam também a preservação do valor decimal e da estrutura de colunas. Os 21 resultados de conversão entre formatos de planilha e PDF receberam essa verificação mais rigorosa, registrada em `tests/results/numeric-checks-20261026.json`.

O verificador também recebeu correções próprias (fechamento do leitor PDF e parâmetros opcionais), antes das respectivas aprovações. Os XMLs brutos preservam os resultados originais e as repetições; a consolidação não apaga falhas anteriores.

## Instalação e limites

O worker corrigido está no código-fonte, na publicação e na instalação, com SHA-256 `{worker_hash}`. O worker anterior foi preservado em `tests/results/worker-installed-before-20261026.py`.

Os pares que já passaram não foram todos repetidos depois da correção localizada; foram repetidos os casos que falharam e as operações afetadas, além dos testes específicos. Não houve alteração dos motores nem do código da interface.

Esta rodada testa as conversões por seus motores, sem executar 323 gestos físicos. Os testes anteriores com Gabriel confirmaram o menu circular para imagem → WEBP, vídeo → MP4/MP3 e Word/Excel → PDF. Arquivos extensos ou complexos, outras variantes de codecs, fórmulas, fontes e versões CAD podem apresentar diferenças. Reinício do PC, várias telas/escalas e desconexão física da rede continuam fora desta rodada. GIF e imagens com várias páginas continuam limitados ao primeiro quadro/página.

## Evidências

Os registros por caso e o XML de origem de cada aprovação estão em `tests/results/validation-consolidated-20261026.json`. Os resultados não foram contados como aprovações apenas pela existência dos arquivos.
"""
(ROOT / "RELATORIO-TESTES-20261026.md").write_text(report, encoding="utf-8")
(RESULTS / "validation-consolidated-20261026.json").write_text(
    json.dumps(
        {k: list(v.values()) for k, v in groups.items()}, ensure_ascii=False, indent=2
    ),
    encoding="utf-8",
)
print(
    json.dumps(
        dict(
            total=sum(len(v) for v in groups.values()),
            matrix=len(matrix),
            originals=len(hashes),
            failures=0,
        )
    )
)
