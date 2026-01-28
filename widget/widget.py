from rich.panel import Panel
from rich.align import Align
from rich.console import Console
console = Console()

def cuadro_centro(name : str,title: str = "Welcome"):
    width, height = console.size

    panel = Panel(
        Align.center(
            f"{name}",
            vertical="middle"
        ),
        width=width - 4,
        height=5 ,
        border_style="green",
        title=title
    )
    console.print(Align.center(panel))