# Validação da versão 0.3

Verificação local em 26/10/2026, Windows x64. Os resultados são específicos das amostras abaixo.

## Playlist real pela interface

Na aba **Baixar vídeos**, foi consultada a playlist pública [JODA15](https://www.youtube.com/playlist?list=PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu), de milan. Foram selecionados playlist inteira, vídeo com áudio, MP4 e **Até 240p**. O primeiro item oferece 240p e 144p. Os quatro itens foram salvos e o Histórico registrou Concluído, sem avisos.

| Item | ID | Dimensões | Áudio | Duração de saída | Decodificação completa |
|---|---|---|---|---|---|
| JOD | yN-Q-tFFElc | 320 × 240 | AAC | 516,087 s | Sem erros |
| JOD2 | aVjGozRKnS0 | 320 × 240 | AAC | 362,417 s | Sem erros |
| JOD3 | BdvQkoF6Jq4 | 320 × 240 | AAC | 162,563 s | Sem erros |
| JOD4 | DpNKHkMbULM | 320 × 240 | AAC | 154,041 s | Sem erros |

FFprobe conferiu resolução, duração e faixas. FFmpeg leu cada arquivo até o fim com `-xerror`, sem saída de erro e código zero. Arquivos salvos em Downloads/Conversor/Teste playlist 240p. Evidência local não distribuída: `tests/results/playlist-ui-validation.json`. O teste foi iniciado na interface 0.2 antes da atualização 0.3; o código do downloader não mudou nesta entrega.

## Redimensionamento

- 31 testes reais e de validação em `tests/test_resize_media.py`: posições de recorte por pixels conhecidos; PNG/JPG/WEBP; vídeo MP4/MKV/WEBM; modos recorte e faixas; dimensões, duração, áudio e decodificação completa; vídeo silencioso; prévias; EXIF; transparência; pixels não quadrados; rotação por metadados; conflitos; arquivos corrompidos; cancelamento antes e durante o FFmpeg.
- 53 testes offline do downloader e 7 regressões do worker: **91 testes aprovados** no conjunto. Relatório local: `tests/results/resize-release-final.xml`.
- A fixture de rotação usa `-display_rotation` e verifica a presença da matriz antes de testar. A sintaxe antiga de metadados não cria essa matriz no FFmpeg instalado. Referência: [documentação oficial](https://www.ffmpeg.org/ffmpeg.html#Video-Options).
- A matriz histórica de conversões não foi repetida inteira nesta entrega.

Na interface instalada 0.3, uma imagem PNG e um vídeo MP4 foram adicionados juntos pelo seletor. Foram processados em 1080 × 1920 (preset TikTok/Shorts, recorte central) e novamente em 600 × 400 (largura 600, proporção digitada 3:2, Aplicar, modo com faixas). As prévias de imagem e vídeo carregaram. Os quatro trabalhos concluíram no Histórico. Medidas e decodificação dos arquivos finais foram conferidas separadamente.

## Limites

O recorte usa nove posições fixas; não há desenho livre de retângulo ou acompanhamento de rosto. A prévia mostra um quadro estático. Vídeos mantêm a duração, com nova compressão de imagem e áudio. Não há corte temporal nesta ferramenta. GIF/TIFF usam apenas a primeira imagem. O formato escolhido é geométrico; não constitui garantia de aceitação por uma plataforma social.

Os testes não simulam todos os dispositivos, arquivos muito longos, espaço esgotado, HDR ou formatos incomuns. Reinicialização do Windows e instalação limpa sem rede não foram repetidas nesta versão.
