import cv2
import math

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

cap = cv2.VideoCapture("http://192.168.1.168:8080/video")
dice_count_list = []

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = 500
    max_area = 1000
    dice_contours = [cnt for cnt in contours if (cv2.contourArea(cnt) > min_area and cv2.contourArea(cnt) < max_area)]

    # Draw circles around detected dots
    for cnt in dice_contours:
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(frame, (cX, cY), 5, (0, 255, 0), -1)

    # Initialize a dictionary to store connected dots
    connected_dots = {}

    # Connect dots by visible lines based on proximity
    for i in range(len(dice_contours) - 1):
        for j in range(i + 1, len(dice_contours)):
            cnt1 = dice_contours[i]
            cnt2 = dice_contours[j]
            M1 = cv2.moments(cnt1)
            M2 = cv2.moments(cnt2)
            if M1["m00"] != 0 and M2["m00"] != 0:
                cX1, cY1 = int(M1["m10"] / M1["m00"]), int(M1["m01"] / M1["m00"])
                cX2, cY2 = int(M2["m10"] / M2["m00"]), int(M2["m01"] / M2["m00"])

                # Calculate distance between dots
                distance = math.sqrt((cX1 - cX2)**2 + (cY1 - cY2)**2)

                # Connect dots only if they are within 100 pixels
                if distance < 100:
                    # Find or create a unique group identifier for the current dot
                    group_id_i = next((key for key, value in connected_dots.items() if i in value), None)
                    group_id_j = next((key for key, value in connected_dots.items() if j in value), None)

                    if group_id_i is None and group_id_j is None:
                        # If both dots are not in any group, create a new group
                        new_group_id = len(connected_dots) + 1
                        connected_dots[new_group_id] = {i, j}
                    elif group_id_i is None:
                        # If dot i is not in any group, add it to the group of dot j
                        connected_dots[group_id_j].add(i)
                    elif group_id_j is None:
                        # If dot j is not in any group, add it to the group of dot i
                        connected_dots[group_id_i].add(j)
                    elif group_id_i != group_id_j:
                        # If dots i and j are in different groups, merge the groups
                        merged_group = connected_dots[group_id_i] | connected_dots[group_id_j]
                        del connected_dots[group_id_i]
                        del connected_dots[group_id_j]
                        connected_dots[new_group_id] = merged_group

    # Check for single dots and create individual groups
    for i in range(len(dice_contours)):
        if i not in {dot for group in connected_dots.values() for dot in group}:
            new_group_id = len(connected_dots) + 1
            connected_dots[new_group_id] = {i}

    # Draw connecting red lines between dots
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

    # Display results directly on the frame
    group_texts = " | ".join([f"{len(group)}" for group_id, group in connected_dots.items()])
    result_score = evaluate_dice_results(group_texts)
    result_text = f"[{len(connected_dots)}] : ({group_texts}) = {result_score}"

    # Define font properties
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

    cv2.imshow("Dice", frame)

    key = cv2.waitKey(1)
    if key == ord("s"):
        print(result_text)
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
