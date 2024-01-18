Simple algo to detect dots and by proximity also the individual dice values for a game evaluation scoring

Setup as python program (app.py), request via streamlit interface (stapp.py) or flask application with scoring options (flaskapp.py)

My use is via other phone camera with IP Webcam installed and hooked to my local network via wifi, i then run the application on my server (or PC) and connect to it via browser from my tablet

It is setup for fixed spot not far from actual dice, so tweaking might be important, listing most insteresting parts:
- cap = cv2.VideoCapture("http://192.168.1.168:8080/video")
-- can be changed to different IP or replaced for directly connected camera

- min_area = 500
-- minimal size for dot detection

- distance < 100:
-- maximal proximity distance of individual dots for grouping

Notes:
* for running python app press "q" to exit