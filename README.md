# Live-Digit-Recognition
  Step-by-Step Setup & Execution Guide

 Step 1: Train the Model

Run the training script to generate the trained model:

bash
python train_digit_model.py

This will:

 Download MNIST dataset automatically
 Train the CNN model
 Save the model as `digit_model.h5`

 Step 2: Run the Live Digit Recognition System

bash
python live_digit_recognition.py


  Step 3: Using the Application

 A webcam window will open
 A box will appear in the center
 Write a digit (0–9) on paper
 Place it inside the box
 The system will display:

  * Predicted digit
  * Confidence score

Press **'q'** to exit the application

Important Notes

 Ensure webcam is not used by another application
 Run `train_digit_model.py` before running detection
 Keep all files in the same directory
 Make sure `digit_model.h5` exists before running

