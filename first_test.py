import cv2
import mediapipe as mp
import time
import math
import logging


# 1. MediaPipe Initialisierung
mp_hands = mp.solutions.hands
'''
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.1
)
'''

# Initialisiere die Hand-Erkennung
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands= 2,
    min_detection_confidence=0.7  # Höhere Konfidenz für bessere Genauigkeit
)

mp_drawing = mp.solutions.drawing_utils

# 2. Kamera Initialisierung (WICHTIG: Verwenden Sie den Index 1, der bei Ihnen funktioniert hat)
cam = cv2.VideoCapture(1)

if not cam.isOpened():
    print("Fehler: Kamera konnte nicht geöffnet werden. Prüfen Sie den Kamera-Index und die Systemberechtigungen.")
    exit()

print("Kamera läuft. Bringen Sie Ihre Hand ins Bild und drücken Sie 'q' zum Beenden.")

# Variablen für die FPS-Anzeige (optional)
pTime = 0

#--------------______DATENBANK_________----------------------


# -- SYMBOLE Zahlen HAND ERKENNUNG --

#--Erkennung von G KONSTANTEN
WINKEL_SCHWELLE_HORIZONTAL = 30
WINKEL_SCHWELLE_VERTICAL_MIN = 60
WINKEL_SCHWELLE_VERITCAL_MAX = 120

faust_code = "00000"   #faust
eins_code = "01000"    #zeigefinger
zwei_code = "01100"    #zeige/mittelfinger
drei_code = "01110"    #zeige/mittel/ringfinger
vier_code = "01111"    #alle außer daumen
fuenf_code = "11111"   #alle 5 finger
#stop_code = "00000"

# -- Symbole Buchstaben Hand Erkennung --
a = "10000"
b = "01111"
#TODO: c = ...
#TODO: d = ...
#TODO: e = ...
#TODO: f = ...
#g = "01000"
#TODO: h = ...
#TODO: i = ...
#TODO: j = ...
#TODO: k = ...
#TODO: l = ...
#TODO: m = ...
#TODO: n = ...
#TODO: o = ...
#TODO: p = ...
#TODO: q = ...
#TODO: r = ...
#TODO: s = ...
#TODO: t = ...
#TODO: u = ...
v = "01100"
#TODO: w = ...
#TODO: x = ...
#TODO: y = ...
#TODO: z = ...

# -- Gebärdensprach-Dictionary --
gebaerdensprache_dictionary_zahlen = \
    {
    #eins_code: "eins",
    zwei_code: "zwei",
    drei_code: "drei",
    vier_code: "vier",
    fuenf_code: "fuenf",
    }

gebaerden_sprache_dictionary_buchstaben = \
    {
    a: "a",
    b: "b",
    #g: "g",
    v: "v"
    }

