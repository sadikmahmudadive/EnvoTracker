import flet as ft
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Carbon footprint reference data (kg CO2)
ACTIVITY_EMISSIONS = {
    "Car (per mile)": 0.404,
    "Bus (per mile)": 0.089,
    "Train (per mile)": 0.041,
    "Bike (per mile)": 0.0,
    "Walk (per mile)": 0.0,
    "Electric Vehicle (per mile)": 0.15,
    "Beef Meal": 6.61,
    "Chicken Meal": 2.33,
    "Vegetarian Meal": 1.0,
    "Vegan Meal": 0.68,
    "Electricity (per kWh)": 0.92,
    "Natural Gas (per therm)": 5.3,
}

def main(page: ft.Page):
    page.title = "🌍 EcoTrack - Carbon Footprint Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = "#F0F7F4"
    
    # State variable
    editing_doc_id = [None]
    
    # Activity type dropdown
    activity_type = ft.Dropdown(
        label="Activity Type",
        options=[
            ft.dropdown.Option("Transport"),
            ft.dropdown.Option("Meal"),
            ft.dropdown.Option("Energy"),
        ],
        value="Transport",
        width=200,
    )
    
    activity_detail = ft.Dropdown(label="Detail", width=250)
    
    def update_activity_detail(e):
        if activity_type.value == "Transport":
            activity_detail.options = [
                ft.dropdown.Option("Car (per mile)"),
                ft.dropdown.Option("Bus (per mile)"),
                ft.dropdown.Option("Train (per mile)"),
                ft.dropdown.Option("Bike (per mile)"),
                ft.dropdown.Option("Walk (per mile)"),
                ft.dropdown.Option("Electric Vehicle (per mile)"),
            ]
        elif activity_type.value == "Meal":
            activity_detail.options = [
                ft.dropdown.Option("Beef Meal"),
                ft.dropdown.Option("Chicken Meal"),
                ft.dropdown.Option("Vegetarian Meal"),
                ft.dropdown.Option("Vegan Meal"),
            ]
        elif activity_type.value == "Energy":
            activity_detail.options = [
                ft.dropdown.Option("Electricity (per kWh)"),
                ft.dropdown.Option("Natural Gas (per therm)"),
            ]
        activity_detail.value = activity_detail.options[0].key if activity_detail.options else None
        page.update()
    
    activity_type.on_change = update_activity_detail
    
    amount_input = ft.TextField(
        label="Amount (miles/units)",
        width=150,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    
    description_input = ft.TextField(
        label="Description (optional)",
        width=300,
    )
    
    log_list = ft.Column(spacing=10)
    log_scroll = ft.Container(content=log_list, height=400)
    
    weekly_progress = ft.ProgressBar(value=0, color="green", bgcolor="#C8E6C9", height=20)
    weekly_goal_text = ft.Text("", size=14, color="#2E7D32")
    total_saved_text = ft.Text("Total CO2 Saved This Week: 0 kg", size=18, weight="bold", color="#1B5E20")
    
    def calculate_co2_impact(activity, amount):
        emission_rate = ACTIVITY_EMISSIONS.get(activity, 0)
        return round(emission_rate * amount, 2)

    def show_snackbar(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()

    def add_log(e):
        if activity_detail.value and amount_input.value:
            try:
                amount = float(amount_input.value)
                co2_impact = calculate_co2_impact(activity_detail.value, amount)
                
                data = {
                    "activity_type": activity_type.value,
                    "activity_detail": activity_detail.value,
                    "amount": amount,
                    "description": description_input.value or "",
                    "co2_impact": co2_impact,
                    "timestamp": datetime.now(),
                    "user_id": "default_user"
                }
                db.collection("logs").add(data)
                
                amount_input.value = ""
                description_input.value = ""
                load_logs()
                update_weekly_progress()
                show_snackbar("✅ Log added successfully!")
                page.update()
            except ValueError:
                show_snackbar("❌ Please enter a valid number")

    def update_log(e):
        if editing_doc_id[0] and activity_detail.value and amount_input.value:
            try:
                amount = float(amount_input.value)
                co2_impact = calculate_co2_impact(activity_detail.value, amount)
                
                data = {
                    "activity_type": activity_type.value,
                    "activity_detail": activity_detail.value,
                    "amount": amount,
                    "description": description_input.value or "",
                    "co2_impact": co2_impact,
                }
                db.collection("logs").document(editing_doc_id[0]).update(data)
                
                editing_doc_id[0] = None
                amount_input.value = ""
                description_input.value = ""
                add_btn.text = "Add Log"
                add_btn.on_click = add_log
                
                load_logs()
                update_weekly_progress()
                show_snackbar("✅ Log updated!")
                page.update()
            except ValueError:
                show_snackbar("❌ Please enter a valid number")

    def edit_log(doc_id, log_data):
        editing_doc_id[0] = doc_id
        activity_type.value = log_data['activity_type']
        update_activity_detail(None)
        activity_detail.value = log_data['activity_detail']
        amount_input.value = str(log_data['amount'])
        description_input.value = log_data.get('description', '')
        add_btn.text = "Update Log"
        add_btn.on_click = update_log
        page.update()

    def load_logs():
        log_list.controls.clear()
        docs = db.collection("logs").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
        
        for doc in docs:
            log_data = doc.to_dict()
            doc_id = doc.id
            
            timestamp = log_data['timestamp']
            time_str = timestamp.strftime("%b %d, %I:%M %p") if hasattr(timestamp, 'strftime') else "Recent"
            
            icon_map = {"Transport": "🚗", "Meal": "🍽️", "Energy": "⚡"}
            icon = icon_map.get(log_data.get('activity_type', ''), "🌿")
            
            description = log_data.get('description', '')
            subtitle = f"{log_data['amount']} units • {log_data['co2_impact']} kg CO2"
            if description:
                subtitle = f"{description} • {subtitle}"
            
            log_card = ft.Container(
                content=ft.Row([
                    ft.Text(icon, size=32),
                    ft.Column([
                        ft.Text(log_data['activity_detail'], weight="w500"),
                        ft.Text(subtitle, size=12, color="grey"),
                    ], expand=True),
                    ft.Column([
                        ft.Text(time_str, size=11, color="grey"),
                        ft.Row([
                            ft.TextButton("✏️ Edit", on_click=lambda e, id=doc_id, data=log_data: edit_log(id, data)),
                            ft.TextButton("🗑️ Delete", on_click=lambda e, id=doc_id: delete_log(id)),
                        ]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.END),
                ]),
                padding=15,
                bgcolor="white",
                border_radius=8,
            )
            log_list.controls.append(log_card)
        page.update()

    def delete_log(doc_id):
        db.collection("logs").document(doc_id).delete()
        load_logs()
        update_weekly_progress()
        show_snackbar("🗑️ Log deleted")
        page.update()
    
    def update_weekly_progress():
        week_ago = datetime.now() - timedelta(days=7)
        docs = db.collection("logs").where("timestamp", ">=", week_ago).stream()
        
        total_saved = 0
        for doc in docs:
            log_data = doc.to_dict()
            total_saved += abs(log_data.get('co2_impact', 0))
        
        weekly_goal = 50
        progress = min(total_saved / weekly_goal, 1.0) if weekly_goal > 0 else 0
        
        weekly_progress.value = progress
        total_saved_text.value = f"Total CO2 Impact This Week: {round(total_saved, 2)} kg"
        weekly_goal_text.value = f"Weekly Goal: {round(total_saved, 2)} / {weekly_goal} kg ({round(progress * 100)}%)"
        page.update()
    
    leaderboard_list = ft.Column(spacing=10)
    leaderboard_scroll = ft.Container(content=leaderboard_list, height=400)
    community_total_text = ft.Text("", size=24, weight="bold", color="#1B5E20")
    
    def load_leaderboard(e=None):
        leaderboard_list.controls.clear()
        
        all_docs = db.collection("logs").stream()
        total_community_impact = 0
        user_totals = {}
        
        for doc in all_docs:
            log_data = doc.to_dict()
            impact = abs(log_data.get('co2_impact', 0))
            total_community_impact += impact
            user_id = log_data.get('user_id', 'Unknown')
            user_totals[user_id] = user_totals.get(user_id, 0) + impact
        
        community_total_text.value = f"🌍 Total Community Impact: {round(total_community_impact, 2)} kg CO2"
        
        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)
        
        for i, (user_id, total) in enumerate(sorted_users[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            leaderboard_item = ft.Container(
                content=ft.Row([
                    ft.Text(medal, size=24),
                    ft.Text(f"User: {user_id}", weight="w500", expand=True),
                    ft.Text(f"{round(total, 2)} kg", size=16, weight="bold", color="green"),
                ]),
                padding=15,
                bgcolor="white",
                border_radius=8,
            )
            leaderboard_list.controls.append(leaderboard_item)
        
        if not sorted_users:
            leaderboard_list.controls.append(
                ft.Text("No community data yet. Be the first to log!", size=14, color="grey")
            )
        
        page.update()
    
    add_btn = ft.Button("Add Log", on_click=add_log, width=150, height=50, bgcolor="#4CAF50", color="white")
    update_activity_detail(None)
    
    dashboard_view = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text("🌿 EcoTrack", size=36, weight="bold", color="#2E7D32"),
                ft.Text("Track your carbon footprint & make a difference", size=14, color="grey"),
            ]),
            padding=20,
        ),
        ft.Divider(height=1, color="#C8E6C9"),
        ft.Container(
            content=ft.Column([
                total_saved_text,
                weekly_progress,
                weekly_goal_text,
            ], spacing=10),
            padding=20,
            bgcolor="#E8F5E9",
            border_radius=10,
            margin=10,
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Log New Activity", size=18, weight="w500", color="#2E7D32"),
                ft.Row([activity_type, activity_detail], wrap=True),
                ft.Row([amount_input, description_input], wrap=True),
                add_btn,
            ], spacing=10),
            padding=20,
            bgcolor="white",
            border_radius=10,
            margin=10,
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("📜 Recent Logs", size=18, weight="w500", color="#2E7D32"),
                log_scroll,
            ]),
            padding=20,
            bgcolor="white",
            border_radius=10,
            margin=10,
        ),
    ], scroll=ft.ScrollMode.AUTO, expand=True)
    
    leaderboard_view = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text("🏆 Community Leaderboard", size=32, weight="bold", color="#2E7D32"),
                ft.Text("See how you compare with other eco-warriors!", size=14, color="grey"),
                community_total_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30,
        ),
        ft.Button("🔄 Refresh", on_click=load_leaderboard, width=150, bgcolor="#4CAF50", color="white"),
        ft.Divider(height=1, color="#C8E6C9"),
        leaderboard_scroll,
    ], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    # Simple tab bar (manual view switching to avoid Tab API differences)
    main_body = ft.Container(content=dashboard_view, expand=True)

    def show_dashboard(e=None):
        main_body.content = dashboard_view
        dashboard_btn.bgcolor = "#4CAF50"
        dashboard_btn.color = "white"
        community_btn.bgcolor = None
        community_btn.color = "black"
        page.update()

    def show_community(e=None):
        main_body.content = leaderboard_view
        community_btn.bgcolor = "#4CAF50"
        community_btn.color = "white"
        dashboard_btn.bgcolor = None
        dashboard_btn.color = "black"
        page.update()

    dashboard_btn = ft.Button("📊 Dashboard", on_click=show_dashboard, bgcolor="#4CAF50", color="white")
    community_btn = ft.Button("🌍 Community", on_click=show_community)

    tabs_row = ft.Row([dashboard_btn, community_btn], spacing=10)

    page.add(tabs_row, ft.Divider(), main_body)
    
    load_logs()
    update_weekly_progress()
    load_leaderboard()

ft.run(main)
