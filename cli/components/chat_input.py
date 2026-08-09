"""Componente de entrada de texto do chat.

Renderiza uma caixa de prompt compacta no rodapé, inspirada em TUIs de agentes
de código: borda discreta, dica curta e foco no texto digitado.
"""

from rich import box
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .theme import (
    PURPLE_INPUT_BG,
    PURPLE_PRIMARY,
    SURFACE_BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
)

# Caractere usado para simular o cursor dentro da caixa de entrada.
CURSOR_BLOCK = "█"


class ChatInput:
    """Linha de prompt centralizada no rodapé do chat.

    Guarda o texto digitado e fornece métodos para manipulá-lo, além de
    renderizar a própria linha com o símbolo de prompt e o cursor.
    """

    def __init__(self, prompt: str = "›") -> None:
        # Símbolo exibido antes do conteúdo digitado (identifica a entrada).
        self.prompt = prompt
        # Buffer com o conteúdo atual digitado pelo usuário.
        self.buffer = ""

    def append(self, char: str) -> None:
        """Adiciona um caractere ao final do buffer."""
        self.buffer += char

    def backspace(self) -> None:
        """Remove o último caractere digitado."""
        if self.buffer:
            self.buffer = self.buffer[:-1]

    def clear(self) -> None:
        """Limpa todo o conteúdo digitado."""
        self.buffer = ""

    def value(self) -> str:
        """Devolve o conteúdo atual da caixa de entrada."""
        return self.buffer

    def render(self) -> RenderableType:
        """Monta e devolve a caixa de prompt da entrada."""
        placeholder = "Digite uma mensagem, /help para comandos"
        typed_text = self.buffer if self.buffer else placeholder
        typed_style = Style(color=TEXT_PRIMARY) if self.buffer else Style(color=TEXT_DIM)

        input_line = Text.assemble(
            (f"{self.prompt} ", Style(color=PURPLE_PRIMARY, bold=True)),
            (typed_text, typed_style),
            (CURSOR_BLOCK, Style(color=PURPLE_PRIMARY)),
        )

        return Panel(
            input_line,
            title="[chat.dim]mensagem[/]",
            title_align="left",
            subtitle="[chat.dim]Enter envia[/]",
            subtitle_align="right",
            border_style=SURFACE_BORDER,
            style=Style(bgcolor=PURPLE_INPUT_BG),
            box=box.ROUNDED,
            padding=(0, 1),
        )
