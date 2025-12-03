import cv2
import mediapipe as mp
import time
import math


#--- KONSTANTEN (X/Y Werte, Winkel)---
Y_STRECK_SCHWELLE_ZEIG_MITT_RING = 0.25
Y_STRECK_SCHWELLE_PINKY = 0.06

DAUMEN_X_OFFSET_STRECKUNG = 0.04
DAUMEN_Y_OFFSET_MAX_BEUGUNG = 0.05

WINKEL_SCHWELLE_HORIZONTAL = 30 #25 auf 30 änderung
WINKEL_SCHWELLE_VERTIKAL_MIN = 60
WINKEL_SCHWELLE_VERTIKAL_MAX = 120

#>_________---------DATENBANK GEBÄRDEN--------____________<

#Zahlen
faust_code = "00000"
eins_code = "01000"
zwei_code = "01100"
drei_code = "01110"
vier_code = "01111"
fuenf_code = "11111"

#Buchstaben
a_code = "10000"
b_code = "01111"
v_code = "01100"
#TODO: implementierung rest buchstaben

#Dictionaries
gebaerden_sprache_dictionary_zahlen = \
    {
    faust_code: "null",
    eins_code: "eins",
    zwei_code: "zwei",
    drei_code: "drei",
    vier_code: "vier",
    fuenf_code: "fuenf",
    }
gebaerden_sprache_dictionary_buchstaben = \
    {
    a_code: "a",
    b_code: "b",
    v_code: "v",
    }


# 1. MediaPipe Initialisierung für Handerkennung
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands= 2,
    min_detection_confidence=0.7  # Höhere Konfidenz für bessere Genauigkeit
)
mp_drawing = mp.solutions.drawing_utils

#2. Kamera initialisierung
cam = cv2.VideoCapture(1)
if not cam.isOpened():
    print("Fehler: Kamera konnte nicht geöffnet werden. Prüfen Sie den Kamera-Index und die Systemberechtigungen.")
    exit()

print("Kamera läuft. Bringen Sie Ihre Hand ins Bild und drücken Sie 'q' zum Beenden.")
pTime = 0   #FPS ANZEIGE

