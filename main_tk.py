import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import ttkbootstrap as tb
from tkinter import ttk
from datetime import datetime, timedelta

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os
import json
import csv
from tkinter import filedialog

# plotting
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

APP_TITLE = "EcoTrack - Desktop (Tkinter)"
WEEKLY_GOAL_KG = 50

class EcoTrackApp(tb.Window):
    def __init__(self):
        super().__init__(themename='minty')
        self.title(APP_TITLE)
        self.geometry('900x600')
        self.configure(bg='#F0F7F4')

        self.selected_doc_id = None
        self.current_user = None
        self.api_key = None
        self.user_goal = WEEKLY_GOAL_KG
        self._load_firebase_config()

        self._build_ui()
        self.load_logs_async()
        self.load_leaderboard_async()

    def _build_ui(self):
        # ttkbootstrap Style applied by tb.Window with themename='minty'

        # Notebook for tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill='both', expand=True, padx=12, pady=12)

        self._build_dashboard()
        self._build_community()
        self._build_summary()
        self._build_profile()

    def _build_dashboard(self):
        frame = ttk.Frame(self.nb)
        frame.pack(fill='both', expand=True)
        self.nb.add(frame, text='Dashboard')

        # Top: Inputs
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill='x', padx=10, pady=8)

        ttk.Label(input_frame, text='Activity Type').grid(row=0, column=0, sticky='w')
        self.activity_type = ttk.Combobox(input_frame, values=['Transport','Meal','Energy'], state='readonly')
        self.activity_type.current(0)
        self.activity_type.grid(row=1, column=0, padx=6, pady=4)
        self.activity_type.bind('<<ComboboxSelected>>', self._on_type_change)

        ttk.Label(input_frame, text='Detail').grid(row=0, column=1, sticky='w')
        self.activity_detail = ttk.Combobox(input_frame, values=[], state='readonly', width=30)
        self.activity_detail.grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(input_frame, text='Amount').grid(row=0, column=2, sticky='w')
        self.amount_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.amount_var, width=12).grid(row=1, column=2, padx=6, pady=4)

        ttk.Label(input_frame, text='Description').grid(row=0, column=3, sticky='w')
        self.desc_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.desc_var, width=30).grid(row=1, column=3, padx=6, pady=4)

        self.add_btn = tb.Button(input_frame, text='Add Log', command=self.on_add_update, bootstyle='success')
        self.add_btn.grid(row=1, column=4, padx=8)
        tb.Button(input_frame, text='Export CSV', command=self.export_csv, bootstyle='info').grid(row=1, column=6, padx=8)

        # Auth controls
        auth_frame = ttk.Frame(input_frame)
        auth_frame.grid(row=0, column=5, rowspan=2, padx=10)
        ttk.Label(auth_frame, text='Email').grid(row=0, column=0, sticky='w')
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(auth_frame, textvariable=self.email_var, width=25)
        self.email_entry.grid(row=1, column=0, padx=4)
        ttk.Label(auth_frame, text='Password').grid(row=0, column=1, sticky='w')
        self.pw_var = tk.StringVar()
        self.pw_entry = ttk.Entry(auth_frame, textvariable=self.pw_var, show='*', width=18)
        self.pw_entry.grid(row=1, column=1, padx=4)
        self.signin_btn = tb.Button(auth_frame, text='Sign In', command=self.sign_in, bootstyle='primary')
        self.signin_btn.grid(row=1, column=2, padx=4)
        self.register_btn = tb.Button(auth_frame, text='Register', command=self.register, bootstyle='outline-primary')
        self.register_btn.grid(row=1, column=3, padx=4)
        self.signout_btn = tb.Button(auth_frame, text='Sign Out', command=self.sign_out, bootstyle='secondary')
        self.signout_btn.grid(row=1, column=4, padx=4)
        # start disabled until a user signs in
        try:
            self.signout_btn.config(state='disabled')
        except Exception:
            pass
        self.user_label = ttk.Label(auth_frame, text='Not signed in', foreground='gray')
        self.user_label.grid(row=2, column=0, columnspan=4, pady=4)

        # Middle: Progress
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill='x', padx=10, pady=6)
        self.total_label = ttk.Label(progress_frame, text='Total CO2 This Week: 0 kg', font=('Segoe UI', 10, 'bold'))
        self.total_label.pack(side='left')
        self.progress = tb.Progressbar(progress_frame, length=300, bootstyle='success')
        self.progress.pack(side='right', padx=12)
        # user goal display and set
        self.goal_label = ttk.Label(progress_frame, text=f'Goal: {self.user_goal} kg')
        self.goal_label.pack(side='left', padx=12)
        tb.Button(progress_frame, text='Set Goal', command=self.set_goal_dialog, bootstyle='outline-secondary').pack(side='left')

        # Bottom: Logs tree
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=6)

        # include hidden 'uid' column to track owner of each log
        cols = ('detail','amount','impact','description','time','uid')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
        for c in cols:
            if c == 'uid':
                # keep heading blank for hidden uid column
                self.tree.heading(c, text='')
            else:
                self.tree.heading(c, text=c.capitalize())
        self.tree.column('detail', width=180)
        self.tree.column('amount', width=80)
        self.tree.column('impact', width=100)
        self.tree.column('description', width=260)
        self.tree.column('time', width=120)
        # hide the uid column from view
        self.tree.column('uid', width=0, stretch=False)
        self.tree.pack(fill='both', expand=True, side='left')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        btns = ttk.Frame(tree_frame)
        btns.pack(fill='y', side='right', padx=6)
        # keep references so we can enable/disable based on ownership
        self.edit_btn = tb.Button(btns, text='Edit', command=self.on_edit, bootstyle='warning')
        self.edit_btn.pack(fill='x', pady=4)
        self.delete_btn = tb.Button(btns, text='Delete', command=self.on_delete, bootstyle='danger')
        self.delete_btn.pack(fill='x', pady=4)
        try:
            self.edit_btn.config(state='disabled')
            self.delete_btn.config(state='disabled')
        except Exception:
            pass

        self._on_type_change()

    def _build_community(self):
        frame = ttk.Frame(self.nb)
        frame.pack(fill='both', expand=True)
        self.nb.add(frame, text='Community')

        top = ttk.Frame(frame)
        top.pack(fill='x', padx=10, pady=8)
        self.community_total = ttk.Label(top, text='🌍 Total Community Impact: 0 kg', font=('Segoe UI', 11, 'bold'))
        self.community_total.pack(side='left')
        # search and sort controls
        ctrl = ttk.Frame(top)
        ctrl.pack(side='right')
        ttk.Label(ctrl, text='Search:').pack(side='left', padx=(0,4))
        self.leaderboard_search_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.leaderboard_search_var, width=20).pack(side='left')
        tb.Button(ctrl, text='Search', command=self.load_leaderboard_async, bootstyle='outline-primary').pack(side='left', padx=4)
        tb.Button(ctrl, text='Clear', command=self._clear_leaderboard_search, bootstyle='outline-secondary').pack(side='left', padx=4)
        ttk.Label(ctrl, text='Sort:').pack(side='left', padx=(8,4))
        self.leaderboard_sort_var = tk.StringVar(value='Total')
        self.leaderboard_sort = ttk.Combobox(ctrl, values=['Total','Name'], textvariable=self.leaderboard_sort_var, state='readonly', width=8)
        self.leaderboard_sort.pack(side='left')
        tb.Button(top, text='Refresh', command=self.load_leaderboard_async, bootstyle='primary').pack(side='right')

        self.leaderboard = ttk.Treeview(frame, columns=('user','kg'), show='headings')
        self.leaderboard.heading('user', text='User')
        self.leaderboard.heading('kg', text='kg CO2')
        self.leaderboard.column('user', width=200)
        self.leaderboard.column('kg', width=120)
        self.leaderboard.pack(fill='both', expand=True, padx=10, pady=6)

    def _clear_leaderboard_search(self):
        try:
            self.leaderboard_search_var.set('')
        except Exception:
            pass
        self.load_leaderboard_async()

    def _build_summary(self):
        frame = ttk.Frame(self.nb)
        frame.pack(fill='both', expand=True)
        self.nb.add(frame, text='Summary')

        top = ttk.Frame(frame)
        top.pack(fill='x', padx=10, pady=8)
        ttk.Label(top, text='Monthly CO2 (last 12 months)', font=('Segoe UI', 11, 'bold')).pack(side='left')
        tb.Button(top, text='Refresh', command=self.load_summary_async, bootstyle='primary').pack(side='right')

        self.summary_canvas_frame = ttk.Frame(frame)
        self.summary_canvas_frame.pack(fill='both', expand=True, padx=10, pady=6)

    def load_summary_async(self):
        threading.Thread(target=self.load_summary, daemon=True).start()

    def load_summary(self):
        # aggregate last 12 months by year-month
        now = datetime.now()
        start = (now.replace(day=1) - timedelta(days=365)).replace(day=1)
        docs = db.collection('logs').where('timestamp', '>=', start).stream()
        totals = {}
        for doc in docs:
            d = doc.to_dict()
            ts = d.get('timestamp')
            if not ts:
                continue
            if hasattr(ts, 'astimezone'):
                dt = ts.astimezone()
            else:
                dt = ts
            ym = dt.strftime('%Y-%m')
            totals[ym] = totals.get(ym, 0) + abs(d.get('co2_impact', 0))

        # build ordered last 12 months labels
        labels = []
        values = []
        for i in range(11, -1, -1):
            m = (now.replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m')
            labels.append(m)
            values.append(round(totals.get(m, 0), 2))

        # draw chart
        fig = Figure(figsize=(6,3), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(labels, values, color='#2b8cbe')
        ax.set_ylabel('kg CO2')
        ax.set_xticklabels(labels, rotation=45, ha='right')
        fig.tight_layout()

        # clear previous
        for child in self.summary_canvas_frame.winfo_children():
            child.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.summary_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _build_profile(self):
        frame = ttk.Frame(self.nb)
        frame.pack(fill='both', expand=True)
        self.nb.add(frame, text='Profile')

        container = ttk.Frame(frame)
        container.pack(fill='both', expand=True, padx=12, pady=12)

        ttk.Label(container, text='Display Name').grid(row=0, column=0, sticky='w')
        self.display_name_var = tk.StringVar()
        self.display_name_entry = ttk.Entry(container, textvariable=self.display_name_var, width=30)
        self.display_name_entry.grid(row=1, column=0, padx=6, pady=4)

        ttk.Label(container, text='Location').grid(row=0, column=1, sticky='w')
        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(container, textvariable=self.location_var, width=30)
        self.location_entry.grid(row=1, column=1, padx=6, pady=4)

        tb.Button(container, text='Save Profile', command=self.save_profile, bootstyle='primary').grid(row=1, column=2, padx=8)

        # start disabled until signed in
        try:
            self.display_name_entry.config(state='disabled')
            self.location_entry.config(state='disabled')
        except Exception:
            pass


    def _on_type_change(self, e=None):
        t = self.activity_type.get()
        if t == 'Transport':
            opts = ['Car (per mile)','Bus (per mile)','Train (per mile)','Bike (per mile)','Walk (per mile)','Electric Vehicle (per mile)']
        elif t == 'Meal':
            opts = ['Beef Meal','Chicken Meal','Vegetarian Meal','Vegan Meal']
        else:
            opts = ['Electricity (per kWh)','Natural Gas (per therm)']
        self.activity_detail['values'] = opts
        if opts:
            self.activity_detail.current(0)

    def on_add_update(self):
        # add or update depending on selected_doc_id
        if self.selected_doc_id:
            self._update_log()
        else:
            self._add_log()

    def _add_log(self):
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror('Error','Enter valid amount')
            return
        detail = self.activity_detail.get()
        impact = self._calc(detail, amount)
        data = {
            'activity_type': self.activity_type.get(),
            'activity_detail': detail,
            'amount': amount,
            'description': self.desc_var.get() or '',
            'co2_impact': impact,
            'timestamp': datetime.now(),
            'user_id': (self.current_user.get('uid') if self.current_user else 'default_user')
        }
        db.collection('logs').add(data)
        self._clear_inputs()
        self.load_logs_async()
        self.load_leaderboard_async()

    def _update_log(self):
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror('Error','Enter valid amount')
            return
        detail = self.activity_detail.get()
        impact = self._calc(detail, amount)
        data = {
            'activity_type': self.activity_type.get(),
            'activity_detail': detail,
            'amount': amount,
            'description': self.desc_var.get() or '',
            'co2_impact': impact,
        }
        db.collection('logs').document(self.selected_doc_id).update(data)
        self.selected_doc_id = None
        self.add_btn.config(text='Add Log')
        self._clear_inputs()
        self.load_logs_async()
        self.load_leaderboard_async()

    def on_tree_select(self, e):
        sel = self.tree.selection()
        if not sel:
            try:
                self.edit_btn.config(state='disabled')
                self.delete_btn.config(state='disabled')
            except Exception:
                pass
            return
        item_id = sel[0]
        item = self.tree.item(item_id)
        vals = item.get('values', [])
        uid = None
        if vals and len(vals) >= 6:
            uid = vals[5]
        can_modify = self.current_user and uid and uid == self.current_user.get('uid')
        try:
            self.edit_btn.config(state='normal' if can_modify else 'disabled')
            self.delete_btn.config(state='normal' if can_modify else 'disabled')
        except Exception:
            pass

    def on_edit(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        doc_id = sel[0]
        self.selected_doc_id = doc_id
        # values: detail, amount, impact, description, time
        vals = item['values']
        self.activity_detail.set(vals[0])
        self.amount_var.set(vals[1])
        self.desc_var.set(vals[3])
        self.add_btn.config(text='Update Log')

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        doc_id = sel[0]
        if messagebox.askyesno('Confirm','Delete selected log?'):
            db.collection('logs').document(doc_id).delete()
            self.load_logs_async()
            self.load_leaderboard_async()

    def _clear_inputs(self):
        self.amount_var.set('')
        self.desc_var.set('')

    def _calc(self, detail, amount):
        EM = {
            'Car (per mile)':0.404,'Bus (per mile)':0.089,'Train (per mile)':0.041,
            'Bike (per mile)':0.0,'Walk (per mile)':0.0,'Electric Vehicle (per mile)':0.15,
            'Beef Meal':6.61,'Chicken Meal':2.33,'Vegetarian Meal':1.0,'Vegan Meal':0.68,
            'Electricity (per kWh)':0.92,'Natural Gas (per therm)':5.3
        }
        return round(EM.get(detail,0)*amount,2)

    def load_logs_async(self):
        threading.Thread(target=self.load_logs, daemon=True).start()

    def load_logs(self):
        # fetch latest logs and populate treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
        docs = db.collection('logs').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(200).stream()
        for doc in docs:
            d = doc.to_dict()
            timestamp = d.get('timestamp')
            t = timestamp.strftime('%b %d %H:%M') if hasattr(timestamp,'strftime') else ''
            # include owner uid as hidden last column
            values = (d.get('activity_detail'), d.get('amount'), d.get('co2_impact'), d.get('description'), t, d.get('user_id','default_user'))
            # use document id as item id
            self.tree.insert('', 'end', iid=doc.id, values=values)
        self.update_weekly_progress()

    def load_user_profile_async(self):
        threading.Thread(target=self.load_user_profile, daemon=True).start()

    def load_user_profile(self):
        # fetch user doc with personal settings (like weekly goal)
        if not self.current_user:
            return
        try:
            uid = self.current_user.get('uid')
            doc = db.collection('users').document(uid).get()
            if doc.exists:
                d = doc.to_dict()
                goal = d.get('weekly_goal_kg')
                if goal:
                    self.user_goal = goal
                # profile fields
                name = d.get('display_name')
                loc = d.get('location')
                try:
                    if name:
                        self.display_name_var.set(name)
                    if loc:
                        self.location_var.set(loc)
                except Exception:
                    pass
            # update UI on main thread
            try:
                self.goal_label.config(text=f'Goal: {self.user_goal} kg')
            except Exception:
                pass
            # enable profile fields when loaded
            try:
                self.display_name_entry.config(state='normal')
                self.location_entry.config(state='normal')
            except Exception:
                pass
        except Exception:
            pass

    def set_goal_dialog(self):
        if not self.current_user:
            messagebox.showinfo('Set Goal','Sign in to set a personal goal')
            return
        val = simpledialog.askfloat('Set Weekly Goal','Enter weekly CO2 goal (kg):', minvalue=1, initialvalue=self.user_goal)
        if val is None:
            return
        try:
            uid = self.current_user.get('uid')
            db.collection('users').document(uid).set({'weekly_goal_kg': float(val)}, merge=True)
            self.user_goal = float(val)
            self.goal_label.config(text=f'Goal: {self.user_goal} kg')
            self.update_weekly_progress()
            messagebox.showinfo('Goal Saved', f'Weekly goal set to {self.user_goal} kg')
        except Exception as ex:
            messagebox.showerror('Error', str(ex))

    def save_profile(self):
        if not self.current_user:
            messagebox.showinfo('Profile','Sign in to save your profile')
            return
        try:
            uid = self.current_user.get('uid')
            payload = {
                'display_name': self.display_name_var.get() or None,
                'location': self.location_var.get() or None,
            }
            db.collection('users').document(uid).set(payload, merge=True)
            messagebox.showinfo('Profile', 'Profile saved')
        except Exception as ex:
            messagebox.showerror('Profile', str(ex))

    def export_csv(self):
        # fetch logs and write CSV
        docs = db.collection('logs').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        rows = []
        user_cache = {}
        for doc in docs:
            d = doc.to_dict()
            ts = d.get('timestamp')
            t = ts.strftime('%Y-%m-%d %H:%M:%S') if hasattr(ts, 'strftime') else ''
            uid = d.get('user_id','')
            display_name = ''
            if uid:
                if uid in user_cache:
                    display_name = user_cache[uid]
                else:
                    try:
                        udoc = db.collection('users').document(uid).get()
                        if udoc.exists:
                            udata = udoc.to_dict()
                            display_name = udata.get('display_name') or ''
                    except Exception:
                        display_name = ''
                    user_cache[uid] = display_name
            rows.append({
                'id': doc.id,
                'activity_type': d.get('activity_type'),
                'activity_detail': d.get('activity_detail'),
                'amount': d.get('amount'),
                'co2_impact': d.get('co2_impact'),
                'description': d.get('description'),
                'timestamp': t,
                'user_id': uid,
                'display_name': display_name,
            })

        if not rows:
            messagebox.showinfo('Export CSV', 'No logs to export')
            return

        fpath = filedialog.asksaveasfilename(title='Save CSV', defaultextension='.csv', filetypes=[('CSV files','*.csv')])
        if not fpath:
            return
        try:
            with open(fpath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo('Export CSV', f'Exported {len(rows)} rows to {fpath}')
        except Exception as ex:
            messagebox.showerror('Export CSV', str(ex))

    def update_weekly_progress(self):
        week_ago = datetime.now() - timedelta(days=7)
        docs = db.collection('logs').where('timestamp','>=',week_ago).stream()
        total = 0
        for doc in docs:
            d = doc.to_dict()
            total += abs(d.get('co2_impact',0))
        self.total_label.config(text=f'Total CO2 This Week: {round(total,2)} kg')
        goal = getattr(self, 'user_goal', WEEKLY_GOAL_KG) or WEEKLY_GOAL_KG
        try:
            pct = min(total/goal*100, 100)
        except Exception:
            pct = 0
        self.progress['value'] = pct

    def load_leaderboard_async(self):
        threading.Thread(target=self.load_leaderboard, daemon=True).start()

    def load_leaderboard(self):
        for i in self.leaderboard.get_children():
            self.leaderboard.delete(i)
        all_docs = db.collection('logs').stream()
        totals = {}
        total_community = 0
        for doc in all_docs:
            d = doc.to_dict()
            uid = d.get('user_id','Unknown')
            kg = abs(d.get('co2_impact',0))
            totals[uid] = totals.get(uid,0)+kg
            total_community += kg
        # Resolve display names where available (users collection), with caching
        label_map = {}
        user_cache = {}
        for uid in totals.keys():
            if uid == 'default_user':
                label_map[uid] = 'Anonymous'
                continue
            if self.current_user and uid == self.current_user.get('uid'):
                label_map[uid] = f"You ({self.current_user.get('email')})"
                continue
            # try cache first
            if uid in user_cache:
                name = user_cache.get(uid)
                label_map[uid] = name or uid
                continue
            try:
                doc = db.collection('users').document(uid).get()
                if doc.exists:
                    d = doc.to_dict()
                    name = d.get('display_name')
                    user_cache[uid] = name
                    if name:
                        label_map[uid] = name
                        continue
            except Exception:
                pass
            label_map[uid] = uid

        self.community_total.config(text=f'🌍 Total Community Impact: {round(total_community,2)} kg')

        # Apply search filter (by display name or uid)
        search_term = ''
        try:
            search_term = (self.leaderboard_search_var.get() or '').strip().lower()
        except Exception:
            search_term = ''

        rows = []
        for uid, kg in totals.items():
            display_name = label_map.get(uid, uid)
            rows.append((uid, display_name, kg))

        # apply search
        if search_term:
            rows = [r for r in rows if search_term in (r[1] or '').lower() or search_term in (r[0] or '').lower()]

        # sort
        sort_by = 'Total'
        try:
            sort_by = (self.leaderboard_sort_var.get() or 'Total')
        except Exception:
            sort_by = 'Total'
        if sort_by == 'Name':
            rows.sort(key=lambda x: (x[1] or '').lower())
        else:
            rows.sort(key=lambda x: x[2], reverse=True)

        for uid, display_name, kg in rows[:50]:
            self.leaderboard.insert('', 'end', values=(display_name, round(kg, 2)))

    # --- Authentication helpers ---
    def _load_firebase_config(self):
        cfg_path = os.path.join(os.path.dirname(__file__), 'firebase_config.json')
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.api_key = cfg.get('apiKey')
            except Exception:
                self.api_key = None
        else:
            self.api_key = os.environ.get('FIREBASE_API_KEY')

    def register(self):
        if not self.api_key:
            messagebox.showwarning('Missing API Key','Add firebase_config.json with apiKey or set FIREBASE_API_KEY env var')
            return
        email = self.email_var.get()
        pw = self.pw_var.get()
        if not email or not pw:
            messagebox.showerror('Error','Email and password required')
            return
        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}'
        payload = {'email': email, 'password': pw, 'returnSecureToken': True}
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            data = r.json()
            self.current_user = {'uid': data['localId'], 'email': email, 'idToken': data['idToken']}
            self.user_label.config(text=f"Signed in: {email}")
            try:
                self.signout_btn.config(state='normal')
            except Exception:
                pass
            self.load_leaderboard_async()
            self.load_logs_async()
        else:
            messagebox.showerror('Register failed', r.text)

    def sign_in(self):
        if not self.api_key:
            messagebox.showwarning('Missing API Key','Add firebase_config.json with apiKey or set FIREBASE_API_KEY env var')
            return
        email = self.email_var.get()
        pw = self.pw_var.get()
        if not email or not pw:
            messagebox.showerror('Error','Email and password required')
            return
        url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}'
        payload = {'email': email, 'password': pw, 'returnSecureToken': True}
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            data = r.json()
            self.current_user = {'uid': data['localId'], 'email': email, 'idToken': data['idToken']}
            self.user_label.config(text=f"Signed in: {email}")
            try:
                self.signout_btn.config(state='normal')
                self.signin_btn.config(state='disabled')
                self.register_btn.config(state='disabled')
                self.email_entry.config(state='disabled')
                self.pw_entry.config(state='disabled')
                # enable profile inputs (will be filled by load_user_profile)
                try:
                    self.display_name_entry.config(state='normal')
                    self.location_entry.config(state='normal')
                except Exception:
                    pass
            except Exception:
                pass
            # load user profile (goal etc.)
            self.load_user_profile_async()
            self.load_leaderboard_async()
            self.load_logs_async()
        else:
            messagebox.showerror('Sign-in failed', r.text)

    def sign_out(self):
        self.current_user = None
        self.user_label.config(text='Not signed in')
        try:
            self.signout_btn.config(state='disabled')
        except Exception:
            pass
        try:
            self.signin_btn.config(state='normal')
            self.register_btn.config(state='normal')
            self.email_entry.config(state='normal')
            self.pw_entry.config(state='normal')
        except Exception:
            pass
        # reset to default goal on sign out
        self.user_goal = WEEKLY_GOAL_KG
        try:
            self.goal_label.config(text=f'Goal: {self.user_goal} kg')
        except Exception:
            pass
        # clear profile fields and disable
        try:
            self.display_name_var.set('')
            self.location_var.set('')
            self.display_name_entry.config(state='disabled')
            self.location_entry.config(state='disabled')
        except Exception:
            pass
        self.load_leaderboard_async()

if __name__ == '__main__':
    app = EcoTrackApp()
    app.mainloop()
