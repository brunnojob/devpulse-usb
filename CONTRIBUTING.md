# Contribuir com DevPulse USB

Um relato reproduzível vale mais do que uma promessa de compatibilidade.

Para problemas no agente, informe sistema operacional, versão do Python, comando utilizado, comportamento esperado e erro observado. Para problemas de hardware, inclua modelo exato da placa, controlador da tela, biblioteca/versão e um esquema ou exemplo público do fabricante. Remova dados pessoais das capturas antes de publicá-las.

## Executar as verificações

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m pip install ruff==0.17.2
python -m ruff check .
python -m ruff format --check .
npm ci
npm test
npm run format:check
```

Para o parser C++ nativo:

```sh
g++ -std=c++11 -Wall -Wextra -Werror tests/framer_test.cpp -o framer-test
./framer-test
```

O CI executa esse parser também com AddressSanitizer e UndefinedBehaviorSanitizer no Linux. Isso testa enquadramento de bytes; não substitui compilar e rodar o sketch na placa.

Mantenha mudanças de protocolo compatíveis ou altere explicitamente a versão. Adicione casos que exercitem o erro corrigido: escrita parcial, pacote malformado, reinício de contador, lacuna ou timestamp regressivo, por exemplo.

Perfis de placas precisam de identificação e verificação física antes de serem descritos como suportados. Não substitua métricas indisponíveis por números aleatórios.
