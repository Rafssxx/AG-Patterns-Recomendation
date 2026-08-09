"""Tema central da interface CLI.

A paleta mantém o roxo como cor de identidade do projeto, mas usa tons mais
escuros e bordas discretas para aproximar a experiência de uma TUI
terminal-native, semelhante ao visual minimalista do opencode.
"""

from rich.theme import Theme

# Paleta principal: fundo quase preto + acentos roxos suaves.
PURPLE_PRIMARY = "#A78BFA"  # Destaques principais e cursor
PURPLE_BRIGHT = "#C4B5FD"  # Destaques de papel/estado ativo
PURPLE_BORDER = "#3B3158"  # Bordas discretas dos painéis
PURPLE_BG = "#111018"  # Fundo principal da aplicação
PURPLE_USER_BG = "#181323"  # Superfície sutil para mensagens do usuário
PURPLE_ASSISTANT_BG = "#14121D"  # Superfície sutil para respostas
PURPLE_INPUT_BG = "#171321"  # Fundo da caixa de entrada

# Cores neutras usadas para hierarquia de texto.
TEXT_PRIMARY = "#F4F0FF"
TEXT_MUTED = "#A39AAE"
TEXT_DIM = "#6F667A"
SURFACE_BORDER = "#2A2438"


def build_theme() -> Theme:
    """Cria o Theme do rich com os estilos nomeados da aplicação.

    Os estilos podem ser usados em markup (ex.: [chat.title]Texto[/])
    ou diretamente via console.style em toda a interface.
    """
    return Theme(
        {
            "chat.title": f"bold {PURPLE_PRIMARY}",
            "chat.user": f"bold {PURPLE_BRIGHT}",
            "chat.assistant": TEXT_PRIMARY,
            "chat.hint": TEXT_MUTED,
            "chat.dim": TEXT_DIM,
            "chat.border": PURPLE_BORDER,
            "chat.surface.border": SURFACE_BORDER,
            "chat.input": TEXT_PRIMARY,
            "chat.cursor": f"bold {PURPLE_PRIMARY}",
        },
        inherit=True,
    )
