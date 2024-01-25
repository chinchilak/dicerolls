import streamlit as st

def update_input(value):
    current_value = st.session_state.input_value
    if current_value == "0":
        st.session_state.input_value = value
    else:
        st.session_state.input_value += value
    update_result()

def delete_last():
    current_value = st.session_state.input_value
    if len(current_value) > 1:
        st.session_state.input_value = current_value[:-1]
    else:
        st.session_state.input_value = "0"
    update_result()

def clear_all():
    st.session_state.input_value = "0"
    update_result()

def update_result():
    try:
        st.session_state.result = str(eval(st.session_state.input_value))
    except:
        st.session_state.result = "Error"

def add_amount(index, value):
    original_value = st.session_state.running_totals[f"player{index}"]
    updated_value = original_value + int(value)
    st.session_state.running_totals[f"player{index}"] = updated_value
    st.session_state.additions_history[f"additions_history{index}"].append(int(value))
    st.session_state.input_value = "0"


st.set_page_config(layout="wide")

if 'running_totals' not in st.session_state:
    st.session_state.running_totals = {}

if 'additions_history' not in st.session_state:
    st.session_state.additions_history = {}

if 'input_value' not in st.session_state:
    st.session_state.input_value = str(0)


with st.sidebar:
    st.header("Dice Rolls")
    players = st.slider("Player count", 1, 5, 2)
    if st.button("Reset Data"):
        st.session_state.running_totals = {}
        st.session_state.additions_history = {}
        st.session_state.input_value = "0"
        for index in range(players):
            st.session_state[f"player{index}"] = 0

ival1, ival2 = st.columns([3,4])
value = ival1.text_input("Value", key="input_value")

col1, col2, col3, col4 = st.columns([1,1,1,4])

for i in [1,2,3,4,5,6,7,8,9,0,"DEL","CLEAR"]:
    if i in [1,4,7,0]:
        col1.button(str(i), key=f"button_{i}", on_click=update_input, args=(str(i),), use_container_width=True)
    elif i in [2,5,8]:
        col2.button(str(i), key=f"button_{i}", on_click=update_input, args=(str(i),), use_container_width=True)
    elif i == "DEL":
        col2.button(i, key="button_DEL", on_click=delete_last, use_container_width=True)
    elif i == "CLEAR":
        col3.button(i, key="button_CLEAR", on_click=clear_all, use_container_width=True)
    elif i in [3,6,9]:
        col3.button(str(i), key=f"button_{i}", on_click=update_input, args=(str(i),), use_container_width=True)

player_ids = [i for i in range(players)]
running_total = [0] * players

columns = st.columns(players)

for index, player, column in zip(player_ids, range(1, players + 1), columns):
    if f"player{index}" not in st.session_state.running_totals:
        st.session_state.running_totals[f"player{index}"] = 0

    if f"additions_history{index}" not in st.session_state.additions_history:
        st.session_state.additions_history[f"additions_history{index}"] = []
    
    with column:
        nm = st.text_input("Name", f"Pusik {index + 1}", key=f"name{index}")

        c1, c2, c3, c4 = st.columns([2,1,2,2])
        c1.button("Add", key=f"addbtn{index}", on_click=add_amount, args=(str(index),st.session_state.input_value), use_container_width=True)
        c3.button("+350", key=f"add350{index}", on_click=add_amount, args=(str(index),350), use_container_width=True)
        c4.button("+1000", key=f"add1000{index}", on_click=add_amount, args=(str(index),1000), use_container_width=True)

        c1.subheader(f"Score: {st.session_state.running_totals[f'player{index}']} / {10_000 - int(st.session_state.running_totals[f'player{index}'])}")
        try:
            c3.subheader(f"Zero: {st.session_state.additions_history.get(f'additions_history{index}', []).count(0)}  ({(st.session_state.additions_history.get(f'additions_history{index}', []).count(0))/len(st.session_state.additions_history.get(f'additions_history{index}')):.2%})")
        except:
            pass
        st.line_chart({index: value for index, value in enumerate(st.session_state.additions_history[f'additions_history{index}'])}, use_container_width=True)
        st.code(f"{st.session_state.additions_history[f'additions_history{index}']}")