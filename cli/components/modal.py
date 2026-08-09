"""Componente de modal/menu em formato CLI.

Renderiza uma janela discreta para comandos como /help. O visual segue a
mesma linguagem terminal-native dos demais componentes: borda roxa sutil,
fundo escuro e texto direto.
"""

from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style

from .theme import PURPLE_ASSISTANT_BG, PURPLE_BG, PURPLE_PRIMARY, SURFACE_BORDER


class Modal:
    """Janela modal simples para exibir menus e ajudas no CLI."""

    def __init__(self, title: str, body: str) -> None:
        # Título exibido na borda superior do modal.
        self.title = title
        # Corpo do modal (texto com markup rich).
        self.body = body

    def _panel(self) -> Panel:
        """Monta o painel central do modal."""
        return Panel(
            Align.center(self.body),
            title=f"[bold {PURPLE_PRIMARY}]{self.title}[/]",
            subtitle="[chat.dim]ESC para fechar[/]",
            subtitle_align="right",
            border_style=Style(color=SURFACE_BORDER),
            style=Style(bgcolor=PURPLE_ASSISTANT_BG),
            box=box.ROUNDED,
            padding=(1, 2),
            width=58,
        )

    def render(self) -> Layout:
        """Renderiza somente o modal, substituindo a tela atual do chat."""
        layout = Layout(name="modal-screen")
        layout.update(
            Panel(
                Align.center(self._panel(), vertical="middle"),
                border_style=Style(color=PURPLE_BG),
                style=Style(bgcolor=PURPLE_BG),
                box=box.SQUARE,
                padding=(1, 1),
            )
        )
        return layout
