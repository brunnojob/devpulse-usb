# Estado de validação

## Executado no ambiente de desenvolvimento

- Quatro testes unitários do agente Python: aprovados.
- Validação sintática do agente: aprovada.
- Teste do agente com psutil 7.2.2 e pyserial 3.5 neste ambiente Linux: coleta e serialização de uma amostra real aprovadas, sem placa conectada.

## Ainda não executado

- Compilação do firmware Arduino com perfil real de placa.
- Gravação e execução no ESP32-C6 da fotografia.
- Teste de desconexão/reconexão USB física.
- Leitura real de sensores em Windows, Linux e macOS.
- Teste visual de controlador, geometria, cores e backlight.
- Medição de consumo e latência.

## Critérios para demonstração pública

1. Confirmar o código da placa e registrar o esquema correspondente.
2. Compilar e gravar usando versões de bibliotecas registradas.
3. Conferir as métricas com o monitor do sistema; diferenças pequenas decorrem das janelas de amostragem.
4. Executar uma carga conhecida: confirmar alerta somente após dez segundos e limpeza ao cair abaixo de 90%.
5. Encerrar o agente e conferir indicação de dados desatualizados após cinco segundos.
6. Reconectar o cabo e confirmar recuperação sem reiniciar o agente.
7. Enviar pacote malformado ou muito longo e verificar recuperação na linha seguinte.
8. Gravar vídeo da leitura do PC. A foto original sozinha demonstra apenas os dados do ESP32.
