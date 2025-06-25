# HolyPython v0.0.1

HolyPython é uma linguagem de programação didática inspirada em Python e C, que permite tanto interpretar quanto compilar seus códigos para Assembly bootável x86. O projeto é multiplataforma e colorido, com recursos de memória, includes, variáveis, input e até compilação para um `.asm` que pode se tornar um sistema operacional mínimo!

---

## Características

- **Sintaxe inspirada em Python e C**
- **Execução interpretada em Python (`interpreter.py`)**
- **Compilação para Assembly x86 bootável** (`.asm` → `.bin`)
- **Cores no terminal** usando tags (`[red]`, `[green]`, etc)
- **Memória simulada com `poke` e `peek`**
- **Includes de outros arquivos `.hpy`**
- **Variáveis, input (caractere), if/else, comentários**
- **Geração automática de `.asm` para boot em QEMU/Bochs**

---

## Instalação

1. **Clone este repositório ou copie os arquivos.**
2. Instale o Python 3.x.
3. Instale a biblioteca de cores:
   ```bash
   pip install colorama
   ```
4. (Para compilar o `.asm` em `.bin` bootável) Instale o NASM:
   - Linux: `sudo apt install nasm`
   - Windows: [nasm.us](https://www.nasm.us/)

---

## Comandos disponíveis em HolyPython

| Comando                        | Descrição                                                    |
|--------------------------------|--------------------------------------------------------------|
| `print("texto")`               | Imprime texto, aceita tags de cor.                           |
| `poke(addr, val)`              | Escreve valor em endereço fictício da memória HolyPython.    |
| `peek(addr)`                   | Lê valor do endereço fictício da memória HolyPython.         |
| `input("mensagem")`            | Lê um caractere do teclado, salvo em variável.               |
| `int x = 5;` / `x = 10`        | Declara e atribui valores inteiros.                          |
| `if (x == 5): ... else: ...`   | Condicional simples (==).                                    |
| `include "outro.hpy"`          | Inclui outro arquivo HolyPython.                             |
| Comentários `//` ou `#`        | Ignorados no código.                                         |

### Exemplo de arquivo main.hpy

```c
include "lib.hpy"
int x = 2;
print("[red]Hello, Boot![/red]")
poke(10, 77)
if (x == 2):
    print("[green]X é 2![/green]")
else:
    print("[yellow]X não é 2![/yellow]")
nome = input("[cyan]Digite a inicial do seu nome: [/cyan]")
print("Você digitou: " + nome)
print("Valor em poke(10):")
print(peek(10))
```

---

## Cores suportadas

| Tag        | Cor exibida   |
|------------|---------------|
| `[red]`    | Vermelho      |
| `[green]`  | Verde         |
| `[yellow]` | Amarelo       |
| `[blue]`   | Azul          |
| `[magenta]`| Magenta       |
| `[cyan]`   | Ciano         |
| `[white]`  | Branco        |
| `[black]`  | Preto         |
| `[reset]`  | Reset         |

**Exemplo:**
```python
print("[red]Alerta![/red] [green]Sucesso![/green] [blue]Azul![/blue]")
```

---

## Uso do interpretador

```bash
python interpreter.py
```
Você verá o menu:
- Digite `1` para rodar um arquivo `.hpy`
- Digite `2` para compilar um `.hpy` para Assembly bootável (`.asm`).  
  Compile manualmente para `.bin` se quiser rodar em emulador.

---

## Compilando para Assembly e Bootando

1. **Gere o `.asm`**
   ```bash
   python interpreter.py
   # escolha opção 2, informe seu arquivo .hpy
   ```
2. **Compile para binário bootável**
   ```bash
   nasm -f bin seu_arquivo.asm -o output.bin
   ```
3. **Rode no QEMU**
   ```bash
   qemu-system-x86_64 -drive format=raw,file=output.bin
   ```
   Ou outro emulador/VM x86.

---

## O que está incluso (v0.0.1)

- `interpreter.py` — interpretador e compilador para `.asm`
- Suporte a todas as features listadas acima
- Exemplo de `main.hpy` e includes

---

## Limitações da v0.0.1

- Só suporta condicional `==`
- Apenas input de um caractere
- Somente variáveis inteiras
- Laços, funções e strings dinâmicas não implementados
- Bootável: apenas output de texto, sem SO real

---

## Licença

O Autor

---

## Autor

@Johnzin-WakaWaka

---
