# Tuya Energy Logger - GitHub Storage (100% FREE!)

This solution logs your Tuya smart meter's `forward_energy_total` to CSV files directly in your GitHub repository. No paid services required!

## 🆓 Why This Solution is Better

- **100% Free**: Uses only GitHub (free tier)
- **No External Dependencies**: No Google Cloud, no third-party services
- **Data Ownership**: Your data stays in your repository
- **Version Control**: Full history of all changes
- **Easy Access**: Download CSV files anytime
- **Automatic Backup**: GitHub handles backup and sync
- **No Rate Limits**: No API quotas to worry about

## 📊 Data Structure

The script creates this structure in your repository:

```
your-repo/
├── data/
│   ├── daily/
│   │   ├── energy_2024-01-01.csv
│   │   ├── energy_2024-01-02.csv
│   │   └── ...
│   ├── monthly/
│   │   ├── energy_summary_2024-01.csv
│   │   ├── energy_summary_2024-02.csv
│   │   └── ...
│   ├── latest_reading.json
│   └── README.md
├── energy_logger.py
├── requirements.txt
└── .github/workflows/energy-logger.yml
```

## 🚀 Quick Setup (5 minutes!)

### 1. Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and create a new repository
2. Make it public or private (your choice)
3. Clone it to your computer or use GitHub's web interface

### 2. Add Files to Repository
Upload these files:
- `energy_logger.py` (main script)
- `requirements.txt` (dependencies)
- `.github/workflows/energy-logger.yml` (automation)

### 3. Set GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
- `TUYA_ACCESS_ID`: Your Tuya API Access ID
- `TUYA_ACCESS_KEY`: Your Tuya API Access Key
- `TUYA_DEVICE_ID`: Your smart meter device ID
- `TUYA_API_ENDPOINT`: Your regional endpoint (e.g., `https://openapi.tuyaeu.com`)

### 4. Enable GitHub Actions
1. Go to your repository → Actions tab
2. If prompted, enable GitHub Actions
3. Click "Run workflow" to test manually

### 5. Done! 🎉
Your energy data will now be logged every hour automatically!

## 📋 What You Get

### Daily CSV Files (`data/daily/`)
Each day gets its own CSV file with hourly readings:
```csv
timestamp,date,time,forward_energy_total_kwh,hour,day_of_week,unix_timestamp
2024-01-01 00:00:00 UTC,2024-01-01,00:00:00,1234.5,0,Monday,1704067200
2024-01-01 01:00:00 UTC,2024-01-01,01:00:00,1235.1,1,Monday,1704070800
```

### Monthly Summary Files (`data/monthly/`)
Monthly summaries with daily statistics:
```csv
date,day_of_week,latest_reading_kwh,last_updated,readings_count
2024-01-01,Monday,1250.5,2024-01-01 23:00:00 UTC,24
2024-01-02,Tuesday,1275.2,2024-01-02 23:00:00 UTC,24
```

### Latest Reading (`data/latest_reading.json`)
Always current reading for easy access:
```json
{
  "timestamp": "2024-01-01T12:00:00+00:00",
  "forward_energy_total_kwh": 1242.3,
  "formatted_reading": "1242.3 kWh at 2024-01-01 12:00:00 UTC"
}
```

## 🔧 Customization Options

### Change Schedule
Edit `.github/workflows/energy-logger.yml`:
```yaml
# Every 30 minutes
- cron: '*/30 * * * *'

# Every 6 hours  
- cron: '0 */6 * * *'

# Daily at 8 AM
- cron: '0 8 * * *'
```

### Add More Data Points
Modify the `get_tuya_energy_data()` function to capture additional values from your smart meter.

### Custom Data Processing
The script logs raw data - you can add calculations for:
- Daily consumption (difference between readings)
- Cost calculations
- Usage patterns
- Alerts for unusual consumption

## 📈 Using Your Data

### Download CSV Files
1. Go to your repository → data folder
2. Click on any CSV file
3. Click "Raw" to download
4. Open in Excel, Google Sheets, or any spreadsheet app

### View in GitHub
- Click on CSV files to see data directly in GitHub
- Use the blame view to see when each reading was added
- View commit history to see all changes

### Programming Access
```python
# Read latest reading
import json
with open('data/latest_reading.json') as f:
    latest = json.load(f)
    print(f"Current: {latest['formatted_reading']}")

# Read daily data
import csv
with open('data/daily/energy_2024-01-01.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"{row['time']}: {row['forward_energy_total_kwh']} kWh")
```

## 🔍 Monitoring & Troubleshooting

### Check if it's Working
1. Go to your repository → Actions tab
2. Look for green checkmarks ✅
3. Check the `data/` folder for new files
4. View `data/latest_reading.json` for current status

### Common Issues

**"No data appearing"**
- Check GitHub Actions logs for errors
- Verify your Tuya credentials are correct
- Ensure your device is online

**"Authentication failed"**
- Double-check your GitHub Secrets
- Make sure device ID is correct
- Verify API endpoint matches your region

**"Workflow not running"**
- Check if GitHub Actions is enabled
- Verify the cron schedule is correct
- Make sure the workflow file is in `.github/workflows/`

## 🎯 Advanced Features

### Data Analysis
Once you have data, you can:
- Calculate daily/monthly consumption
- Find peak usage hours
- Track efficiency improvements
- Set up alerts for unusual patterns

### Webhooks & Notifications
Add webhook notifications to get alerts:
```yaml
- name: Send notification
  run: |
    curl -X POST YOUR_WEBHOOK_URL \
    -H "Content-Type: application/json" \
    -d '{"text": "Energy logged: ${{ env.ENERGY_READING }} kWh"}'
```

### Data Visualization
Create charts using:
- GitHub's built-in CSV viewer
- Excel/Google Sheets charts
- Python matplotlib/plotly
- Web dashboards reading from GitHub

## 🔒 Security & Privacy

### Advantages
- **Private Repository**: Keep your data private
- **No Third Parties**: Data never leaves GitHub
- **Full Control**: You own and control everything
- **Audit Trail**: Full history of all changes

### Best Practices
- Use a private repository for sensitive data
- Regularly backup your repository
- Monitor GitHub Actions logs
- Keep your Tuya credentials secure

## 💡 Why This Beats Paid Solutions

| Feature | This Solution | Google Sheets | Cloud Services |
|---------|---------------|---------------|----------------|
| Cost | Free | Free (with limits) | $$$$ |
| Data Ownership | ✅ You own it | ❌ Google owns it | ❌ Vendor owns it |
| Privacy | ✅ Private | ❌ Google can access | ❌ Vendor can access |
| Backup | ✅ Automatic | ❌ Manual | ❌ Extra cost |
| Version Control | ✅ Full history | ❌ Limited | ❌ Usually none |
| API Access | ✅ Git/GitHub API | ❌ Limited | ❌ Vendor lock-in |
| Scalability | ✅ Unlimited | ❌ Row limits | ❌ Usage limits |

## 🚀 Next Steps

1. **Set it up** (5 minutes)
2. **Let it run** for a few days
3. **Download your data** and analyze it
4. **Customize** for your specific needs
5. **Share** your insights (optional)

Your energy data, your repository, your control! 🎉
