# DevPulse USB

Um painel físico para acompanhar o computador enquanto você programa.
Firmware Arduino `.ino`, telemetria local em Python e um único cabo USB para alimentação e dados. Por brunnodev — https://brunnodev.store

![Protótipo de referência do autor](assets/prototype-reference.png)

> A foto é a referência de hardware fornecida pelo autor: nela, a tela mostra os dados do próprio ESP32-C6. Ela não demonstra o firmware DevPulse nem medições do computador. Esta primeira versão ainda precisa de configuração e validação na placa física.

## Página de apresentação

https://brunnojob.github.io/devpulse-usb/

A página inclui guia de instalação e prévia interativa com dados ilustrativos; o navegador não coleta métricas do PC. O monitoramento real é feito pelo agente Python.

## O problema

Durante uma compilação ou execução pesada, um painel separado permite acompanhar a máquina sem trocar de janela. A proposta é um projeto aberto, reproduzível e local, que possa evoluir para diagnóstico de ambientes de desenvolvimento.

## Implementado nesta base

- Uso de CPU e RAM do computador.
- Ocupação do volume selecionado (não mede atividade de leitura/escrita).
- Tráfego agregado de rede em KiB/s; inclui interfaces virtuais e loopback conforme o sistema operacional.
- Alerta quando CPU ou RAM ficam em pelo menos 90% durante dez segundos contínuos.
- Reconexão à porta explicitamente escolhida.
- Mensagem de dados desatualizados após cinco segundos sem pacote válido.
- Protocolo JSON por linha, versionado e sem comandos de execução no firmware.
- Modo de saída no terminal para testar o agente sem a placa.

Não há Wi-Fi, conta, servidor ou envio de telemetria à internet no código do projeto. A instalação das dependências usa a internet.

## O que ainda depende de hardware

A foto identifica o texto ESP32-C6, mas não confirma o modelo comercial da placa, controlador da tela, pinos, offsets, polaridade do backlight ou geometria. O perfil fornecido é apenas um ponto de partida para uma tela SPI **confirmada como ST7789**. Não selecione esse controlador por semelhança visual.

`BOARD_CONFIGURED=0` bloqueia a compilação até a configuração explícita. Se o controlador for outro, adapte também o driver do firmware. Não há alegação de compatibilidade já testada com a placa da foto. A atualização atual redesenha a tela inteira e poderá apresentar cintilação; a otimização depende de testes físicos.

## Agente no PC

Python 3.10 ou mais recente. APIs escolhidas para Windows, Linux e macOS, mas estes sistemas ainda precisam de validação prática com a placa.

```sh
python -m venv .venv
```

Ative o ambiente:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```sh
# Linux / macOS
source .venv/bin/activate
```

```sh
python -m pip install -r requirements.txt
python agent.py --list
python agent.py --stdout
python agent.py --port COM5
```

No Linux, por exemplo: `python agent.py --port /dev/ttyACM0`. Em macOS use o caminho listado por `--list`. Selecione o dispositivo correto. O programa não tenta abrir todas as portas automaticamente. Feche o Monitor Serial da IDE antes de iniciar o agente. Algumas placas reiniciam ao abrir a conexão; os pacotes seguintes atualizam a tela.

`--disk C:\` no Windows, ou `--disk /home` no Linux, seleciona o volume. `--interval` aceita 0.25 a 2 segundos, padrão 1. O agente não requer elevação por projeto; acesso à porta pode depender de permissões locais e drivers da placa.

## Firmware

1. Identifique a placa e consulte seu esquema ou o exemplo funcional do fabricante.
2. Instale o suporte Arduino-ESP32 da Espressif na Arduino IDE.
3. Instale ArduinoJson **7**, Adafruit GFX Library e Adafruit ST7735 and ST7789 Library pelo gerenciador de bibliotecas.
4. Abra `firmware/DevPulse/DevPulse.ino`.
5. Em `board_config.h`, preencha controlador compatível, MOSI, SCLK, CS, DC, RST, backlight, dimensões e rotação. Alguns painéis também exigem offsets específicos; adapte a inicialização ao exemplo do fabricante.
6. A interface atual espera uma área útil horizontal de pelo menos 240 × 160 pixels. Os valores 172 × 320 com rotação 1 são **placeholders**, não uma identificação da sua tela.
7. Só então altere `BOARD_CONFIGURED` para `1`.
8. Se usar USB nativo do ESP32-C6, habilite **USB CDC On Boot**. Para placas com ponte USB/UART, siga o perfil do fabricante. Use cabo com dados.
9. Grave, feche o monitor serial e inicie o agente no computador.

## Protocolo v1

115200 baud; um objeto ASCII JSON por linha, terminado por LF. Exemplo:

```json
{"v":1,"cpu":31.2,"ram":58.0,"disk":44.0,"rx":22.4,"tx":3.1,"alert":"OK"}
```

Percentuais devem estar entre 0 e 100; rede é não negativa. Alertas válidos: `OK`, `CPU`, `RAM`, `CPU+RAM`. Pacotes incompletos, inválidos ou maiores que o buffer de 255 bytes são descartados. Após overflow o parser espera LF antes de aceitar outro pacote. O estado fica desatualizado se o agente parar de enviar pacotes válidos; isso não distingue falha física do USB de encerramento do agente.

Não há handshake nem confirmação de entrega nesta versão. Não há GPU, temperatura de CPU ou FPS: essas leituras precisam de provedores específicos e não devem ser substituídas por números simulados.

## Validação

```sh
python -m unittest discover -s tests
```

Quatro testes cobrem alerta contínuo, reinício de contadores, enquadramento do pacote e rejeição de métricas inválidas. Os testes não comprovam renderização, USB físico ou compilação Arduino. Consulte `docs/VALIDATION.md`.

## Próximos diferenciais

Estas são propostas, ainda não implementadas:

- Cronômetro de build ligado a comandos locais escolhidos pelo usuário.
- Histórico por projeto para comparar compilações no mesmo computador.
- Adaptadores de GPU e temperatura com indicação explícita de sensor indisponível.
- Perfis verificados de placas, com esquema e instruções reproduzíveis.
- Atualização parcial da tela para reduzir cintilação.

Monitores USB não são uma categoria inédita. O objetivo é desenvolver uma ferramenta autoral com foco em diagnóstico de trabalho de desenvolvimento, sem prometer detectar automaticamente a causa de lentidão apenas por percentuais de uso.

## Referências

- USB serial no ESP32-C6: https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/get-started/establish-serial-connection.html
- USB CDC em Arduino-ESP32: https://github.com/espressif/arduino-esp32/blob/master/docs/en/tutorials/cdc_dfu_flash.rst
- psutil: https://psutil.readthedocs.io/stable/index.html
- ArduinoJson: https://arduinojson.org/v7/api/json/deserializejson/
- Biblioteca de display: https://github.com/adafruit/Adafruit-ST7735-Library
- Projeto existente na mesma categoria: https://github.com/mathoudebine/turing-smart-screen-python

## Autor e licença

brunnodev — https://brunnodev.store

Código sob licença MIT. A licença do código não concede direitos sobre marcas de fabricantes.
