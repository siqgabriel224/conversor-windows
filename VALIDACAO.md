# Validação do Conversor 0.1.0

## Rodada ampliada de 26/10/2026

- 429 casos distintos aprovados após correções e repetições: 323 pares do catálogo, 91 testes anteriores, 8 variações adicionais e 7 regressões específicas.
- A matriz usa 50 extensões de entrada, incluindo Office antigo, RAR/TAR/GZ, OPUS, HEIC, OTF e DWG. Os hashes das 50 amostras permaneceram intactos.
- A primeira matriz teve 315 aprovações e 8 falhas. Foi corrigida a rejeição indevida de TAR com campos de link vazios e acrescentada uma espera limitada para bloqueios temporários na publicação de arquivos. Os casos que falharam e as operações afetadas foram repetidos na instalação corrigida: 13 aprovações.
- O calibre usou configurações isoladas nos testes para evitar a restrição de escrita do terminal no AppData.
- Uma conferência numérica mais rigorosa encontrou separação indevida do decimal na importação de TSV. A importação foi corrigida para usar tabulações explicitamente, e as seis saídas de TSV foram repetidas; 21 resultados de planilhas também tiveram estrutura e valor decimal conferidos. Essa falha não era detectada pelas verificações básicas da primeira matriz.
- A matriz verifica os motores instalados; não representa 323 gestos físicos nem garante fidelidade para todos os arquivos possíveis. Detalhes e evidências: `RELATORIO-TESTES-20261026.md` e `tests/results/validation-consolidated-20261026.json`.

## Motores reais

- `tests/results/worker.xml`: 81 testes passaram, sem falhas ou testes ignorados (192 segundos).
- `tests/results/specialized.xml`: 10 testes passaram, sem falhas ou testes ignorados (39 segundos).
- Imagens: seis entradas × sete saídas; resultados reabertos com Pillow ou leitor PDF, dimensão/conteúdo validados.
- PDF: páginas para PNG/JPG, divisão, extração, junção e compressão; contagem de páginas e resultados conferidos.
- Office: exemplos de Word, Excel, PowerPoint, texto e CSV; saídas para PDF, ODT, DOCX, ODS, CSV, TSV, XLSX e ODP.
- Mídia: dez saídas; streams de áudio/vídeo conferidos com ffprobe.
- E-books: EPUB para MOBI, AZW3, PDF e TXT; MOBI/AZW3 retornaram a EPUB legível.
- Fontes: geração de WOFF/WOFF2 e restauração a TTF, preservando a quantidade de glifos.
- CAD: DXF para PDF/SVG/PNG e ciclo DXF → DWG → DXF, com entidades reabertas.
- HEIC: arquivo HEIC real gerado e convertido para JPG legível.
- Compactação: ZIP/7Z criados e extraídos; conteúdo idêntico aos originais. Caminhos de extração inseguros e links foram rejeitados.
- Falhas: arquivo danificado, intervalo inválido, conflito de nomes, cancelamento antes de iniciar e cancelamento durante execução de componente.
- Todos os testes de conversão compararam os hashes das entradas antes e depois.

## Integração

- A janela foi inspecionada visualmente e uma imagem foi adicionada pelo seletor de arquivos e convertida para JPG pela interface. A fila concluiu e o resultado foi reaberto com Pillow (320 × 240).
- A linha de comando enfileirou e aguardou WEBP na mesma instância da interface. O caminho com `Área de Trabalho` e `ação-final` foi conferido após a correção explícita de UTF-8.
- Uma regra de monitoramento foi criada pela interface. Uma imagem nova gerou automaticamente PDF de uma página na pasta de saída.
- O botão Cancelar interrompeu uma conversão real de MP4 para WEBM; a linha de comando recebeu `Cancelado`, código de saída 1 e nenhuma saída publicada.
- Quatro conversões (imagem, PDF, Office e mídia) também concluíram no ambiente de execução com rede restrita, usando temporários dentro do projeto. Isso não equivale a desligar fisicamente a conexão do PC.
- Na instalação final, Gabriel executou Ctrl + arrastar no Explorador e confirmou que o menu apareceu e recebeu a imagem sobre WEBP. O histórico registrou origem `menu circular`, destino `webp` e estado `Concluído` em 25/10/2026 às 23:48. O arquivo `tests/gesto-ctrl/teste-ctrl.webp` foi reaberto com Pillow: WEBP válido, 320 × 240, 1.120 bytes. O SHA-256 do PNG original permaneceu idêntico ao da amostra de origem. Combinações de monitores e escalas ainda precisam de teste manual.

