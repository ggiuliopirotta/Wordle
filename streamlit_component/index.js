document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("wordle-grid");
  const COLORS = {
    gray: "#787c7e",
    yellow: "#c9b458",
    green: "#6aaa64",
    white: "#ffffff"  // default color
  };

  function createGrid(data) {
    container.innerHTML = "";
    const grid = data.grid || Array(6).fill().map(() => Array(5).fill(""));
    const colors = data.colors || Array(6).fill().map(() => Array(5).fill("gray"));
    const activeRow = data.activeRow;

    for (let i = 0; i < 6; i++) {
      const row = document.createElement("div");
      row.className = "wordle-row";

      for (let j = 0; j < 5; j++) {
        const cell = document.createElement("div");
        cell.className = "wordle-cell";

        // Set cell background color based on the color state
        const cellColor = colors[i][j] || "white";
        cell.style.backgroundColor = COLORS[cellColor];

        const input = document.createElement("input");
        input.type = "text";
        input.className = "wordle-input";
        input.value = grid[i][j] || "";  // Ensure empty string if no value
        input.maxLength = 1;
        input.pattern = "[A-Za-z]";
        input.setAttribute("data-row", i);
        input.setAttribute("data-col", j);

        // Set input background to match cell
        input.style.backgroundColor = COLORS[cellColor];

        // Set text color based on background
        input.style.color = cellColor === "white" ? "black" : "white";

        // Disable input if not in active row
        if (i !== activeRow) {
          input.disabled = true;
          input.style.cursor = "default";
        }

        // Color indicator dot
        const colorDot = document.createElement("div");
        colorDot.className = "color-indicator";

        // Handle letter input
        input.addEventListener("input", (e) => {
          if (i === activeRow) {
            const value = e.target.value.replace(/[^A-Za-z]/g, "").toUpperCase();
            e.target.value = value;
            const row = parseInt(e.target.getAttribute("data-row"));
            const col = parseInt(e.target.getAttribute("data-col"));

            updateValue(row, col, value, colors[row][col] || "white");
          }
        });

        // Handle color cycling (only for active row)
        colorDot.addEventListener("click", (e) => {
          if (i === activeRow) {
            const row = parseInt(input.getAttribute("data-row"));
            const col = parseInt(input.getAttribute("data-col"));
            const currentColor = colors[row][col] || "gray";
            const nextColor = getNextColor(currentColor);

            // Update colors
            colors[row][col] = nextColor;
            cell.style.backgroundColor = COLORS[nextColor];
            input.style.backgroundColor = COLORS[nextColor];
            input.style.color = nextColor === "white" ? "black" : "white";

            updateValue(row, col, input.value, nextColor);
          }
        });

        cell.appendChild(input);
        cell.appendChild(colorDot);
        row.appendChild(cell);
      }
      container.appendChild(row);
    }
  }

  function getNextColor(currentColor) {
    const colorOrder = ["gray", "yellow", "green", "white"];
    const currentIndex = colorOrder.indexOf(currentColor);
    return colorOrder[(currentIndex + 1) % colorOrder.length];
  }

  function updateValue(row, col, letter, color) {
    Streamlit.setComponentValue({
      row,
      col,
      letter: letter,
      color: color
    });
  }

  Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, (event) => {
    createGrid(event.detail.args.spec);
    Streamlit.setFrameHeight(300);
  });

  Streamlit.setComponentReady();
});