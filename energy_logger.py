#!/usr/bin/env python3
"""
Tuya Smart Meter Energy Logger - GitHub Storage with Graphs
Logs forward_energy_total to CSV files in GitHub repository
Generates consumption graphs and embeds them in README.md
"""

import os
import csv
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tuya_connector import TuyaOpenAPI
from dotenv import load_dotenv
import pandas as pd
from collections import defaultdict

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
GRAPHS_DIR = DATA_DIR / "graphs"

def ensure_directories():
    """Create necessary directories if they don't exist"""
    DATA_DIR.mkdir(exist_ok=True)
    DAILY_DATA_DIR.mkdir(exist_ok=True)
    MONTHLY_DATA_DIR.mkdir(exist_ok=True)
    GRAPHS_DIR.mkdir(exist_ok=True)

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

def get_monthly_consumption_data():
    """Calculate monthly consumption from daily data"""
    monthly_consumption = {}
    
    # Get all daily files
    daily_files = list(DAILY_DATA_DIR.glob("energy_*.csv"))
    
    if not daily_files:
        print("⚠️  No daily data files found")
        return monthly_consumption
    
    # Group files by month
    monthly_files = defaultdict(list)
    for file in daily_files:
        date_str = file.stem.replace("energy_", "")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            year_month = date_obj.strftime("%Y-%m")
            monthly_files[year_month].append((date_obj, file))
        except ValueError:
            continue
    
    # Calculate consumption for each month
    for year_month, files in monthly_files.items():
        files.sort(key=lambda x: x[0])  # Sort by date
        
        # Get first and last day's data
        first_day_file = files[0][1]
        last_day_file = files[-1][1]
        
        try:
            # Read first day's first reading
            with open(first_day_file, 'r') as f:
                reader = csv.DictReader(f)
                first_reading = next(reader)
                month_start_energy = float(first_reading['forward_energy_total_kwh'])
            
            # Read last day's last reading
            with open(last_day_file, 'r') as f:
                reader = csv.DictReader(f)
                last_reading = None
                for row in reader:
                    last_reading = row
                month_end_energy = float(last_reading['forward_energy_total_kwh'])
            
            # Calculate consumption
            consumption = month_end_energy - month_start_energy
            monthly_consumption[year_month] = consumption
            
            print(f"📅 {year_month}: {consumption:.2f} kWh consumed")
            
        except Exception as e:
            print(f"⚠️  Error processing {year_month}: {str(e)}")
            continue
    
    return monthly_consumption

