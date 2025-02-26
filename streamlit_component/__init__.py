import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "custom_component",
    path=os.path.dirname(__file__)
)

def render_wordle(grid, colors, current_row=0):
    """
    Render the Wordle grid using an HTML streamlit custom component.

    :param grid: 2D list for the grid
    :param colors: 2D list of colors for each cell
    :param current_row: active row
    :return: Updated cells
    """

    return _component_func(
        spec={
            "grid": grid,
            "colors": colors,
            "activeRow": current_row
        },
        default=None
    )