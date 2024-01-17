import cv2
import math
import streamlit as st


def evaluate_dice_results(dice_string):
    score = 0
    dice_values = {
        "1": [100,200,1000,2000,4000,8000,0],
        "2": [0,0,200,400,800,1200,0],
        "3": [0,0,300,900,1800,3600,0],
        "4": [0,0,400,800,1600,3200,0],
        "5": [50,100,500,1000,2000,4000,0],
        "6": [0,0,600,1200,2400,4800,0]}

    try:
        values = [int(d) for d in dice_string.split(" | ")]
        occurrences = [values.count(i) for i in range(1, 7)]

        if sorted(set(values)) == list(range(1, 7)):
            return 2000

        for i, j in zip(range(1, 7), occurrences):
            score += dice_values[str(i)][j - 1]
        return score
    except:
        return 0


st.title("Dice Rolls")
run = st.toggle('Activate Camera')
FRAME_WINDOW = st.image([])

camera = cv2.VideoCapture("http://192.168.1.168:8080/video")

dice_count_list = []

while run:
    _, frame = camera.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = 500
    max_area = 1000
    dice_contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > min_area and cv2.contourArea(cnt) < max_area)]

    for cnt in dice_contours:
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)

    connected_dots = {}

    for i in range(len(dice_contours) - 1):
        for j in range(i + 1, len(dice_contours)):
            cnt1 = dice_contours[i]
            cnt2 = dice_contours[j]
            M1 = cv2.moments(cnt1)
            M2 = cv2.moments(cnt2)
            if M1["m00"] != 0 and M2["m00"] != 0:
                cX1, cY1 = int(M1["m10"] / M1["m00"]), int(M1["m01"] / M1["m00"])
                cX2, cY2 = int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"])

                distance = math.sqrt((cX1 - cX2)**2 + (cY1 - cY2)**2)

                if distance < 100:
                    group_id_i = next((key for key, value in connected_dots.items() if i in value), None)
                    group_id_j = next((key for key, value in connected_dots.items() if j in value), None)

                    if group_id_i is None and group_id_j is None:
                        new_group_id = len(connected_dots) + 1
                        connected_dots[new_group_id] = {i, j}
                    elif group_id_i is None:
                        connected_dots[group_id_j].add(i)
                    elif group_id_j is None:
                        connected_dots[group_id_i].add(j)
                    elif group_id_i != group_id_j:
                        merged_group = connected_dots[group_id_i] | connected_dots[group_id_j]
                        del connected_dots[group_id_i]
                        del connected_dots[group_id_j]
                        connected_dots[new_group_id] = merged_group

    for i in range(len(dice_contours)):
        if i not in {dot for group in connected_dots.values() for dot in group}:
            new_group_id = len(connected_dots) + 1
            connected_dots[new_group_id] = {i}

    for group_id, group in connected_dots.items():
        for dot_index in group:
            cnt = dice_contours[dot_index]
            M = cv2.moments(cnt)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)

        if len(group) > 1:
            group_centers = [(int(cv2.moments(dice_contours[dot_index])["m10"] / cv2.moments(dice_contours[dot_index])["m00"]),
                              int(cv2.moments(dice_contours[dot_index])["m01"] / cv2.moments(dice_contours[dot_index])["m00"]))
                             for dot_index in group]

            for i in range(len(group_centers) - 1):
                for j in range(i + 1, len(group_centers)):
                    cv2.line(frame, group_centers[i], group_centers[j], (0, 0, 255), 2)

    group_texts = " | ".join([f"{len(group)}" for group_id, group in connected_dots.items()])
    result_score = evaluate_dice_results(group_texts)
    result_text = f"[{len(connected_dots)}] : ({group_texts}) = {result_score}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_thickness = 2
    font_color = (255, 255, 255)
    background_color = (0, 0, 0)
    margin = 10

    (text_width, text_height), _ = cv2.getTextSize(result_text, font, font_scale, font_thickness)
    text_x = 10
    text_y = 10 + text_height

    cv2.rectangle(frame, (text_x - margin, text_y - text_height - margin), (text_x + text_width + margin, text_y + margin), background_color, -1)
    cv2.putText(frame, result_text, (text_x, text_y), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

    FRAME_WINDOW.image(frame)

else:
    camera.release()
    cv2.destroyAllWindows()

if 'running_totals' not in st.session_state:
    st.session_state.running_totals = {}

if 'additions_history' not in st.session_state:
    st.session_state.additions_history = {}

with st.expander("Settings", expanded=False):
    players = st.slider("Player count", 1, 5, 2)
    if st.button("Clear All Scores and History"):
        st.session_state.running_totals = {}
        st.session_state.additions_history = {}
        for index in range(players):
            st.session_state[f"player{index}"] = 0
            
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
        val = st.number_input(nm, min_value=0, step=50, label_visibility="hidden", key=f"player{index}")

        if st.button("Add", key=f"addbtn{index}"):
            original_value = st.session_state.running_totals[f"player{index}"]
            updated_value = original_value + val
            st.session_state.running_totals[f"player{index}"] = updated_value

            st.session_state.additions_history[f"additions_history{index}"].append(val)

        st.subheader(f"Score: {st.session_state.running_totals[f'player{index}']}")

        st.json(f"{st.session_state.additions_history[f'additions_history{index}']}")