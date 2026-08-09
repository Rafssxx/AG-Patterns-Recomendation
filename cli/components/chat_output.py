"""Componente de saída/resposta do chat.

Renderiza o histórico em blocos próprios, com fundos diferentes do painel
central. A intenção é manter a leitura de uma TUI de agente de código, mas
com cada mensagem claramente separada dentro da área de respostas.
"""

from dataclasses import dataclass

from rich import box
from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .theme import (
    PURPLE_ASSISTANT_BG,
    PURPLE_BG,
    PURPLE_BRIGHT,
    PURPLE_PRIMARY,
    PURPLE_USER_BG,
    SURFACE_BORDER,
    TEXT_DIM,
    TEXT_MUTED,
)
from ..utils import visible_window


@dataclass
class Message:
    """Uma única mensagem do chat (papel + conteúdo)."""

    role: str  # "user" (usuário) ou "assistant" (assistente)
    content: str  # conteúdo textual; markdown nas respostas do assistente


class ChatOutput:
    """Histórico de mensagens renderizado em blocos compactos.

    Mantém a conversa em memória e renderiza as respostas com suporte a
    Markdown, incluindo blocos de código destacados pelo Rich/Pygments.
    """

    def __init__(self) -> None:
        # Histórico de mensagens exibido na área de resposta.
        self.messages: list[Message] = []
        # 0 significa fim da conversa; valores maiores mostram mensagens antigas.
        self.scroll_offset = 0

    def add_user(self, content: str) -> None:
        """Adiciona uma mensagem do usuário ao histórico."""
        self.messages.append(Message(role="user", content=content))
        self.scroll_to_bottom()

    def add_assistant(self, content: str) -> None:
        """Adiciona uma resposta do assistente ao histórico."""
        self.messages.append(Message(role="assistant", content=content))
        self.scroll_to_bottom()

    def clear(self) -> None:
        """Remove todas as mensagens do histórico."""
        self.messages.clear()
        self.scroll_to_bottom()

    def scroll_to_bottom(self) -> None:
        """Volta a visualização para as mensagens mais recentes."""
        self.scroll_offset = 0

    def scroll_up(self, amount: int = 1) -> None:
        """Move a janela de mensagens para itens mais antigos."""
        if not self.messages:
            return

        self.scroll_offset = min(
            len(self.messages) - 1,
            self.scroll_offset + amount,
        )

    def scroll_down(self, amount: int = 1) -> None:
        """Move a janela de mensagens para itens mais recentes."""
        self.scroll_offset = max(0, self.scroll_offset - amount)

    def _message_panel(
        self,
        *,
        title: Text,
        body: RenderableType,
        background: str,
    ) -> Panel:
        """Envolve uma mensagem em um bloco visual próprio."""
        return Panel(
            Group(title, Padding(body, (0, 0, 0, 2))),
            border_style=SURFACE_BORDER,
            style=Style(bgcolor=background),
            box=box.ROUNDED,
            padding=(0, 1),
        )

    def _responses_panel(self, content: RenderableType, footer: str | None = None) -> Panel:
        """Monta o card que agrupa toda a área de respostas."""
        return Panel(
            content,
            title="[chat.dim]respostas[/]",
            title_align="left",
            subtitle=footer,
            subtitle_align="right",
            border_style=SURFACE_BORDER,
            style=Style(bgcolor=PURPLE_BG),
            box=box.ROUNDED,
            padding=(1, 1),
        )

    def _render_message(self, message: Message) -> RenderableType:
        """Renderiza uma única mensagem em um bloco com fundo próprio."""
        if message.role == "user":
            # Mensagens do usuário usam uma superfície própria dentro do painel.
            return Padding(
                self._message_panel(
                    title=Text.assemble(
                        ("● ", PURPLE_BRIGHT),
                        ("você", f"bold {PURPLE_BRIGHT}"),
                    ),
                    body=Text(message.content, style="chat.input"),
                    background=PURPLE_USER_BG,
                ),
                (0, 0, 1, 0),
            )

        # Respostas do assistente preservam Markdown para texto e código.
        return Padding(
            self._message_panel(
                title=Text.assemble(
                    ("◆ ", PURPLE_PRIMARY),
                    ("ag patterns", f"bold {PURPLE_PRIMARY}"),
                ),
                body=Markdown(message.content, code_theme="material"),
                background=PURPLE_ASSISTANT_BG,
            ),
            (0, 0, 1, 0),
        )

    def render(self, max_messages: int = 6) -> RenderableType:
        """Empilha todas as mensagens em ordem de chegada."""
        if not self.messages:
            return self._responses_panel(
                Padding(
                    Group(
                        Text("AG Patterns", style=f"bold {PURPLE_PRIMARY}"),
                        Text(
                            "Pergunte algo, peça uma análise ou use /help para comandos.",
                            style=TEXT_MUTED,
                        ),
                        Text("A conversa aparecerá aqui.", style=TEXT_DIM),
                    ),
                    (1, 0, 2, 0),
                )
            )

        window = visible_window(
            self.messages,
            max_items=max_messages,
            scroll_offset=self.scroll_offset,
        )
        self.scroll_offset = window.scroll_offset
        footer = (
            f"[chat.dim]{window.first_index + 1}-{window.last_index}/"
            f"{len(self.messages)} · "
            "↑/↓ PgUp/PgDn[/]"
        )

        return self._responses_panel(
            Group(*[self._render_message(message) for message in window.items]),
            footer=footer,
        )
