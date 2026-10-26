# Validação ampliada do Conversor — 26/10/2026

## Resultado consolidado

**429 casos distintos aprovados**, após correções e repetições direcionadas:

- 323 pares do catálogo, com 50 extensões de entrada e componentes da instalação final.
- 91 testes anteriores de integração, conteúdo básico, cancelamento, corrupção e conflitos.
- 8 variações adicionais: transparência, redimensionamento, vídeo sem áudio, restauração de OTF/CFF e compactação de extensões desconhecidas.
- 7 regressões específicas para TAR, links e bloqueios temporários/permanentes ao publicar resultados.

| Categoria | Pares testados | Aprovados |
|---|---:|---:|
| Imagens | 75 | 75 |
| PDF | 7 | 7 |
| Texto / Word | 27 | 27 |
| Planilhas | 31 | 31 |
| Apresentações | 13 | 13 |
| Vídeo e extração de áudio | 62 | 62 |
| Áudio | 50 | 50 |
| E-books | 18 | 18 |
| Compactados | 13 | 13 |
| Fontes | 18 | 18 |
| CAD | 9 | 9 |

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

O worker corrigido está no código-fonte, na publicação e na instalação, com SHA-256 `68083ddca5804f9d1da378c02af71c51f03b72ca5d801ab1bc4ac31f08e6c49e`. O worker anterior foi preservado em `tests/results/worker-installed-before-20261026.py`.

Os pares que já passaram não foram todos repetidos depois da correção localizada; foram repetidos os casos que falharam e as operações afetadas, além dos testes específicos. Não houve alteração dos motores nem do código da interface.

Esta rodada testa as conversões por seus motores, sem executar 323 gestos físicos. Os testes anteriores com Gabriel confirmaram o menu circular para imagem → WEBP, vídeo → MP4/MP3 e Word/Excel → PDF. Arquivos extensos ou complexos, outras variantes de codecs, fórmulas, fontes e versões CAD podem apresentar diferenças. Reinício do PC, várias telas/escalas e desconexão física da rede continuam fora desta rodada. GIF e imagens com várias páginas continuam limitados ao primeiro quadro/página.

## Evidências

Os registros por caso e o XML de origem de cada aprovação estão em `tests/results/validation-consolidated-20261026.json`. Os resultados não foram contados como aprovações apenas pela existência dos arquivos.
