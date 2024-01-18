from flask import Flask, render_template, Response, request
import cv2
import math


app = Flask(__name__)
cap = cv2.VideoCapture("http://192.168.1.168:8080/video")

player1_score = 0
player2_score = 0
player1_score_history = []
player2_score_history = []

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

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
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

            # cv2.imshow("Dice", frame)

            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update_score', methods=['POST'])
def update_score():
    global player1_score, player2_score, player1_score_history, player2_score_history

    if request.method == 'POST':
        player = request.form['player']
        score = int(request.form['score'])
        if player == 'player1':
            player1_score_history.append(score)
            player1_score += score
        elif player == 'player2':
            player2_score_history.append(score)
            player2_score += score

    return render_template('index.html', player1_score=player1_score, player2_score=player2_score, player1_score_history=player1_score_history, player2_score_history=player2_score_history)

@app.route('/clear_all', methods=['POST'])
def clear_all():
    global player1_score, player2_score, player1_score_history, player2_score_history

    if request.method == 'POST':
        player1_score = 0
        player2_score = 0
        player1_score_history = []
        player2_score_history = []

    return render_template('index.html', player1_score=player1_score, player2_score=player2_score, player1_score_history=player1_score_history, player2_score_history=player2_score_history)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
