import pandas as pd
import streamlit as st
from streamlit_component import render_wordle
from wordle_solver_v1 import WordleSolver


### -------------------------------------------------- ###
### --- INITIALIZE SESSION STATE --- ###


if not "init" in st.session_state:
    st.session_state.init           = True
    st.session_state.wordle_solver  = WordleSolver()
    _guess, _h                      = st.session_state.wordle_solver.get_guess()
    st.session_state.hints          = pd.DataFrame(columns=["Guess", "H(x) gained", "H(x) left", "Candidates"])
    st.session_state.hints.loc[0]   = [
        _guess.upper(),
        _h,
        st.session_state.wordle_solver.max_h-_h,
        len(st.session_state.wordle_solver.candidates)
    ]
    st.session_state.guesses_grid   = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.results_grid   = [["" for _ in range(5)] for _ in range(6)]
    st.session_state.guesses        = []
    st.session_state.results        = []


### -------------------------------------------------- ###
### --- HELPER FUNCTIONS --- ###


def create_feedback(guess: str, result: list) -> str:
    """
    Return the feedback string from the cells' background color.

    :param guess: guessed word
    :param result: list of colors
    :return: feedback string
    """

    feedback = ""
    for i, color in enumerate(result):
        if color == "green":
            feedback += guess[i]
        if color == "yellow":
            feedback += "-"
        if color == "gray":
            feedback += "+"

    return feedback


### -------------------------------------------------- ###
### --- PAGE CONTENT --- ###

candidates = st.session_state.wordle_solver.candidates
n_guesses = len(st.session_state.guesses)

cols = st.columns((2, 3))
with cols[0]:
    updated_grid = render_wordle(
        grid=st.session_state.guesses_grid,
        colors=st.session_state.results_grid,
        current_row=n_guesses
    )
with cols[1]:
    if st.session_state.hints.shape[0] > 0:
        sel1 = dict(selector='th', props=[('text-align', 'center')])
        sel2 = dict(selector='td', props=[('text-align', 'center')])
        floating = st.session_state.hints.select_dtypes(include=['float64']).round(2)
        floating_cols = floating.columns.tolist()
        form = {col: "{:.2f}" for col in floating_cols}
        table = st.session_state.hints.style.format(form).set_table_styles([sel1, sel2]).hide(axis=0).to_html()
        st.write(f'{table}', unsafe_allow_html=True)

    # Show all remaining candidates if there are just a few left
    if len(candidates) < 5:
        with st.expander("Show remaining candidates"):
            st.write(" - ".join(candidates).upper())


if updated_grid:
    row, col = updated_grid["row"], updated_grid["col"]
    st.session_state.guesses_grid[row][col] = updated_grid["letter"]
    st.session_state.results_grid[row][col] = updated_grid["color"]
    st.rerun()


with cols[0]:
    if st.button("Submit guess"):
        guess_list = st.session_state.guesses_grid[n_guesses]
        color_list = st.session_state.results_grid[n_guesses]
        if "" in guess_list or "white" in color_list:
            raise Exception("Incomplete guess or feedback")

        guess = "".join(guess_list).lower()
        if guess not in st.session_state.wordle_solver.allowed_words:
            print(guess)
            raise Exception("Invalid guess")
        feedback = create_feedback(
            guess=guess,
            result=color_list
        )

        st.session_state.guesses.append(guess)
        st.session_state.results.append(feedback)
        st.session_state.wordle_solver.attempts = (guess, feedback)
        _guess, _h = st.session_state.wordle_solver.get_guess()
        st.session_state.hints.loc[n_guesses+1] = [
            _guess.upper(),
            _h,
            st.session_state.hints["H(x) left"].iloc[-1]-_h,
            len(candidates)
        ]
        st.rerun()

    # Restart the game cleaning the state
    if st.button("Restart"):
        st.session_state.wordle_solver.restart_game()
        _guess, _h                        = st.session_state.wordle_solver.first_guess
        st.session_state.hints          = pd.DataFrame(columns=["Guess", "H(x) gained", "H(x) left", "Candidates"])
        st.session_state.hints.loc[0]   = [
            _guess.upper(),
            _h,
            st.session_state.wordle_solver.max_h-_h,
            len(candidates)
        ]
        st.session_state.guesses_grid   = [["" for _ in range(5)] for _ in range(6)]
        st.session_state.results_grid   = [["" for _ in range(5)] for _ in range(6)]
        st.session_state.guesses        = []
        st.session_state.results        = []
        st.rerun()