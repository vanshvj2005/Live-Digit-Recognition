import cv2
import numpy as np
import tensorflow as tf
import imutils

print("[INFO] Setting up camera and loading resources...")
model_path = 'digit_model.h5'

try:
    print(f"[INFO] Looking for {model_path}...")
    model = tf.keras.models.load_model(model_path)
    print(f"[SUCCESS] Deep Learning Model loaded.")
except Exception as e:
    print(f"[ERROR] Could not load '{model_path}'.")
    print("Have you run 'python train_digit_model.py' to build the CNN first?")
    exit()

def preprocess_for_cnn(roi):
    """
    OpenCV contours can be tight around the digit. The CNN (from MNIST) 
    expects a 28x28 image where the digit is roughly 20x20 in the very center.
    This function mimics that structure!
    """
    (h, w) = roi.shape
    
    # Check if the shape is abnormal to prevent crashes
    if w == 0 or h == 0:
        return None
        
    # Resize the longer dimension to 20 pixels, maintaining aspect ratio
    if w > h:
        new_w = 20
        new_h = int((h / w) * 20)
    else:
        new_h = 20
        new_w = int((w / h) * 20)
    
    # Avoid 0 dimensions from integer division
    if new_w <= 0: new_w = 1
    if new_h <= 0: new_h = 1

    roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Calculate padding to make it a perfect 28x28 square
    top = (28 - new_h) // 2
    bottom = 28 - new_h - top
    left = (28 - new_w) // 2
    right = 28 - new_w - left

    # Add black border (MNIST is white digit on black background)
    roi_padded = cv2.copyMakeBorder(roi, top, bottom, left, right, cv2.BORDER_CONSTANT, value=0)

    # Normalize pixels to 0-1 and reshape clearly for CNN (1 sample, 28x28 size, 1 channel)
    roi_padded = roi_padded.astype('float32') / 255.0
    roi_padded = roi_padded.reshape(1, 28, 28, 1)
    return roi_padded

print("[INFO] Searching for Webcam (Index 0)...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("[ERROR] Cannot access the webcam. Ensure it's not open in another app.")
    exit()

print("[INFO] Camera opened correctly! Hold up a digit written on a piece of paper.")
print("[TIP] For best results, use a dark marker on white paper!")
print("[INFO] Press 'q' key to Quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Frame grab failed.")
        break

    # We want processing to be fast, resize the frame slightly
    frame = imutils.resize(frame, width=640)
    
    # --- ADDING A CENTRAL "REGION OF INTEREST" BOX ---
    # This prevents the webcam from analyzing your whole room for digits
    (H, W) = frame.shape[:2]
    # 300x300 box in center
    box_size = 300
    startX = (W - box_size) // 2
    startY = (H - box_size) // 2
    endX = startX + box_size
    endY = startY + box_size
    
    # Draw guide box for user
    cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 0, 0), 2)
    cv2.putText(frame, "Place digit here", (startX, startY - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # Crop out just the region inside the box to process
    roi_frame = frame[startY:endY, startX:endX]
    
    # Convert crop to grayscale for thresholding
    gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    
    # Use Gaussian Blur to smooth out noise or textured paper
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive Threshold:
    # We increase block size to 51 and C to 10 to ignore gradient shadows on faces/paper 
    # but still pick up faint pen strokes on the paper.
    thresh = cv2.adaptiveThreshold(blurred, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 51, 10)

    # THICKEN THE LINES: 
    # The CNN (MNIST) was trained on thick handwriting (like a marker).
    # Since you are using a very fine tipped pen, we artificially dilate (thicken) the lines!
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    # Find the outlines (contours) of the isolated shapes in the cropped box
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        # Get local coordinate box
        (x, y, w, h) = cv2.boundingRect(c)
        
        # Filter based on size. A drawn digit should be tall. 
        # A straight "1" is extremely thin, so we allow widths down to 5 pixels.
        if (w >= 5 and w <= 250) and (h >= 45 and h <= 250):
            # Also consider aspect ratio! A straight "1" has a tiny aspect ratio (w/h)
            aspect_ratio = w / float(h)
            
            if 0.05 <= aspect_ratio <= 1.5: # Valid shape for a character
                # Extract the Region of Interest from the Thresholded mask
                roi = thresh[y:y+h, x:x+w]
                
                # Check "fill ratio": The amount of ink inside the bounding box.
                # A giant digit drawn with a fine pen has a very low fill ratio natively,
                # but our 5x5 dilation thickens the lines safely above 2%.
                ink_pixels = cv2.countNonZero(roi)
                total_pixels = w * h
                fill_ratio = ink_pixels / total_pixels
                
                if 0.02 <= fill_ratio <= 0.70:
                    # Preprocess Region Into MNIST shape
                    processed_roi = preprocess_for_cnn(roi)
                    
                    if processed_roi is not None:
                        # Run the trained CNN forward pass
                        prediction = model.predict(processed_roi, verbose=0)
                        
                        digit = np.argmax(prediction[0])
                        confidence = np.max(prediction[0])

                        # Only show results the model is very sure about
                        if confidence > 0.96:
                            # Draw green box on the MAIN frame (we have to offset x and y by startX and startY)
                            drawX = startX + x
                            drawY = startY + y
                            cv2.rectangle(frame, (drawX, drawY), (drawX + w, drawY + h), (0, 255, 0), 2)
                            
                            text = f"{digit} ({confidence*100:.1f}%)"
                            cv2.putText(frame, text, (drawX, drawY - 10),
                                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)

    # Top-Left visual helper so you can see the raw shape mask the CNN is looking at
    cv2.imshow("Raw Mask Output (What the network sees)", cv2.resize(thresh, (300, 300)))
    cv2.imshow("Live CNN Digit Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("[INFO] Quitting gracefully...")
        break

cap.release()
cv2.destroyAllWindows()
