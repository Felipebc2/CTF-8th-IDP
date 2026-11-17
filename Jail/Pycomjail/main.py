#!/usr/bin/python3
# -*- coding: utf-8 -*-

import ast
import builtins
from inspect import getsource, getmodule, currentframe

print(getsource(getmodule(currentframe())))

BLOQUEADOS = {
    '__import__', 'breakpoint', 'help', 'getattr', 'setattr', 'delattr',
    'vars', 'globals', 'locals', 'eval', 'exec', 'compile', 'input', 'exit', 'quit',
}
SEGUROS = {k: v for k, v in vars(builtins).items() if k not in BLOQUEADOS}


def verifica(codigo):
    for no in ast.walk(ast.parse(codigo)):
        if isinstance(no, (ast.Import, ast.ImportFrom)):
            raise ValueError('import não permitido')
        nome = getattr(no, 'attr', None) or getattr(no, 'id', None)
        if nome and nome.startswith('_'):
            raise ValueError('nomes com _ não permitidos')


with open('./flag.txt'):
    import os, sys
    os.unlink('./flag.txt')
    sys.modules['os'] = None
    del os, sys

    while True:
        try:
            comando = input('>>> ')
            verifica(comando)
            exec(comando, {'__builtins__': SEGUROS})
        except EOFError:
            break
        except Exception as e:
            print(e)