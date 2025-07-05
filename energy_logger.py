#!/usr/bin/env python3
"""
Tuya Smart Meter Energy Logger - GitHub Storage
Logs forward_energy_total to CSV files in GitHub repository
Completely free solution using GitHub Actions and repository storage
"""

import os
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from tuya_connector import TuyaOpenAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Tuya API Configuration
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY") 
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
API_ENDPOINT = os.getenv("TUYA_API_ENDPOINT", "https://openapi.tuyaeu.com")

# Data storage configuration
DATA_DIR = Path("data")
DAILY_DATA_DIR = DATA_DIR / "daily"
MONTHLY_DATA_DIR = DATA_DIR / "monthly"

def ensure_directories():
    """Create necessary directories if they don't exist"""
    DATA_DIR.mkdir(exist_ok=True)
    DAILY_DATA_DIR.mkdir(exist_ok=True)
    MONTHLY_DATA_DIR.mkdir(exist_ok=True)

def get_tuya_energy_data():
    """Get forward_energy_total from Tuya smart meter"""
    try:
        # Initialize API connection
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
        openapi.connect()
        
        print(f"🔌 Connecting to Tuya device: {DEVICE_ID}")
        
        # Get device status
        status_response = openapi.get(f"/v1.0/devices/{DEVICE_ID}/status")
        
        if not status_response.get("success"):
            raise Exception(f"Tuya API error: {status_response.get('msg')}")
        
        # Parse status data
        status_data = status_response["result"]
        data_points = {item["code"]: item["value"] for item in status_data}
        
        print(f"📊 Available data points: {list(data_points.keys())}")
        
        # Get forward_energy_total
        if "forward_energy_total" not in data_points:
            raise Exception("forward_energy_total not found in device data")
        
        forward_energy = data_points["forward_energy_total"]/100
        timestamp = datetime.now(timezone.utc)
        
        print(f"⚡ Forward Energy Total: {forward_energy} kWh")
        print(f"🕐 Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return {
            "timestamp": timestamp,
            "forward_energy_total": forward_energy,
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S"),
            "hour": timestamp.hour,
            "day_of_week": timestamp.strftime("%A"),
            "unix_timestamp": int(timestamp.timestamp()),
            "all_data": data_points
        }
        
    except Exception as e:
        print(f"❌ Error getting Tuya data: {str(e)}")
        raise

