# 🌿 EcoTrack - Personal Carbon Footprint Dashboard

A beautiful desktop application to track your daily carbon footprint and join a community of eco-conscious users!

## ✨ Features

### Complete CRUD Operations
- ✅ **Create**: Log daily activities (transport, meals, energy usage)
- ✅ **Read**: View all your historical logs in a clean, organized list
- ✅ **Update**: Edit any entry if you forgot details or made a mistake
- ✅ **Delete**: Remove incorrect or accidental logs

### Smart Carbon Tracking
- 🚗 **Transport**: Track car, bus, train, bike, walking, and EV usage
- 🍽️ **Meals**: Log beef, chicken, vegetarian, or vegan meals
- ⚡ **Energy**: Monitor electricity and natural gas consumption
- 📊 **Auto-calculation**: Automatic CO2 impact calculation based on scientific data

### Community Features
- 🏆 **Live Leaderboard**: See how you compare with other users
- 🌍 **Global Impact**: View total CO2 tracked by the entire community
- 🔄 **Real-time Updates**: Data syncs instantly via Firebase

### Beautiful UI
- 🌿 **Nature-inspired Theme**: Soft greens and calming colors
- 📈 **Progress Tracking**: Visual progress bars for weekly goals
- 📱 **Responsive Design**: Clean, modern interface with card-based layouts
- 🎨 **Color-coded Logs**: Quick visual feedback on impact levels

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- A Firebase account

### 2. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or use an existing one)
3. Go to Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON file as `serviceAccountKey.json` in the EcoTrack folder
6. Enable Firestore Database in your Firebase project

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

## 📖 How to Use

### Dashboard Tab
1. Select an activity type (Transport, Meal, or Energy)
2. Choose the specific activity detail from the dropdown
3. Enter the amount (miles, units, etc.)
4. Add an optional description
5. Click "Add Log" to save

### Editing Logs
- Click the ✏️ edit icon next to any log
- Modify the details in the form
- Click "Update Log" to save changes

### Community Tab
- View the leaderboard of top contributors
- See total community CO2 impact
- Click "Refresh" to update the data

## 🎯 Weekly Goals

The app tracks your weekly CO2 impact and shows progress toward a 50kg goal. Adjust this in the code if needed!

## 🔧 Customization

### Change Carbon Emission Values
Edit the `ACTIVITY_EMISSIONS` dictionary in `main.py`:

```python
ACTIVITY_EMISSIONS = {
    "Car (per mile)": 0.404,  # Modify these values
    "Bike (per mile)": 0.0,
    # Add more activities...
}
```

### Adjust Weekly Goal
Find this line in `main.py`:

```python
weekly_goal = 50  # Change to your desired goal
```

## 📊 Data Structure

### Log Entry Format
```python
{
    "activity_type": "Transport",
    "activity_detail": "Bike (per mile)",
    "amount": 10.0,
    "description": "Morning commute",
    "co2_impact": 0.0,
    "timestamp": datetime.now(),
    "user_id": "default_user"
}
```

## 🤝 Multi-User Support

To enable real multi-user functionality:
1. Implement user authentication
2. Replace `"default_user"` with actual user IDs
3. Add user profiles and avatars to the leaderboard

## 🐛 Troubleshooting

### Firebase Connection Issues
- Ensure `serviceAccountKey.json` is in the correct location
- Check that Firestore is enabled in Firebase Console
- Verify your internet connection

### Module Not Found
```bash
pip install --upgrade flet firebase-admin
```

## 📝 License

This project is open source and available for personal and educational use.

## 🌟 Future Enhancements

- [ ] Export data to CSV
- [ ] Monthly/yearly statistics
- [ ] Goal customization per user
- [ ] Push notifications for milestones
- [ ] Social sharing features
- [ ] Carbon offset recommendations

---

Made with 💚 for a greener planet!