while True:
    ret, frame = cam.read()
    if not ret:
        break

    # Optional: Bild spiegeln, damit es natürlicher wirkt
    frame = cv2.flip(frame, 1)


    # 3. Bild für MediaPipe vorbereiten (BGR -> RGB)
    # MediaPipe erwartet RGB-Bilder
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 4. Hand-Erkennung durchführen
    results_hands = hands.process(image_rgb)

    #results_face = face_detection.process(image_rgb)
    '''
    if results_face.detections:



        cv2.putText(frame, "Gesicht erkannt", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2, cv2.LINE_AA)


        cv2.putText(frame, "Gesicht erkannt", (frame.shape[1] - 300, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2
                    , cv2.LINE_AA)

        for detection in results_face.detections:
            mp_drawing.draw_detection(frame, detection)
            '''
    # 5. Hand-Erkennung prüfen und Aktion ausführen
    if results_hands.multi_hand_landmarks:

        cv2.putText(frame, 'HÄNDE ERKANNT', (frame.shape[1] - 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Landmarkierungen zeichnen
        for hand_landmarks in results_hands.multi_hand_landmarks:
            wrist_landmark = hand_landmarks.landmark[0]

            normalized_landmarks = []

            for i, landmark in enumerate(hand_landmarks.landmark):
                relative_x = landmark.x - wrist_landmark.x
                relative_y = landmark.y - wrist_landmark.y

                normalized_landmarks.append([relative_x, relative_y])

                if i == 8:
                    cv2.putText(frame, f'Finger 8 Relativ: ({relative_x:.2f}, {relative_y:.2f})', (50, 140),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

            # --- DATEN ZUWEISEN ---
            x_daumen_spitze_index = normalized_landmarks[4][0]
            y_daumen_spitze_index = normalized_landmarks[4][1]

            y_zeigefinger_spitze_index = normalized_landmarks[8][1]
            y_mittelfinger_spitze_index = normalized_landmarks[12][1]
            y_ringfinger_spitze_index = normalized_landmarks[16][1]
            y_pinky_spitze_index = normalized_landmarks[20][1]

            x_daumen_basis_index = normalized_landmarks[2][0]
            y_daumen_basis_index = normalized_landmarks[2][1]

            y_zeigefinger_basis_index = normalized_landmarks[5][1]
            y_mittelfinger_basis_index = normalized_landmarks[9][1]
            y_ringfinger_basis_index = normalized_landmarks[13][1]
            y_pinky_basis_index = normalized_landmarks[17][1]

            #Landmarks für G, Winkel der Handfläche (Handgelenk - Mittelfingerspitze)
            #x1 = hand_landmarks[0].x
            #y1 = hand_landmarks[0].y
            #x2 = hand_landmarks[9].x
            #y2 = hand_landmarks[9].y

            #--- STATUS INITIALISIERUNG ---
            daumen_status = "0"
            zeigefinger_status = "0"
            mittelfinger_status = "0"
            ringfinger_status = "0"
            pinky_status = "0"

            # --- GESTEN-LOGIK: FINGER (4 & 1, 8 & 5, 12 & 9, 16 & 13, 20 & 17) ---
            if (x_daumen_spitze_index > x_daumen_basis_index + 0.04) and (y_daumen_spitze_index < y_zeigefinger_basis_index - 0.05):
                gesture_daumen_status = "DAUMEN STRECKT"
                color_thumb = (0, 255, 255)
                daumen_status = "1"
            else:
                gesture_daumen_status = "Daumen gebeugt oder seitlich"
                color_thumb = (255, 0, 0)
                daumen_status = "0"
            cv2.putText(frame, gesture_daumen_status, (50,100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_thumb, 2, cv2.LINE_AA)

            if y_zeigefinger_spitze_index < y_zeigefinger_basis_index - 0.25:
                gesture_zeigefinger_status = "ZEIGEFINGER STRECKT 👆"
                color_index = (0, 255, 255)  # Gelb/Cyan (Für GESTRECKT)
                zeigefinger_status = "1"
            else:
                gesture_zeigefinger_status = "Zeigefinger GEBEUGT. 🤏"
                color_index = (255, 0, 0)  # Blau (Für GEBEUGT)
                zeigefinger_status = "0"
            cv2.putText(frame, gesture_zeigefinger_status, (50, 180),  # Position 100
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_index, 2, cv2.LINE_AA)  # FARBVARIABLE VERWENDET

            # --- GESTEN-LOGIK: MITTELFINGER (9 & 12) ---
            if y_mittelfinger_spitze_index < y_mittelfinger_basis_index - 0.25:
                gesture_middle_status = "MITTELFINGER STRECKT"
                color_middle = (0, 255, 255)
                mittelfinger_status = "1"
            else:
                gesture_middle_status = "Mittelfinger gebeugt"
                color_middle = (255, 0, 0)
                mittelfinger_status = "0"
            cv2.putText(frame, gesture_middle_status, (50, 210),  # NEUE POSITION 180 (KEINE ÜBERLAPPUNG)
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_middle, 2, cv2.LINE_AA)  # FARBVARIABLE VERWENDET

            if y_ringfinger_spitze_index < y_ringfinger_basis_index - 0.25:
                gesture_ringfinger_status = "RINGFINGER STRECKT"
                color_ringfinger = (0, 255, 255)
                ringfinger_status = "1"
            else:
                gesture_ringfinger_status = "Ringfinger gebeugt"
                color_ringfinger = (255, 0, 0)
                ringfinger_status = "0"
            cv2.putText(frame, gesture_ringfinger_status, (50, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ringfinger, 2, cv2.LINE_AA)

            if y_pinky_spitze_index < y_pinky_basis_index - 0.06:
                gesture_pinky_status = "PINKY STRECKT"
                color_pinky = (0, 255, 255)
                pinky_status = "1"
            else:
                gesture_pinky_status = "Pinky gebeugt"
                color_pinky = (255, 0, 0)
                pinky_status = "0"
            cv2.putText(frame, gesture_pinky_status, (50, 280),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_pinky, 2, cv2.LINE_AA)

            # --Fingerabdruck erstellen -- Abgleich zu Dict--
            aktueller_code = daumen_status + zeigefinger_status + mittelfinger_status + ringfinger_status + pinky_status

            erkannter_buchstabe = "?"
            erkannte_zahl = "?"
            winkel_anzeige = ""

            if aktueller_code == eins_code:
                x1 = normalized_landmarks[5][0]; y1 = normalized_landmarks[5][1]
                x2 = normalized_landmarks[17][0]; y2 = normalized_landmarks[17][1]
                angle_degree = math.degrees(math.atan2(y2 - y1, x2 - x1))
                winkel_anzeige = f" ( {int(angle_degree)})"

                if abs(angle_degree) < 25:
                    erkannter_buchstabe = "G"
                elif angle_degree > 60 and angle_degree < 120:
                    erkannte_zahl = "eins"
                else:
                    erkannter_buchstabe = " G / 1 ? "
            elif aktueller_code in gebaerden_sprache_dictionary_buchstaben:
                erkannter_buchstabe = gebaerden_sprache_dictionary_buchstaben[aktueller_code]
            elif aktueller_code in gebaerdensprache_dictionary_zahlen:
                erkannte_zahl = gebaerdensprache_dictionary_zahlen[aktueller_code]

            if erkannte_zahl != "?":
                cv2.putText(frame, f"Zahl: {erkannte_zahl}{winkel_anzeige}", (50, 350),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "Zahl: -", (50, 350),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (100,100,100), 2, cv2.LINE_AA)


            if erkannter_buchstabe != "?":
                cv2.putText(frame, f"Symbol: {erkannter_buchstabe}{winkel_anzeige}", (50, 450),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "Symbol: ?", (50, 450),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)


            anzahl_gestreckte_finger = aktueller_code.count("1")
            erkannte_zahl_str = str(f"Erk. Finger: {anzahl_gestreckte_finger}")
            cv2.putText(frame, erkannte_zahl_str, (50, 400),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
            """
            if aktueller_code in gebaerdensprache_dictionary_zahlen:
                erkannte_zahl = gebaerdensprache_dictionary_zahlen[aktueller_code]
                cv2.putText(frame, f"aktuelle Zahl: {erkannte_zahl}", (50, 350),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "Aktuelle Zahl: ?", (50, 350),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            #erkannte Zahl als String
            erkannte_zahl = str(f"Erkannte Anzahl an Finger: {anzahl_gestreckte_finger}")
            cv2.putText(frame, erkannte_zahl, (50, 400), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 0, 0), 4, cv2.LINE_AA)

            if aktueller_code in gebaerden_sprache_dictionary_buchstaben:
                erkannte_gebaerde = gebaerden_sprache_dictionary_buchstaben[aktueller_code]

                cv2.putText(frame, f"Buchstabe: {erkannte_gebaerde}", (50, 450),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 4, cv2.LINE_AA)

            else:
                cv2.putText(frame, "Buchstabe: ?", (50, 450),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 4, cv2.LINE_AA)

            """
            # --- ZEICHNEN (NUR EINMAL) ---
            # Die beiden redundanten Aufrufe wurden entfernt.
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
            )

    # Hier könnten Sie später Aktionen wie Tastendrücke (mit pyautogui) einfügen
    # Beispiel: print("Hand im Frame, Leertaste drücken!")

    else:
        # Keine Hand im Bild
        cv2.putText(frame, 'Suche Hand...', (frame.shape[1] - 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)




    # FPS Anzeige (Optional)
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(frame, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    # 6. Anzeige
    cv2.imshow('Hand Detection', frame)
    #cv2.imshow('Face Detection', frame)

    # Beenden mit 'q'
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# 7. Aufräumen
cam.release()
cv2.destroyAllWindows()