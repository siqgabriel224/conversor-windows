# Componentes de terceiros

A interface e o código de integração são próprios. O Filee foi utilizado como referência de interação; seu código não foi copiado.

Os motores e bibliotecas mantêm suas licenças originais e seus avisos distribuídos nas respectivas pastas:

| Componente | Projeto / licença |
|---|---|
| .NET / WPF | Microsoft, MIT e avisos distribuídos com o runtime |
| CPython | Python Software Foundation License |
| ImageMagick | ImageMagick License |
| FFmpeg (Gyan Essentials) | GPL; configurações e licenças na distribuição oficial |
| LibreOffice | MPL 2.0 e componentes com licenças próprias |
| Ghostscript | GNU AGPL v3, Artifex |
| 7-Zip | GNU LGPL, BSD e restrição unRAR |
| calibre | GNU GPL v3 |
| Pandoc | GNU GPL v2 ou posterior |
| pypdf | BSD-3-Clause |
| pypdfium2 / PDFium | Apache-2.0 / BSD e avisos do PDFium |
| Pillow | HPND |
| fontTools / Brotli | MIT |
| ezdxf | MIT |
| PyMuPDF | GNU AGPL v3, Artifex |
| ODA File Converter | Software proprietário gratuito; termos da Open Design Alliance |
| yt-dlp | Unlicense; dependências com licenças próprias |
| yt-dlp-ejs | Unlicense, incluindo componentes MIT e ISC |
| Deno | MIT e avisos dos componentes distribuídos no runtime |
| curl-cffi | MIT; libcurl e componentes TLS mantêm seus próprios avisos |
| requests / urllib3 / certifi e demais dependências de rede | Licenças e avisos nos metadados distribuídos com cada pacote Python |

Este pacote foi preparado para uso pessoal local. Os termos de redistribuição de cada motor continuam aplicáveis caso o pacote seja compartilhado. Fontes do Windows usadas nos testes não fazem parte do instalador. As origens e os hashes dos pacotes estão em `engines.json`.

Não existe uma licença única concedendo redistribuição de todos os motores. Em particular, o ODA exige leitura dos termos oficiais, e os componentes GPL/AGPL têm obrigações próprias. O código próprio é disponibilizado sob AGPL-3.0, conforme [LICENSING.md](LICENSING.md). O repositório exclui motores, instaladores, arquivos baixados e dados locais. Essa seleção não equivale à aprovação de redistribuição do instalador completo.