def get_daily_consumption_data(target_month=None):
    """Calculate daily consumption for the last month or specified month"""
    if target_month is None:
        # Get current month
        current_date = datetime.now(timezone.utc)
        target_month = current_date.strftime("%Y-%m")
    
    daily_consumption = {}
    
    # Get all daily files for the target month
    daily_files = list(DAILY_DATA_DIR.glob(f"energy_{target_month}-*.csv"))
    
    if not daily_files:
        print(f"⚠️  No daily data files found for {target_month}")
        return daily_consumption
    
    # Sort files by date
    daily_files.sort()
    
    prev_day_last_reading = None
    
    for i, file in enumerate(daily_files):
        date_str = file.stem.replace("energy_", "")
        
        try:
            with open(file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    continue
                
                # Get first and last reading of the day
                first_reading = float(rows[0]['forward_energy_total_kwh'])
                last_reading = float(rows[-1]['forward_energy_total_kwh'])
                
                # Calculate daily consumption
                if i == 0:
                    # For first day, use difference within the day
                    daily_consumption[date_str] = last_reading - first_reading
                else:
                    # Use last reading of previous day
                    if prev_day_last_reading is not None:
                        daily_consumption[date_str] = last_reading - prev_day_last_reading
                    else:
                        daily_consumption[date_str] = last_reading - first_reading
                
                prev_day_last_reading = last_reading
                
        except Exception as e:
            print(f"⚠️  Error processing {date_str}: {str(e)}")
            continue
    
    return daily_consumption

def create_yearly_consumption_graph():
    """Create yearly consumption graph"""
    monthly_data = get_monthly_consumption_data()
    
    if not monthly_data:
        print("⚠️  No data available for yearly consumption graph")
        return None
    
    # Prepare data for plotting
    months = []
    consumption = []
    
    for year_month in sorted(monthly_data.keys()):
        months.append(datetime.strptime(year_month, "%Y-%m"))
        consumption.append(monthly_data[year_month])
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(months, consumption, marker='o', linewidth=2, markersize=8)
    plt.title('Monthly Energy Consumption', fontsize=16, fontweight='bold')
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Energy Consumption (kWh)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    # Add value labels on points
    for i, (month, cons) in enumerate(zip(months, consumption)):
        plt.annotate(f'{cons:.1f}', (month, cons), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=10)
    
    plt.tight_layout()
    
    # Save the graph
    graph_file = GRAPHS_DIR / "yearly_consumption.png"
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📈 Yearly consumption graph saved: {graph_file}")
    return graph_file

def create_daily_consumption_graph():
    """Create daily consumption graph for the last month"""
    current_date = datetime.now(timezone.utc)
    current_month = current_date.strftime("%Y-%m")
    
    daily_data = get_daily_consumption_data(current_month)
    
    if not daily_data:
        print(f"⚠️  No data available for daily consumption graph ({current_month})")
        return None
    
    # Prepare data for plotting
    dates = []
    consumption = []
    
    for date_str in sorted(daily_data.keys()):
        dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
        consumption.append(daily_data[date_str])
    
    # Create the plot
    plt.figure(figsize=(14, 6))
    plt.bar(dates, consumption, alpha=0.7, color='steelblue')
    plt.title(f'Daily Energy Consumption - {current_month}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Energy Consumption (kWh)', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45)
    
    # Add value labels on bars
    for i, (date, cons) in enumerate(zip(dates, consumption)):
        if cons > 0:  # Only show positive values
            plt.annotate(f'{cons:.1f}', (date, cons), textcoords="offset points", 
                        xytext=(0,5), ha='center', fontsize=9)
    
    plt.tight_layout()
    
    # Save the graph
    graph_file = GRAPHS_DIR / f"daily_consumption_{current_month}.png"
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Daily consumption graph saved: {graph_file}")
    return graph_file

def create_readme():
    """Create/update README with data information and graphs"""
    readme_file = DATA_DIR / "README.md"
    
    # Generate graphs
    yearly_graph = create_yearly_consumption_graph()
    daily_graph = create_daily_consumption_graph()
    
    # Get latest reading for summary
    latest_file = DATA_DIR / "latest_reading.json"
    latest_reading = "N/A"
    if latest_file.exists():
        try:
            with open(latest_file, 'r') as f:
                latest_data = json.load(f)
                latest_reading = latest_data.get("formatted_reading", "N/A")
        except:
            pass
    
    # Calculate total consumption
    monthly_data = get_monthly_consumption_data()
    total_consumption = sum(monthly_data.values()) if monthly_data else 0
    
    readme_content = f"""# Energy Consumption Dashboard

## 📊 Consumption Overview

**Latest Reading:** {latest_reading}  
**Total Consumption:** {total_consumption:.2f} kWh  
**Monitoring Period:** {len(monthly_data)} months  

## 📈 Yearly Consumption Trends

"""
    
    # Add yearly graph if available
    if yearly_graph:
        readme_content += f"![Yearly Consumption](graphs/{yearly_graph.name})\n\n"
    else:
        readme_content += "*Yearly consumption graph will be available once data is collected.*\n\n"
    
    readme_content += "## 📅 Daily Consumption (Current Month)\n\n"
    
    # Add daily graph if available
    if daily_graph:
        readme_content += f"![Daily Consumption](graphs/{daily_graph.name})\n\n"
    else:
        readme_content += "*Daily consumption graph will be available once daily data is collected.*\n\n"
    
    readme_content += f"""## 📋 Data Structure

### Daily Data (`daily/`)
- Individual CSV files for each day: `energy_YYYY-MM-DD.csv`
- Contains hourly readings with timestamp, energy total, and metadata
- New file created automatically for each day

### Monthly Summaries (`monthly/`)
- Monthly summary files: `energy_summary_YYYY-MM.csv`
- Contains daily summaries and statistics
- Updated automatically as new data arrives

### Graphs (`graphs/`)
- `yearly_consumption.png`: Monthly consumption trends
- `daily_consumption_YYYY-MM.png`: Daily consumption for each month

### Latest Reading (`latest_reading.json`)
- Always contains the most recent energy reading
- Updated every hour
- Easy to parse for current status

## 📊 Data Columns

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

## 🔄 Automated Collection

Data is automatically collected every hour using GitHub Actions.

## 📈 Consumption Calculation

- **Monthly Consumption**: Difference between last reading of the month and first reading of the month
- **Daily Consumption**: Difference between last reading of the day and last reading of the previous day

Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"📖 README updated with graphs: {readme_file}")

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
        
        # Create/update README with graphs
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
