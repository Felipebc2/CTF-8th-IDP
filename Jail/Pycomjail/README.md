# Pycomjail

Desafio da categoria Jail: interaja com um interpretador Python restrito e encontre uma forma de ler a flag. O código exibido pelo serviço está em [main.py](main.py), e a análise está no [write-up](WRITEUP.md).

**Enunciado:** “Agora sim eu quero ver.”

## Arquivos

- [main.py](main.py): cópia do código apresentado pelo serviço.
- [payload.txt](payload.txt): entrada Python usada na solução. O arquivo contém apenas a linha enviada ao interpretador.

## Conexão

Inicie uma instância na plataforma e use o endereço e a porta fornecidos para enviar o payload:

```sh
cat payload.txt | nc <HOST> <PORTA>
```

O servidor imprime seu código e, em seguida, processa a linha recebida. A solução usa o descritor `3`, que correspondeu ao arquivo da flag no ambiente observado.

## Reprodução local

O programa apaga `flag.txt` no diretório em que é executado. Para testar com segurança, use um diretório temporário e uma flag fictícia:

```sh
mkdir -p /tmp/pycomjail-demo
cd /tmp/pycomjail-demo
printf 'IDP{teste_local}\n' > flag.txt
python3 /caminho/para/Jail/Pycomjail/main.py < /caminho/para/Jail/Pycomjail/payload.txt
```

Substitua os caminhos pelos correspondentes ao seu checkout. O resultado depende de o arquivo receber o descritor `3` no processo de teste.