def log_to_daily_csv(energy_data):
    """Log data to daily CSV file"""
    date_str = energy_data["date"]
    daily_file = DAILY_DATA_DIR / f"energy_{date_str}.csv"
    
    # CSV headers
    headers = [
        "timestamp",
        "date", 
        "time",
        "forward_energy_total_kwh",
        "hour",
        "day_of_week",
        "unix_timestamp"
    ]
    
    # Check if file exists to determine if we need headers
    file_exists = daily_file.exists()
    
    # Append data to daily file
    with open(daily_file, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write headers if file is new
        if not file_exists:
            writer.writerow(headers)
            print(f"📝 Created new daily file: {daily_file}")
        
        # Write data row
        row = [
            energy_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC"),
            energy_data["date"],
            energy_data["time"],
            energy_data["forward_energy_total"],
            energy_data["hour"],
            energy_data["day_of_week"],
            energy_data["unix_timestamp"]
        ]
        
        writer.writerow(row)
        print(f"✅ Data logged to: {daily_file}")

def log_to_monthly_summary(energy_data):
    """Log data to monthly summary CSV file"""
    year_month = energy_data["timestamp"].strftime("%Y-%m")
    monthly_file = MONTHLY_DATA_DIR / f"energy_summary_{year_month}.csv"
    
    # Read existing data if file exists
    existing_data = []
    if monthly_file.exists():
        with open(monthly_file, 'r') as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)
    
    # Find if we already have data for this date
    date_str = energy_data["date"]
    existing_entry = None
    for i, row in enumerate(existing_data):
        if row["date"] == date_str:
            existing_entry = i
            break
    
    # Calculate daily stats (you could enhance this with more readings per day)
    new_entry = {
        "date": date_str,
        "day_of_week": energy_data["day_of_week"],
        "latest_reading_kwh": energy_data["forward_energy_total"],
        "last_updated": energy_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC"),
        "readings_count": 1
    }
    
    # Update existing entry or add new one
    if existing_entry is not None:
        # Update existing entry
        existing_data[existing_entry] = new_entry
    else:
        # Add new entry
        existing_data.append(new_entry)
    
    # Sort by date
    existing_data.sort(key=lambda x: x["date"])
    
    # Write updated data
    headers = ["date", "day_of_week", "latest_reading_kwh", "last_updated", "readings_count"]
    with open(monthly_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(existing_data)
    
    print(f"📊 Monthly summary updated: {monthly_file}")

def create_latest_reading_file(energy_data):
    """Create a file with the latest reading for easy access"""
    latest_file = DATA_DIR / "latest_reading.json"
    
    latest_data = {
        "timestamp": energy_data["timestamp"].isoformat(),
        "date": energy_data["date"],
        "time": energy_data["time"],
        "forward_energy_total_kwh": energy_data["forward_energy_total"],
        "hour": energy_data["hour"],
        "day_of_week": energy_data["day_of_week"],
        "unix_timestamp": energy_data["unix_timestamp"],
        "formatted_reading": f"{energy_data['forward_energy_total']} kWh at {energy_data['date']} {energy_data['time']} UTC"
    }
    
    with open(latest_file, 'w') as f:
        json.dump(latest_data, f, indent=2)
    
    print(f"📌 Latest reading saved: {latest_file}")

def create_readme():
    """Create/update README with data information"""
    readme_file = DATA_DIR / "README.md"
    
    readme_content = f"""# Energy Data

This directory contains energy consumption data from your Tuya smart meter.

## Data Structure

### Daily Data (`daily/`)
- Individual CSV files for each day: `energy_YYYY-MM-DD.csv`
- Contains hourly readings with timestamp, energy total, and metadata
- New file created automatically for each day

### Monthly Summaries (`monthly/`)
- Monthly summary files: `energy_summary_YYYY-MM.csv`
- Contains daily summaries and statistics
- Updated automatically as new data arrives

### Latest Reading (`latest_reading.json`)
- Always contains the most recent energy reading
- Updated every hour
- Easy to parse for current status

## Data Columns

**Daily Files:**
- `timestamp`: Full datetime in UTC
- `date`: Date (YYYY-MM-DD)
- `time`: Time (HH:MM:SS)
- `forward_energy_total_kwh`: Energy reading in kWh
- `hour`: Hour of day (0-23)
- `day_of_week`: Day name (Monday, Tuesday, etc.)
- `unix_timestamp`: Unix timestamp for easy processing

**Monthly Files:**
- `date`: Date (YYYY-MM-DD)
- `day_of_week`: Day name
- `latest_reading_kwh`: Latest energy reading for that day
- `last_updated`: When the data was last updated
- `readings_count`: Number of readings for that day

## Automated Collection

Data is automatically collected every hour using GitHub Actions.

Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"📖 README updated: {readme_file}")

def main():
    """Main execution function"""
    print("🚀 Tuya Energy Logger Starting...")
    print("=" * 50)
    
    # Validate environment variables
    required_vars = ["TUYA_ACCESS_ID", "TUYA_ACCESS_KEY", "TUYA_DEVICE_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Get energy data from Tuya
        energy_data = get_tuya_energy_data()
        
        # Log to daily CSV
        log_to_daily_csv(energy_data)
        
        # Log to monthly summary
        log_to_monthly_summary(energy_data)
        
        # Create latest reading file
        create_latest_reading_file(energy_data)
        
        # Update README
        create_readme()
        
        print("\n🎉 Energy logging completed successfully!")
        print(f"📊 Energy Reading: {energy_data['forward_energy_total']} kWh")
        print(f"📅 Date: {energy_data['date']} {energy_data['time']} UTC")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)