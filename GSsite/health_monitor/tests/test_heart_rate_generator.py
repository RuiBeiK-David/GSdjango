#!/usr/bin/env python
"""
Heart Rate Data Generator Script

This script generates simulated heart rate data and sends it to the API endpoint.
It only requires a username to work.

Usage:
    python test_heart_rate_generator.py --username YOUR_USERNAME

The script will generate random heart rate values within a normal range (60-100 BPM)
with occasional variations to simulate real-world heart rate patterns.
"""

import requests
import random
import time
import argparse
import json
from datetime import datetime

# Special test API endpoint, no authentication required
API_URL = "http://localhost:8000/api/test/heart-rate/add/"

def generate_heart_rate(base_rate=75, variation=5):
    """Generate a realistic heart rate value."""
    # Add some random variation to the base rate
    heart_rate = base_rate + random.uniform(-variation, variation)
    
    # Occasionally simulate a more significant change (exercise, stress, etc.)
    if random.random() < 0.1:  # 10% chance
        heart_rate += random.uniform(-15, 15)
    
    # Ensure the heart rate stays within realistic bounds
    heart_rate = max(50, min(120, heart_rate))
    
    return round(heart_rate, 1)

def send_heart_rate_data(username):
    """Send heart rate data to the API endpoint."""
    headers = {
        'Content-Type': 'application/json'
    }
    
    heart_rate = generate_heart_rate()
    
    data = {
        'username': username,
        'heart_rate': heart_rate
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        
        if response.status_code == 201:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Heart rate data sent successfully for user {username}: {heart_rate} BPM")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error sending data: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Exception: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate and send heart rate data to API')
    parser.add_argument('--username', required=True, help='Username to associate with the data')
    parser.add_argument('--interval', type=float, default=5.0, help='Interval between data points (seconds)')
    
    args = parser.parse_args()
    
    print(f"Heart Rate Data Generator")
    print(f"Sending data for user '{args.username}' every {args.interval} seconds. Press Ctrl+C to stop.")
    
    try:
        while True:
            send_heart_rate_data(args.username)
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\nGenerator stopped.")

if __name__ == "__main__":
    main() 