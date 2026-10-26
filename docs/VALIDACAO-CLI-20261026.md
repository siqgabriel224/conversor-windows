# Recuperação da linha de comando

26/10/2026, Windows x64, aplicativo 0.3.1.

## Causa e recuperação

Os eventos 3077 e 3033 do Code Integrity registraram o bloqueio de `conversor-cli.dll`, com erro `0x800711C7`. O componente não tinha assinatura digital; não havia certificado de assinatura de código disponível no perfil do usuário.

Foi restaurada a cópia anterior intacta do pequeno lançador. A interface, os workers e os motores atuais foram mantidos. O lançador apenas chama `Conversor.Protocol.RunCli(args)`, portanto a comunicação e a conversão continuam usando a implementação do aplicativo 0.3.1.

SHA-256 do lançador restaurado: `079DDF2C676A649800A959C9527E363FBE15081E9C5CD4DCAA55F850E9C3E24D`.

Não foram alteradas políticas de integridade, antivírus, exclusões, certificados confiáveis, modo de teste ou marcas de origem. A execução foi feita pelo EXE e pelo CMD normais da instalação. O Windows continuou avaliando os arquivos.

## Testes executados

- `conversor-cli.exe --help`: código zero e instruções exibidas.
- `conversor.cmd convert`: PNG 64 × 32 para WEBP 32 × 16, qualidade 90, caminho com acentos, resposta JSON de sucesso e código zero.
- Repetição pelo EXE: segundo WEBP com sufixo `(1)`, preservando o primeiro resultado.
- Formato incompatível: JSON com erro em português e código 1, sem agendar uma conversão inválida.
- Partida sem a interface em execução: a CLI iniciou o aplicativo com `--background` e concluiu PNG para JPEG 16 × 8.
- As imagens geradas foram carregadas com Pillow; dimensões e formatos foram conferidos. O hash do PNG original não mudou.
- Nenhum novo evento 3077/3033 relacionado à CLI foi encontrado durante as conversões aprovadas.

Uma tentativa imediatamente após encerramento forçado do processo recebeu `Pipe is broken`, sem registrar bloqueio de integridade. A repetição com o processo anterior já encerrado iniciou a interface e converteu normalmente. Isso não foi tratado como um novo bloqueio de segurança.

As amostras temporárias e seus registros de histórico foram removidos ao terminar. O aplicativo permanece em segundo plano.

## Empacotamento

`Publish-Cli.ps1` reaproveita a cópia local funcional em `dist/cli-verified` quando os hashes do código de entrada e do projeto CLI continuam iguais e os quatro arquivos do lançador conferem com o manifesto. O script também executa `--help` contra a publicação atual para verificar a compatibilidade. Mudanças no código CLI invalidam esse reaproveitamento e exigem nova compilação e validação.

O cache fica fora do código-fonte exportado. Em outra máquina ou sem o cache, a CLI é compilada normalmente; uma compilação nova sem assinatura pode depender da política do Windows daquela máquina. O cache não concede confiança nem cria uma exceção de segurança.

Para distribuição previsível de novas versões, a solução de publicação é assinar os componentes com um certificado emitido por um provedor confiável. Não foi obtido ou instalado um certificado nesta recuperação. Referências: [assinatura para Smart App Control](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control) e [diagnóstico de App Control](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting).
