"""Utilitários puros da interface CLI.

Este módulo concentra pequenas transformações e validações usadas pelo loop da
UI. Mantê-las fora dos componentes deixa os métodos principais mais curtos e
facilita testes futuros sem depender de terminal ou Rich.
"""

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar


T = TypeVar("T")


EXIT_KEYS = ("\x03", "\x04")
ENTER_KEYS = ("\r", "\n")
BACKSPACE_KEYS = ("\x7f", "\x08")

EXIT_COMMANDS = {"/exit", "/sair", "/quit"}
CLEAR_COMMANDS = {"/clear", "/limpar"}
HELP_COMMANDS = {"/help", "/menu", "/ajuda"}

CODE_REQUEST_KEYWORDS = ("código", "codigo", "code", "exemplo")


@dataclass(frozen=True)
class EscapeSequence:
    """Representa uma tecla especial recebida como sequência ANSI."""

    key: str
    next_index: int


@dataclass(frozen=True)
class VisibleWindow(Generic[T]):
    """Fatia visível de uma coleção paginada pela UI."""

    items: list[T]
    first_index: int
    last_index: int
    scroll_offset: int


def normalize_message(text: str) -> str:
    """Remove espaços externos de uma mensagem digitada pelo usuário."""
    return text.strip()


def command_name(text: str) -> str:
    """Extrai o nome normalizado de um comando iniciado com '/'."""
    return text.split()[0].lower()


def is_command(text: str) -> bool:
    """Indica se a mensagem digitada deve ser tratada como comando."""
    return text.startswith("/")


def is_exit_key(char: str) -> bool:
    """Indica se o caractere encerra a aplicação."""
    return char in EXIT_KEYS


def is_enter_key(char: str) -> bool:
    """Indica se o caractere envia a mensagem atual."""
    return char in ENTER_KEYS


def is_backspace_key(char: str) -> bool:
    """Indica se o caractere remove o último item do buffer."""
    return char in BACKSPACE_KEYS


def is_escape_key(char: str) -> bool:
    """Indica se o caractere inicia uma sequência ESC/ANSI."""
    return char == "\x1b"


def has_ansi_prefix(text: str, index: int) -> bool:
    """Valida se há uma sequência ANSI iniciando no índice informado."""
    return index + 1 < len(text) and text[index + 1] == "["


def parse_escape_sequence(text: str, start_index: int) -> EscapeSequence:
    """Converte uma sequência ANSI em uma tecla semântica simples.

    Retorna `unknown` quando a sequência não é uma navegação suportada.
    """
    index = start_index + 2
    params = ""

    while index < len(text) and (text[index].isdigit() or text[index] == ";"):
        params += text[index]
        index += 1

    final_char = text[index] if index < len(text) else ""
    next_index = index + 1 if index < len(text) else index

    if final_char == "A":
        return EscapeSequence("up", next_index)
    if final_char == "B":
        return EscapeSequence("down", next_index)
    if final_char == "~" and params == "5":
        return EscapeSequence("page_up", next_index)
    if final_char == "~" and params == "6":
        return EscapeSequence("page_down", next_index)

    return EscapeSequence("unknown", next_index)


def visible_message_limit(terminal_height: int) -> int:
    """Calcula quantos cards de mensagem cabem na área de respostas."""
    available_height = max(6, terminal_height - 21)
    return max(1, available_height // 5)


def visible_window(
    items: Sequence[T],
    *,
    max_items: int,
    scroll_offset: int,
) -> VisibleWindow[T]:
    """Calcula a fatia visível de uma coleção com scroll pelo final."""
    total_items = len(items)
    if total_items == 0:
        return VisibleWindow([], 0, 0, 0)

    safe_scroll_offset = min(max(0, scroll_offset), total_items - 1)
    visible_count = max(1, min(max_items, total_items))

    last_index = total_items - safe_scroll_offset
    first_index = max(0, last_index - visible_count)

    if last_index <= first_index:
        last_index = total_items
        first_index = max(0, last_index - visible_count)
        safe_scroll_offset = 0

    return VisibleWindow(
        items=list(items[first_index:last_index]),
        first_index=first_index,
        last_index=last_index,
        scroll_offset=safe_scroll_offset,
    )


def contains_code_request(text: str) -> bool:
    """Indica se a mensagem parece pedir exemplo de código."""
    lowered_text = text.lower()
    return any(keyword in lowered_text for keyword in CODE_REQUEST_KEYWORDS)
