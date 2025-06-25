import re
import os
from colorama import init, Fore, Style

init(autoreset=True)

COLOR_MAP = {
    "red": Fore.RED,
    "green": Fore.GREEN,
    "yellow": Fore.YELLOW,
    "blue": Fore.BLUE,
    "magenta": Fore.MAGENTA,
    "cyan": Fore.CYAN,
    "white": Fore.WHITE,
    "black": Fore.BLACK,
    "reset": Style.RESET_ALL,
}

def color_print(text):
    text = str(text)
    def repl(match):
        color = match.group(1).lower()
        return COLOR_MAP.get(color, Style.RESET_ALL)
    text = re.sub(r'\[([a-zA-Z]+)\]', repl, text)
    text = re.sub(r'\[\/[a-zA-Z]+\]', Style.RESET_ALL, text)
    print(text + Style.RESET_ALL)

class HolyPyMemory:
    def __init__(self, size=256):
        self.mem = [0] * size
    def poke(self, addr, val):
        self.mem[addr] = val
    def peek(self, addr):
        return self.mem[addr]

memory = HolyPyMemory()

user_env = {
    "poke": memory.poke,
    "peek": memory.peek,
    "print": color_print,
    "input": input,
}

def preprocess_holypy(code, base_path=""):
    lines = code.splitlines()
    result = []
    for line in lines:
        line = re.sub(r"//.*", "", line)
        line = re.sub(r"#.*", "", line)
        if m := re.match(r'\s*include\s+"([^"]+)"', line):
            inc_path = os.path.join(base_path, m.group(1))
            if os.path.isfile(inc_path):
                with open(inc_path, encoding="utf-8") as f:
                    inc_code = preprocess_holypy(f.read(), os.path.dirname(inc_path))
                    result.append(inc_code)
            continue
        line = re.sub(r'\bint\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);', r'\1 = \2', line)
        line = re.sub(r'\bint\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;', r'\1 = 0', line)
        line = re.sub(r'\bfloat\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);', r'\1 = \2', line)
        line = re.sub(r'\bfloat\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;', r'\1 = 0.0', line)
        line = re.sub(r'\bstr\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^;]+);', r'\1 = \2', line)
        line = re.sub(r'\bstr\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;', r'\1 = ""', line)
        line = re.sub(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{', r'class \1:', line)
        line = re.sub(r'if\s*\((.+)\)\s*\{', r'if \1:', line)
        line = re.sub(r'elif\s*\((.+)\)\s*\{', r'elif \1:', line)
        line = re.sub(r'else\s*\{', r'else:', line)
        line = re.sub(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*\{', r'def \1(\2):', line)
        line = re.sub(r';\s*$', '', line)
        line = re.sub(r'^\s*\}+\s*', '', line)
        line = line.replace('}', '')
        if line.strip():
            result.append(line)
    return "\n".join(result)

def run_hpy_file(filename):
    with open(filename, encoding="utf-8") as f:
        code = f.read()
    py_code = preprocess_holypy(code, os.path.dirname(filename))
    exec(py_code, user_env)

# --- COMPILAÇÃO PARA ASM ---

ASM_PROLOGUE = """
[BITS 16]
[ORG 0x7C00]

section .data
"""

ASM_MESSAGE_TEMPLATE = "msg{idx}: db {msg_bytes}, 0\n"

ASM_VAR_TEMPLATE = "{var}: dw {value}\n"

ASM_MEMORY = "hpmem: times 256 db 0\n"  # 256 bytes de memória HolyPython

ASM_MAIN_START = """
section .text
start:
    mov ax, 0x07C0
    mov ds, ax
"""

ASM_EPILOGUE = """
    cli
    hlt

times 510-($-$$) db 0
dw 0xAA55
"""

def get_all_lines(filename, already_included=None):
    if already_included is None:
        already_included = set()
    if filename in already_included:
        return []
    already_included.add(filename)
    lines = []
    with open(filename, encoding="utf-8") as f:
        code = f.read()
    for inc in re.findall(r'include\s+"([^"]+)"', code):
        inc_path = os.path.join(os.path.dirname(filename), inc)
        if os.path.isfile(inc_path):
            lines += get_all_lines(inc_path, already_included)
    for l in code.splitlines():
        if l.strip().startswith("include"):
            continue
        if "//" in l:
            l = l[:l.index("//")]
        if "#" in l:
            l = l[:l.index("#")]
        if l.strip():
            lines.append(l)
    return lines

def parse_hpy_to_asm(filename, outname=None):
    lines = get_all_lines(filename)
    asm_data = ""
    asm_vars = ""
    asm_code = ASM_MAIN_START
    msg_idx = 0
    var_table = {}
    var_vals = {}
    label_idx = 0

    for line in lines:
        line = line.strip()
        m = re.match(r"int\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?\d+)", line)
        if m:
            vname, vval = m.group(1), int(m.group(2))
            var_table[vname] = f"var_{vname}"
            var_vals[vname] = vval
            continue
        m = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?\d+)", line)
        if m:
            vname, vval = m.group(1), int(m.group(2))
            if vname not in var_table:
                var_table[vname] = f"var_{vname}"
                var_vals[vname] = vval
            else:
                asm_code += f"    mov word [{var_table[vname]}], {vval}\n"
            continue
        m = re.match(r'print\s*\(\s*[\'"](.+)[\'"]\s*\)', line)
        if m:
            msg = m.group(1)
            msg_bytes = ", ".join(str(ord(c)) for c in msg)
            asm_data += ASM_MESSAGE_TEMPLATE.format(idx=msg_idx, msg_bytes=msg_bytes)
            asm_code += f"    mov si, msg{msg_idx}\n"
            asm_code += "    call print_str\n"
            msg_idx += 1
            continue
        m = re.match(r'poke\s*\(\s*(\d+)\s*,\s*(-?\d+)\s*\)', line)
        if m:
            addr, val = int(m.group(1)), int(m.group(2))
            asm_code += f"    mov byte [hpmem+{addr}], {val}\n"
            continue
        m = re.match(r'print\s*\(\s*peek\s*\(\s*(\d+)\s*\)\s*\)', line)
        if m:
            addr = int(m.group(1))
            asm_code += f"    mov al, [hpmem+{addr}]\n"
            asm_code += f"    call print_al_byte\n"
            continue
        m = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*input\s*\(\s*[\'\"](.*)[\'\"]\s*\)', line)
        if m:
            vname, prompt = m.group(1), m.group(2)
            msg_bytes = ", ".join(str(ord(c)) for c in prompt)
            asm_data += ASM_MESSAGE_TEMPLATE.format(idx=msg_idx, msg_bytes=msg_bytes)
            asm_code += f"    mov si, msg{msg_idx}\n"
            asm_code += "    call print_str\n"
            msg_idx += 1
            if vname not in var_table:
                var_table[vname] = f"var_{vname}"
                var_vals[vname] = 0
            asm_code += "    xor ah,ah\n    int 16h\n"
            asm_code += f"    mov [{var_table[vname]}], al\n"
            continue
        m = re.match(r'if\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*(-?\d+)\s*\)\s*\:', line)
        if m:
            vname, val = m.group(1), int(m.group(2))
            label = f"endif_{label_idx}"
            asm_code += f"    mov ax, [{var_table[vname]}]\n"
            asm_code += f"    cmp ax, {val}\n"
            asm_code += f"    jne {label}\n"
            label_idx += 1
            continue
        if line.strip() == "else:":
            label = f"endif_{label_idx-1}"
            asm_code += f"    jmp end{label}\n"
            asm_code += f"{label}:\n"
            continue
        if line.strip() == "":
            continue
        if line.startswith(' '):  # dentro do bloco
            asm_code += line + '\n'
        if re.match(r'#', line) or re.match(r'//', line):
            continue

    for v, asm_v in var_table.items():
        asm_vars += ASM_VAR_TEMPLATE.format(var=asm_v, value=var_vals[v])
    asm_vars += ASM_MEMORY

    asm_routines = """
print_str:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0x00
    mov bl, 0x07
    int 0x10
    jmp print_str
.done:
    ret

print_al_byte:
    push ax
    push bx
    mov ah, 0x0E
    mov bh, 0x00
    mov bl, 0x07
    int 0x10
    pop bx
    pop ax
    ret
"""

    asm = (
        ASM_PROLOGUE
        + asm_data
        + asm_vars
        + asm_code
        + asm_routines
        + ASM_EPILOGUE
    )
    if outname is None:
        outname = filename.replace(".hpy", ".asm")
    with open(outname, "w") as f:
        f.write(asm)
    print(f"{COLOR_MAP['green']}Assembly gerado: {outname}{Style.RESET_ALL}")
    print("Para compilar para binário bootável, use:")
    print(f"  nasm -f bin {outname} -o output.bin")
    print("E rode em um emulador como QEMU ou Bochs.")

if __name__ == "__main__":
    print(f"{COLOR_MAP['blue']}HolyPython Interpreter{Style.RESET_ALL}")
    print("Digite:")
    print("  1 para rodar um arquivo .hpy")
    print("  2 para gerar um .asm bootável (todos comandos HolyPython) de um .hpy (incluindo includes)")
    op = input("Sua escolha: ").strip()
    if op == "1":
        filename = input("Nome do arquivo .hpy para rodar: ").strip()
        if not filename.endswith(".hpy"):
            print(f"{COLOR_MAP['red']}O arquivo precisa ter extensão .hpy{Style.RESET_ALL}")
        elif not os.path.isfile(filename):
            print(f"{COLOR_MAP['red']}Arquivo '{filename}' não encontrado.{Style.RESET_ALL}")
        else:
            run_hpy_file(filename)
    elif op == "2":
        filename = input("Nome do arquivo .hpy para compilar para .asm: ").strip()
        if not filename.endswith(".hpy"):
            print(f"{COLOR_MAP['red']}O arquivo precisa ter extensão .hpy{Style.RESET_ALL}")
        elif not os.path.isfile(filename):
            print(f"{COLOR_MAP['red']}Arquivo '{filename}' não encontrado.{Style.RESET_ALL}")
        else:
            parse_hpy_to_asm(filename)
    else:
        print("Opção inválida.")