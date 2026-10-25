# Estado de validação

As verificações automáticas ficam em [GitHub Actions](https://github.com/brunnojob/devpulse-usb/actions/workflows/tests.yml). O resultado deve ser conferido para o commit utilizado; um teste verde de código anterior não valida uma mudança nova.

## Verificações automatizadas

| Camada | Cobertura |
| --- | --- |
| Python | 14 testes: contrato, alertas, taxas, sensor de rede ausente, falha serial, backoff, captura real, CLI e proteção contra sobrescrita |
| Sessões web | 6 testes: parser, limites, séries inválidas, média com tempo irregular, captura única e escala temporal |
| Enquadramento C++ | Limite do buffer, CRLF, descarte de overflow, recuperação e múltiplos pacotes |
| Qualidade | Ruff e Prettier; sintaxe JavaScript |

O CI verifica o agente em Python 3.10 e 3.12, em Windows, Linux e macOS. As falhas de serial são simuladas. O parser C++ roda com sanitizers no Linux. Os testes do leitor web são executados em Node e não comprovam a interação no navegador.

A compilação completa do sketch e sua execução física continuam pendentes de configuração da placa. O perfil padrão bloqueia a compilação até a identificação do hardware. A foto original mostra os dados do próprio ESP32, não a execução deste firmware com dados do PC.

## Reproduzir uma captura

```sh
python agent.py --record teste.ndjson --duration 60
```

1. Abra o arquivo na bancada do Pages.
2. Confira o total de amostras e percorra a primeira e a última leitura.
3. Compare com uma segunda captura do mesmo trabalho e intervalo.
4. Inspecione o arquivo: há apenas métricas, estado de alerta e tempo relativo, sem hostname, usuário ou caminhos coletados.

## Ainda precisa de bancada física

- Confirmar a placa, ligações, controlador e offsets da tela.
- Compilar, gravar e registrar versões das bibliotecas.
- Conferir métricas com o monitor do sistema, respeitando as janelas de amostragem.
- Verificar alerta, legibilidade, consumo e cintilação.
- Encerrar o agente, testar estado desatualizado e recuperar uma desconexão USB real.
- Injetar linhas inválidas e longas e observar a recuperação do display.

Uma demonstração pública do painel lendo o PC precisa mostrar essa execução. A foto isolada não demonstra a integração.
