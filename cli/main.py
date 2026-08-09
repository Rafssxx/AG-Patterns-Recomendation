"""Ponto de entrada da interface de chat em CLI.

Executa o loop principal da aplicação: captura teclas em modo raw,
atualiza a caixa de entrada em tempo real e exibe a área de respostas
logo abaixo do campo de digitação. Comandos iniciados com '/' abrem
menus/modais (ex.: /help) ou executam ações (ex.: /clear, /exit).

Para executar:  python -m cli.main
"""

import codecs
import os
import select
import sys
import termios
import tty

from rich import box
from rich.align import Align
from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .components.chat_input import ChatInput
from .components.chat_output import ChatOutput
from .components.modal import Modal
from .components.theme import (
    PURPLE_BG,
    PURPLE_BORDER,
    PURPLE_PRIMARY,
    TEXT_MUTED,
    build_theme,
)
from .response import Response
from .utils import (
    CLEAR_COMMANDS,
    EXIT_COMMANDS,
    HELP_COMMANDS,
    command_name,
    has_ansi_prefix,
    is_backspace_key,
    is_command,
    is_enter_key,
    is_escape_key,
    is_exit_key,
    normalize_message,
    parse_escape_sequence,
    visible_message_limit,
)

# Logo exibido no topo da interface.
APP_LOGO = """\
 █████╗  ██████╗       ██████╗  █████╗ ████████╗███████╗██████╗ ███╗   ██╗███████╗
██╔══██╗██╔════╝       ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗████╗  ██║██╔════╝
███████║██║  ███╗█████╗██████╔╝███████║   ██║   █████╗  ██████╔╝██╔██╗ ██║███████╗
██╔══██║██║   ██║╚════╝██╔═══╝ ██╔══██║   ██║   ██╔══╝  ██╔══██╗██║╚██╗██║╚════██║
██║  ██║╚██████╔╝      ██║     ██║  ██║   ██║   ███████╗██║  ██║██║ ╚████║███████║
╚═╝  ╚═╝ ╚═════╝       ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝
"""

# Corpo do modal de ajuda, exibido com o comando /help.
HELP_BODY = (
    "[chat.title]Comandos[/]\n\n"
    "  [chat.user]/help[/]  ou  [chat.user]/menu[/]     Abre este menu\n"
    "  [chat.user]/clear[/] ou  [chat.user]/limpar[/]   Limpa o histórico\n"
    "  [chat.user]/exit[/]  ou  [chat.user]/sair[/]     Encerra o chat\n\n"
    "[chat.title]Navegação[/]\n\n"
    "  [chat.user]↑ / ↓[/]                Rola uma mensagem por vez\n"
    "  [chat.user]PgUp / PgDn[/]          Rola em blocos\n\n"
    "[chat.dim]Pressione ESC para voltar ao chat.[/]"
)


