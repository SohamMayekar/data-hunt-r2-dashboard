"""Shared visual tokens and Plotly template for the dashboard."""
import plotly.graph_objects as go
import plotly.io as pio

COLORS = {
    "paper": "#F6F3EC", "ink": "#1B1B1B", "muted": "#6B6B6B",
    "hairline": "#D9D3C7", "context": "#B8B2A5", "accent": "#C8452B",
    "teal": "#2F5D62", "white": "#FBFAF7", "grid": "#E7E2D8",
}
FONTS = {"serif": "Georgia, 'Source Serif 4', serif", "sans": "'IBM Plex Sans', Inter, Arial, sans-serif"}
SPACE = {"unit": 8, "section": 48, "chart": 24, "max_width": 1280}

EDITORIAL = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=COLORS["paper"], plot_bgcolor=COLORS["paper"],
        font={"family": "Arial, sans-serif", "size": 12, "color": COLORS["ink"]},
        title={"font": {"family": "Georgia, serif", "size": 19, "color": COLORS["ink"]}},
        margin={"l": 54, "r": 28, "t": 55, "b": 46},
        xaxis={"showgrid": False, "zeroline": False, "linecolor": COLORS["hairline"], "ticks": "outside"},
        yaxis={"showgrid": True, "gridcolor": COLORS["grid"], "zeroline": False, "linecolor": COLORS["hairline"]},
        hoverlabel={"bgcolor": COLORS["white"], "bordercolor": COLORS["hairline"], "font": {"family": "Arial, sans-serif", "size": 12}},
        colorway=[COLORS["teal"], COLORS["accent"], COLORS["context"], COLORS["muted"]],
    )
)
pio.templates["editorial"] = EDITORIAL
pio.templates.default = "editorial"
