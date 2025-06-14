#!/usr/bin/env python
"""
Blood Pressure Data Generator Script

This script generates simulated blood pressure data and sends it to the API endpoint.
It only requires a username to work.

Usage:
    python test_blood_pressure_generator.py --username YOUR_USERNAME

The script will generate random blood pressure values within normal ranges:
- Systolic: 110-130 mmHg
- Diastolic: 70-85 mmHg

with occasional variations to simulate real-world blood pressure patterns.
"""

import requests
import random
import time
import argparse
import json
from datetime import datetime

# Special test API endpoint, no authentication required
API_URL = "http://localhost:8000/api/test/blood-pressure/add/"

def generate_blood_pressure(base_systolic=120, base_diastolic=80, variation=5):
    """Generate realistic blood pressure values."""
    # Add some random variation to the base values
    systolic = base_systolic + random.uniform(-variation, variation)
    diastolic = base_diastolic + random.uniform(-variation/2, variation/2)
    
    # Ensure systolic is always higher than diastolic
    if systolic <= diastolic:
        systolic = diastolic + 30
    
    # Occasionally simulate a more significant change (exercise, stress, etc.)
    if random.random() < 0.1:  # 10% chance
        systolic += random.uniform(-10, 15)
        diastolic += random.uniform(-5, 10)
    
    # Ensure the blood pressure stays within realistic bounds
    systolic = max(90, min(160, systolic))
    diastolic = max(60, min(100, diastolic))
    
    # Ensure systolic is at least 30 points higher than diastolic
    if systolic - diastolic < 30:
        diastolic = systolic - 30
    
    return round(systolic), round(diastolic)

def send_blood_pressure_data(username):
    """Send blood pressure data to the API endpoint."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    systolic, diastolic = generate_blood_pressure()
    
    data = {
        'username': username,
        'systolic': systolic,
        'diastolic': diastolic
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        
        if response.status_code == 201:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Blood pressure data sent successfully for user {username}: {systolic}/{diastolic} mmHg")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error sending data: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Exception: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate and send blood pressure data to API')
    parser.add_argument('--username', required=True, help='Username to associate with the data')
    parser.add_argument('--interval', type=float, default=5.0, help='Interval between data points (seconds)')
    
    args = parser.parse_args()
    
    print(f"Blood Pressure Data Generator")
    print(f"Sending data for user '{args.username}' every {args.interval} seconds. Press Ctrl+C to stop.")
    
    try:
        while True:
            send_blood_pressure_data(args.username)
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\nGenerator stopped.")

if __name__ == "__main__":
    main() 