class ChatApp:
    """Aplicação de chat em CLI, montada com os componentes da UI."""

    def __init__(self, console: Console) -> None:
        self.console = console
        # Caixa de texto com fundo (background) onde o usuário digita.
        self.input = ChatInput()
        # Área de resposta exibida logo abaixo do campo de entrada.
        self.output = ChatOutput()
        # Gerador de respostas (mock; pode ser trocado por um LLM).
        self.responder = Response()
        # Modal/menu de ajuda acionado por comandos como /help.
        self.modal = Modal("Ajuda — Comandos", HELP_BODY)
        # Flag que indica se um modal está aberto na tela.
        self.show_modal = False
        # Flag de controle do loop principal.
        self.running = True
        # Decodificador incremental para suportar texto UTF-8 na entrada.
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

        # Mensagem de boas-vindas exibida na área de resposta.
        self.output.add_assistant(
            "Bem-vindo(a)! Digite sua mensagem abaixo e pressione **Enter**.\n"
            "Use **/help** para ver os comandos disponíveis."
        )

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------
    def _render_header(self) -> RenderableType:
        """Renderiza a assinatura visual da aplicação no topo do chat."""
        subtitle = Text(
            "agent cli · /help comandos · ↑/↓ histórico",
            style=TEXT_MUTED,
            justify="center",
        )
        return Align.center(
            Panel(
                Align.center(Text(APP_LOGO, style=f"bold {PURPLE_PRIMARY}")),
                subtitle=subtitle,
                subtitle_align="center",
                border_style=PURPLE_BORDER,
                style=Style(bgcolor=PURPLE_BG),
                box=box.ROUNDED,
                padding=(0, 1),
            )
        )

    def _visible_message_limit(self) -> int:
        """Calcula quantos blocos de mensagem cabem na área de respostas."""
        return visible_message_limit(self.console.height)

    def build_display(self) -> RenderableType:
        """Monta a tela completa do chat ocupando toda a altura do terminal."""
        if self.show_modal:
            # Modal aberto substitui a tela do chat por completo.
            return self.modal.render()

        # Histórico expande no espaço disponível e o input fica fixo no rodapé.
        content = Layout(name="content")
        content.split_column(
            Layout(self._render_header(), name="header", size=9),
            Layout(
                self.output.render(max_messages=self._visible_message_limit()),
                name="messages",
                ratio=1,
            ),
            Layout(self.input.render(), name="input", size=3),
        )

        # Painel principal: card central que ocupa toda a tela.
        base = Panel(
            content,
            border_style=PURPLE_BORDER,
            style=Style(bgcolor=PURPLE_BG),
            box=box.ROUNDED,
            padding=(1, 1),
        )

        # O Layout raiz força o Rich a distribuir o card pela tela inteira.
        screen = Layout(name="screen")
        screen.update(base)

        return screen

    # ------------------------------------------------------------------
    # Processamento de entrada e comandos
    # ------------------------------------------------------------------
    def process_text(self, text: str) -> None:
        """Processa cada caractere recebido do teclado em tempo real."""
        i = 0
        while i < len(text) and self.running:
            ch = text[i]

            if is_escape_key(ch):
                if has_ansi_prefix(text, i):
                    i = self._handle_escape_sequence(text, i)
                    continue
                self.show_modal = False
                i += 1
                continue

            # Com modal aberto, qualquer outra tecla é ignorada.
            if self.show_modal:
                i += 1
                continue

            self._process_input_key(ch)
            i += 1

    def _process_input_key(self, char: str) -> None:
        """Processa uma tecla comum quando o chat está ativo."""
        if is_exit_key(char):
            self.running = False
        elif is_enter_key(char):
            self.submit()
        elif is_backspace_key(char):
            self.input.backspace()
        else:
            self.input.append(char)

    def _handle_escape_sequence(self, text: str, start_index: int) -> int:
        """Processa teclas especiais iniciadas por ESC."""
        sequence = parse_escape_sequence(text, start_index)

        if self.show_modal:
            return sequence.next_index

        page_size = self._visible_message_limit()
        if sequence.key == "up":
            self.output.scroll_up()
        elif sequence.key == "down":
            self.output.scroll_down()
        elif sequence.key == "page_up":
            self.output.scroll_up(page_size)
        elif sequence.key == "page_down":
            self.output.scroll_down(page_size)

        return sequence.next_index

    def submit(self) -> None:
        """Envia o conteúdo do campo de entrada como uma mensagem."""
        user_text = normalize_message(self.input.value())
        self.input.clear()

        if not user_text:
            return  # campo vazio: nada a fazer

        if is_command(user_text):
            self._handle_command(user_text)
            return

        # Mensagem normal: adiciona ao histórico e gera a resposta.
        self.output.add_user(user_text)
        self.output.add_assistant(self.responder.reply(user_text))

    def _handle_command(self, user_text: str) -> None:
        """Executa comandos do usuário como /help, /clear e /exit."""
        cmd = command_name(user_text)
        if cmd in EXIT_COMMANDS:
            # Encerra o loop principal do chat.
            self.running = False
        elif cmd in CLEAR_COMMANDS:
            # Limpa o histórico da área de resposta.
            self.output.clear()
        elif cmd in HELP_COMMANDS:
            # Abre o modal/menu de ajuda na interface.
            self.show_modal = True
        else:
            # Comando desconhecido: informa o usuário.
            self.output.add_user(user_text)
            self.output.add_assistant(f"Comando não reconhecido: `{cmd}`. Use `/help`.")

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Executa o loop principal com entrada em tempo real."""
        # Sem TTY (ex.: pipes), usa um modo simples de leitura linha a linha.
        if not sys.stdin.isatty():
            self._run_fallback()
            return

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            # Modo cbreak: cada tecla é entregue imediatamente, sem Enter.
            tty.setcbreak(fd)

            # Live renderiza a interface a cada atualização, em tela cheia.
            with Live(
                self.build_display(),
                console=self.console,
                screen=True,
                refresh_per_second=30,
            ) as live:
                while self.running:
                    # Se houver bytes disponíveis, processa as teclas.
                    if select.select([sys.stdin], [], [], 0.05)[0]:
                        raw = os.read(fd, 4096)
                        self.process_text(self.decoder.decode(raw))
                        live.update(self.build_display())
                    # Mantém a tela atualizada (ex.: redimensionamentos).
                    live.refresh()
        finally:
            # Restaura o terminal ao estado original.
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            self.decoder.reset()

        # Mensagem final exibida após restaurar o terminal.
        self.console.print(
            Panel(
                Text("Chat encerrado. Até logo!", style=f"bold {PURPLE_PRIMARY}"),
                border_style=PURPLE_BORDER,
                box=box.ROUNDED,
            )
        )

    def _run_fallback(self) -> None:
        """Modo sem TTY: lê uma linha por vez via input() e imprime a tela."""
        self.console.print(self.build_display())
        while self.running:
            try:
                user_text = normalize_message(input("❯ "))
            except (EOFError, KeyboardInterrupt):
                break  # fim do fluxo de entrada
            if not user_text:
                continue

            # Com modal aberto, a primeira tecla/linha fecha o modal.
            if self.show_modal:
                self.show_modal = False
                self.console.print(self.build_display())
                continue

            if is_command(user_text):
                self._handle_command(user_text)
            else:
                self.output.add_user(user_text)
                self.output.add_assistant(self.responder.reply(user_text))

            self.console.print(self.build_display())


def main() -> None:
    """Cria a aplicação e inicia a interface de chat."""
    app = ChatApp(Console(theme=build_theme(), highlight=False))
    app.run()


if __name__ == "__main__":
    main()