## Instalação final

- Excel pelo menu circular: Gabriel soltou `tests/gesto-excel/teste-menu-excel.xlsx` em PDF; o histórico instalado confirmou `Concluído` e origem `menu circular`. O PDF de uma página foi reaberto com PDFium e inspecionado visualmente, sem cortes ou sobreposição. Os cabeçalhos `Produto` e `Valor`, o texto `Teste` e o valor `123,45` coincidem com os dados da planilha. O XLSX original conservou o SHA-256 `1A495ADDDA866C05D2F1D12D4AE4F813CFF42E2ACAB7F745A441C96345B175E4`.

- Word pelo menu circular: Gabriel soltou `tests/gesto-word/teste-menu-word - Copia.docx` em PDF; o histórico instalado confirmou `Concluído` e origem `menu circular`. O PDF tem uma página, renderizada e inspecionada sem cortes ou sobreposição; PDFium confirmou o título e o texto completo, incluindo acentos. O leitor pypdf apresentou divergência na extração de acentos desse PDF, enquanto PDFium e a renderização os preservaram. O DOCX convertido e o DOCX de referência conservaram o SHA-256 `CB99A8A65C284B4CCCCCC78BFFE956D5E6043A7581E85B20478F1CBDB338BCD4`.

- Em 26/10/2026, Gabriel executou dois gestos Ctrl + arrastar com `tests/gesto-video/teste-menu-video.mov`: MP4 e MP3. Ambos constam como `Concluído`, origem `menu circular`, no histórico instalado. O MP4 contém vídeo H.264 de 640 × 360 e áudio AAC; o MP3 contém apenas áudio MP3 a 44.100 Hz. Ambos têm 5 segundos e foram decodificados integralmente com FFmpeg sem erros. O SHA-256 do MOV original permaneceu `F7F6E4AEF2E2D1BFF4FC0B7FEDFF62518B7AB384713165D9A8C408527A12F0BC`, idêntico ao registrado antes dos gestos.

- Instalador autocontido em um único executável: `dist/Conversor-0.1.0-Instalar.exe`, aproximadamente 1.120 MB. A instalação terminou com código 0.
- Instalado em `%LOCALAPPDATA%\Programs\Conversor`; nove componentes foram encontrados nos caminhos privados instalados.
- Atalho `Conversor.lnk` na área de trabalho aponta para a instalação final. DLL principal, worker e manifesto coincidem por SHA-256 com a publicação.
- Uma conversão pela CLI instalada concluiu WEBP na fila da interface instalada, com caminho acentuado correto.
- Fechar a janela ocultou-a e manteve uma única instância na bandeja; reabrir pelo atalho mostrou a mesma instância, sem duplicação. A inicialização automática está configurada para o executável instalado com `--background`.
- A regra temporária de monitoramento foi removida e os históricos dos testes anteriores foram arquivados em `tests/results`. Os arquivos de teste foram preservados.

## Limites da validação

Os testes cobrem os cenários acima; não são garantia de fidelidade para todos os documentos, codecs, fontes e versões CAD. A rodada ampliada incluiu amostras básicas de Office antigo e RAR; arquivos complexos e outras variantes ainda podem exigir ajustes. Reiniciar o PC e desligar fisicamente a rede ainda não foram testados. A aplicação não tem upload, telemetria ou downloads durante conversões.

## Ajuste técnico em relação ao plano

O processamento de PDF ficou no worker Python: PDFium por pypdfium2 e edição por pypdf, em vez de PDFsharp. Isso mantém cada conversão isolada em processo e atende às operações previstas. A fila executa um trabalho por vez nesta versão, preservando a resposta da interface e permitindo cancelamento por arquivo.
