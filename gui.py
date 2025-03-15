from math import log2
import pandas as pd
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_component import render_wordle
from wordle_solver_v1 import WordleSolver


### -------------------------------------------------- ###
### --- INITIALIZE SESSION STATE --- ###


if not "init" in st.session_state:
    st.session_state.init           = True
    st.session_state.wordle_solver  = WordleSolver()
    _guess, _h                      = st.session_state.wordle_solver.get_guess()
    st.session_state.hints          = pd.DataFrame(columns=["Guess", "E[H(x)] gain", "E[H(x)] left", "Candidates"])
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
    st.session_state.delta          = {}


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


def print_alert(message: str, level: str="error") -> None:
    """
    Show a message on the page in a streamlit alert container

    :param message: message to print
    :param level: alert level
    """
    with stylable_container(
        key="alert",
        css_styles="""
            .stAlert{
                text-align: center
            }
        """
    ):
        if level == "error":
            st.error(message)


### -------------------------------------------------- ###
### --- MARKDOWN --- ###


st.markdown(
    """
    <h1 style='text-align: center;'>Wordle Solver</h1>
    
    This is an entropy-based solver for the [Wordle](https://www.nytimes.com/games/wordle).
    
    On the left, there is an interactive grid to input the guesses and the feedbacks received from the game. \
    Once a guess is submitted, the solver will provide the next one.
    
    Note: Attempts needed = 3.6 (avg)
    """,
    unsafe_allow_html=True
)

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

    # Show all remaining candidates if there are just a few possible left
    if len(candidates) in range(2, 6):
        with st.expander("Remaining candidates"):
            st.write(" - ".join(candidates).upper())

    # Show hints table
    if st.session_state.hints.shape[0] > 0:
        sel1 = dict(selector='th', props=[('text-align', 'center')])
        sel2 = dict(selector='td', props=[('text-align', 'center')])
        floating = st.session_state.hints.select_dtypes(include=['float64']).round(2)
        floating_cols = floating.columns.tolist()
        form = {col: "{:.2f}" for col in floating_cols}
        table = st.session_state.hints.style.format(form).set_table_styles([sel1, sel2]).hide(axis=0).to_html()
        st.write(f'{table}', unsafe_allow_html=True)

    if st.button(
            label="Use guess",
            help="Input the suggested guess in the current table row"
    ):
        st.session_state.guesses_grid[n_guesses] = list(st.session_state.hints.loc[n_guesses]["Guess"])
        st.session_state.results_grid[n_guesses] = ["gray"] * 5
        st.rerun()

    # Show how the actual guesses differ from the expectation
    delta = st.session_state.delta
    if delta:
        st.metric(
            label=f"Actual H(x) left after guess",
            value=round(delta["value"], 2),
            delta=round(delta["delta"], 2) if abs(delta["delta"]) > 1e-5 else None,
            delta_color="inverse",
            help="""
                This is the actual entropy left after the last guess and \\
                the little number below indicates the difference from the expected value. \\
                It can be either
                - green: more entropy gained then expected, you were lucky!
                - red: better luck next time...
                
                """
        )

# Show the custom component
if updated_grid:
    row, col = updated_grid["row"], updated_grid["col"]
    st.session_state.guesses_grid[row][col] = updated_grid["letter"]
    st.session_state.results_grid[row][col] = updated_grid["color"]
    st.rerun()

with cols[0]:
    # Submit the guess and get the next one from the solver based on the previous
    if st.button(
            label="Submit guess",
            help="Send the guess to the solver to compute the next one"
    ):
        guess_list = st.session_state.guesses_grid[n_guesses]
        color_list = st.session_state.results_grid[n_guesses]
        try:
            assert "" not in guess_list, "Incomplete guess"
            assert "white" not in color_list, "Incomplete feedback"
            guess = "".join(guess_list).lower()
            assert guess in st.session_state.wordle_solver.allowed_words, "Invalid guess"
            feedback = create_feedback(
                guess=guess,
                result=color_list
            )
            st.session_state.guesses.append(guess)
            st.session_state.results.append(feedback)
            st.session_state.wordle_solver.attempts = (guess, feedback)

            _guess, _h = st.session_state.wordle_solver.get_guess()
            n_left = len(st.session_state.wordle_solver.candidates)
            st.session_state.hints.loc[n_guesses+1] = [
                _guess.upper(),
                _h,
                log2(n_left)-_h,
                n_left
            ]
            st.session_state.delta = {
                "guess": guess,
                "value": log2(n_left),
                "delta": log2(n_left)-st.session_state.hints.loc[n_guesses]["E[H(x)] left"]
            }
            st.rerun()

        except ValueError as e:
            print_alert(message=str(e)+": please restart")
        except Exception as e:
            print_alert(message=str(e))

# Restart the game cleaning the state
if st.button("Restart"):
    st.session_state.wordle_solver.restart_game()
    _guess, _h                      = st.session_state.wordle_solver.first_guess
    st.session_state.hints          = pd.DataFrame(columns=["Guess", "E[H(x)] gain", "E[H(x)] left", "Candidates"])
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
    st.session_state.delta          = {}
    st.rerun()