def get_finger_status(normalized_handmarks, frame):
    """
    ermittelt 5-Stelligen Fingerstatus-Code (vgl: eins_code, ...)
    normalized_handmarks mit original_handmarks änderung
    """

    x_daumen_spitze = normalized_landmarks[4][0]
    y_daumen_spitze = normalized_landmarks[4][1]
    x_daumen_basis = normalized_landmarks[2][0]
    y_zeigefinger_basis = normalized_landmarks[5][1]

    #status initialisierung
    daumen_status = "0"
    if (x_daumen_spitze > x_daumen_basis + DAUMEN_X_OFFSET_STRECKUNG) and \
        (y_daumen_spitze < y_zeigefinger_basis - DAUMEN_Y_OFFSET_MAX_BEUGUNG):
        daumen_status = "1"
        color_daumen = (0, 255, 255)
        gesture_daumen_status = "Daumen streckt"
    else:
        daumen_status = "0"
        color_daumen = (255, 0, 0)
        gesture_daumen_status = "Daumen gebeugt"
    cv2.putText(frame, gesture_daumen_status, (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color_daumen, 2, cv2.LINE_AA)


    #ANDERE FINGERLOGIK (ZEIGEFINGER, MITTELFINGER, RINGFINGER, PINKY)
    #Index der Spitzen von hand.landmarks
    FINER_DATA = [
        (8,5, Y_STRECK_SCHWELLE_ZEIG_MITT_RING, "Zeigefinger"),
        (12, 9, Y_STRECK_SCHWELLE_ZEIG_MITT_RING, "Mittelfinger"),
        (16, 13, Y_STRECK_SCHWELLE_ZEIG_MITT_RING, "Ringfinger"),
        (20, 17, Y_STRECK_SCHWELLE_PINKY, "Pinky")
    ]

    aktueller_code = daumen_status
    text_y_start = 180

    for i, (tip_id, base_id, schwelle, name) in enumerate(FINER_DATA):
        y_tip = normalized_landmarks[tip_id][1]
        y_base = normalized_landmarks[base_id][1]

        status = "0"

        if y_tip < y_base - schwelle:
            status = "1"
            color = (0, 255, 255)
            gesture_status = f"{name.upper()} STRECKT"
        else:
            color = (255, 0, 0)
            gesture_status = f"{name.upper()} beugt"

        aktueller_code += status

        cv2.putText(frame, gesture_status, (50, text_y_start + i * 30),
        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    return aktueller_code

def detect_gesture(aktueller_code, original_hand_landmarks):
    """
    führt Abgleich von Fingerabdruck mit Datenbank
    beinhaltet Logik zur unterscheiden 1 zu G, spätere weitere Buchstaben
    WICHTIG: normalized_handmarks entfernt test!
    """
    erkannte_zahl = "?"
    erkannter_buchstabe = "?"
    winkel_anzeige = ""
    angle_degree = None

    if aktueller_code == eins_code:
        #Landmarks für Winkel der Handfläche
        #x1 = normalized_landmarks[5][0]
        #y1 = normalized_landmarks[5][1]
        #x2 = normalized_landmarks[17][0]
        #y2 = normalized_landmarks[17][1]
        x1 = original_hand_landmarks.landmark[0].x
        y1 = original_hand_landmarks.landmark[0].y
        x2 = original_hand_landmarks.landmark[9].x
        y2 = original_hand_landmarks.landmark[9].y

        #Berechnung Winkel im Grad zwischen beide Punkte
        angle_degree = math.degrees(math.atan2(y2 - y1, x2 - x1))
        winkel_anzeige = f"{int(angle_degree)} deg)"

        # Unterscheidung 1 vs G:
        #Handfläche horizontal heißt G
        if abs(angle_degree) < WINKEL_SCHWELLE_HORIZONTAL or abs(angle_degree) > 180 - WINKEL_SCHWELLE_HORIZONTAL:
            erkannter_buchstabe = "G"
            erkannter_zahl = "-"
        elif WINKEL_SCHWELLE_VERTIKAL_MIN < angle_degree < WINKEL_SCHWELLE_VERTIKAL_MAX:
            erkannte_zahl = "1"
            erkannter_buchstabe = "-"
        else:
            erkannter_buchstabe = "G / 1? "
            erkannte_zahl = "-"
    elif aktueller_code in gebaerden_sprache_dictionary_buchstaben:
        erkannter_buchstabe = gebaerden_sprache_dictionary_buchstaben[aktueller_code]
    elif aktueller_code in gebaerden_sprache_dictionary_zahlen:
        erkannte_zahl = gebaerden_sprache_dictionary_zahlen[aktueller_code]

    return erkannte_zahl, erkannter_buchstabe, winkel_anzeige

def draw_status_text(frame, erkannte_zahl, erkannter_buchstabe, winkel_anzeige, aktueller_code):
    """
    Zeichnet alle Ergebnisse auf Frame
    """
    anzahl_gestreckte_finger = aktueller_code.count("1")

    if erkannte_zahl != "?":
        text_zahl = f"Zahl: {erkannte_zahl}{winkel_anzeige}"
        color_zahl = (0, 0, 255)
    else:
        text_zahl = "Zahl: -"
        color_zahl = (100, 100, 100)
    cv2.putText(frame, text_zahl, (50, 350),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color_zahl, 2, cv2.LINE_AA)

    erkannte_anzahl_str = f"Erkannte Finger: {anzahl_gestreckte_finger} (Code: {aktueller_code})"
    cv2.putText(frame, erkannte_anzahl_str, (50, 400),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    if erkannter_buchstabe != "?":
        text_symbol = f"Symbol: {erkannter_buchstabe}{winkel_anzeige}"
        color_symbol = (0, 0, 255)
    else:
        text_symbol = "Symbol: ?"
        color_symbol = (100, 100, 100)
    cv2.putText(frame, text_symbol, (50, 450),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color_symbol, 2, cv2.LINE_AA)

#-----___________MAINLOOP__________----------

while True:
    ret, frame = cam.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results_hands = hands.process(image_rgb)

    if results_hands.multi_hand_landmarks:
        cv2.putText(frame, "HANDS ERKANNT", (frame.shape[1]- 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        for hand_landmarks in results_hands.multi_hand_landmarks:
            wrist_landmark = hand_landmarks.landmark[0]
            normalized_landmarks = []

            for landmark in hand_landmarks.landmark:
                relative_x = landmark.x - wrist_landmark.x
                relative_y = landmark.y - wrist_landmark.y
                normalized_landmarks.append([relative_x, relative_y])

            aktueller_code = get_finger_status(normalized_landmarks, frame)
            erkannte_zahl, erkannter_buchstabe, winkel_anzeige = detect_gesture(aktueller_code, hand_landmarks)
            draw_status_text(frame, erkannte_zahl, erkannter_buchstabe, winkel_anzeige, aktueller_code)

            #Zeichnen von Landmarks
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
            )
    else:
        cv2.putText(frame, "Suche HANDS", (frame.shape[1]- 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    #6. Anzeige und Beenden
    cv2.imshow("Hand Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

#7. Aufräumen
cam.release()
cv2.destroyAllWindows()



