#!/usr/bin/env python3
"""
The Champ Timer - Tournament Edition GUI
Easy-to-use graphical interface for tracking races

Works on Mac and Windows
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import csv
import datetime
import threading
import time
from pathlib import Path

class TournamentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("The Champ Timer - Tournament Tracker")
        self.root.geometry("1000x700")
        
        # Data structures
        self.serial_port = None
        self.is_connected = False
        self.is_listening = False
        self.heat_number = 1
        self.competitors = {}
        self.current_heat_assignments = {}
        
        # File setup
        self.results_dir = Path("race_results")
        self.results_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.heats_file = self.results_dir / f"heats_{timestamp}.csv"
        self.standings_file = self.results_dir / f"standings_{timestamp}.csv"
        
        # Setup UI
        self.setup_ui()
        self.show_setup_tab()
        
    def setup_ui(self):
        """Create the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=50, pady=50)
        
        # Tab 1: Setup
        self.setup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.setup_frame, text="1. Setup")
        self.create_setup_tab()
        
        # Tab 2: Connection
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text="2. Connect Timer")
        self.create_connection_tab()
        
        # Tab 3: Racing
        self.racing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.racing_frame, text="3. Race")
        self.create_racing_tab()
        
        # Tab 4: Standings
        self.standings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.standings_frame, text="4. Standings")
        self.create_standings_tab()
        
        # Disable tabs until setup is complete
        self.notebook.tab(1, state='disabled')
        self.notebook.tab(2, state='disabled')
        self.notebook.tab(3, state='disabled')
        
    def create_setup_tab(self):
        """Setup tab - add competitors"""
        # Title
        title = tk.Label(self.setup_frame, text="Competitor Setup", 
                        font=('Arial', 20, 'bold'), fg='#2c3e50')
        title.pack(pady=20)
        
        # Instructions
        instructions = tk.Label(self.setup_frame, 
                               text="Add all competitors who will be racing today",
                               font=('Arial', 12))
        instructions.pack(pady=10)
        
        # Competitor entry frame
        entry_frame = ttk.Frame(self.setup_frame)
        entry_frame.pack(pady=20)
        
        tk.Label(entry_frame, text="Competitor Name:", font=('Arial', 11)).grid(row=0, column=0, padx=5)
        self.competitor_entry = ttk.Entry(entry_frame, width=30, font=('Arial', 11))
        self.competitor_entry.grid(row=0, column=1, padx=5)
        self.competitor_entry.bind('<Return>', lambda e: self.add_competitor())
        
        add_btn = tk.Button(entry_frame, text="Add Competitor", 
                           command=self.add_competitor,
                           bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                           padx=20, pady=5)
        add_btn.grid(row=0, column=2, padx=5)
        
        # Competitor list
        list_frame = ttk.LabelFrame(self.setup_frame, text="Competitors", padding=10)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrolled listbox
        self.competitor_listbox = tk.Listbox(list_frame, font=('Arial', 11), height=15)
        self.competitor_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.competitor_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.competitor_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        button_frame = ttk.Frame(self.setup_frame)
        button_frame.pack(pady=10)
        
        remove_btn = tk.Button(button_frame, text="Remove Selected", 
                              command=self.remove_competitor,
                              bg='#e74c3c', fg='white', font=('Arial', 10))
        remove_btn.pack(side='left', padx=5)
        
        done_btn = tk.Button(button_frame, text="Done - Connect Timer →", 
                            command=self.finish_setup,
                            bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                            padx=30, pady=10)
        done_btn.pack(side='left', padx=5)
        
    def create_connection_tab(self):
        """Connection tab - connect to timer"""
        # Title
        title = tk.Label(self.connection_frame, text="Connect to Timer", 
                        font=('Arial', 20, 'bold'), fg='#2c3e50')
        title.pack(pady=20)
        
        # Connection settings frame
        settings_frame = ttk.LabelFrame(self.connection_frame, text="Connection Settings", 
                                       padding=20)
        settings_frame.pack(pady=20, padx=20)
        
        # Port selection
        tk.Label(settings_frame, text="Serial Port:", font=('Arial', 11)).grid(row=0, column=0, sticky='w', pady=5)
        self.port_combo = ttk.Combobox(settings_frame, width=40, font=('Arial', 11), state='readonly')
        self.port_combo.grid(row=0, column=1, padx=10, pady=5)
        
        refresh_btn = tk.Button(settings_frame, text="Refresh Ports", 
                               command=self.refresh_ports,
                               bg='#95a5a6', fg='white', font=('Arial', 10))
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Baudrate
        tk.Label(settings_frame, text="Baud Rate:", font=('Arial', 11)).grid(row=1, column=0, sticky='w', pady=5)
        self.baudrate_combo = ttk.Combobox(settings_frame, width=15, font=('Arial', 11), 
                                          values=['9600', '19200', '38400', '115200'], state='readonly')
        self.baudrate_combo.set('9600')
        self.baudrate_combo.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        # Connect button
        self.connect_btn = tk.Button(self.connection_frame, text="Connect to Timer", 
                                     command=self.connect_timer,
                                     bg='#3498db', fg='white', font=('Arial', 14, 'bold'),
                                     padx=40, pady=15)
        self.connect_btn.pack(pady=20)
        
        # Status label
        self.connection_status = tk.Label(self.connection_frame, text="Not Connected", 
                                         font=('Arial', 12), fg='red')
        self.connection_status.pack(pady=10)
        
        # Next button (disabled until connected)
        self.next_to_race_btn = tk.Button(self.connection_frame, text="Next - Start Racing →", 
                                         command=self.go_to_racing,
                                         bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                         padx=30, pady=10, state='disabled')
        self.next_to_race_btn.pack(pady=20)
        
        # Auto-refresh ports
        self.refresh_ports()
        
    def create_racing_tab(self):
        """Racing tab - assign heats and race"""
        # Top frame - Heat info
        top_frame = ttk.Frame(self.racing_frame)
        top_frame.pack(fill='x', padx=20, pady=10)
        
        self.heat_label = tk.Label(top_frame, text="HEAT #1", 
                                   font=('Arial', 24, 'bold'), fg='#e74c3c')
        self.heat_label.pack()
        
        # Lane assignments frame
        lanes_frame = ttk.LabelFrame(self.racing_frame, text="Lane Assignments", padding=20)
        lanes_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.lane_combos = {}
        for lane in range(1, 5):
            lane_frame = ttk.Frame(lanes_frame)
            lane_frame.pack(fill='x', pady=8)
            
            tk.Label(lane_frame, text=f"Lane {lane}:", font=('Arial', 12, 'bold'), 
                    width=8).pack(side='left', padx=5)
            
            combo = ttk.Combobox(lane_frame, width=30, font=('Arial', 11), state='readonly')
            combo.pack(side='left', padx=5)
            self.lane_combos[lane] = combo
        
        # Auto-assign button
        auto_btn = tk.Button(self.racing_frame, text="Auto-Assign Next Racers", 
                           command=self.auto_assign_lanes,
                           bg='#9b59b6', fg='white', font=('Arial', 11))
        auto_btn.pack(pady=10)
        
        # Race button
        self.race_btn = tk.Button(self.racing_frame, text="🏁 READY TO RACE!", 
                                 command=self.start_listening,
                                 bg='#27ae60', fg='white', font=('Arial', 16, 'bold'),
                                 padx=50, pady=20)
        self.race_btn.pack(pady=20)
        
        # Results display
        results_frame = ttk.LabelFrame(self.racing_frame, text="Last Race Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, 
                                                      font=('Courier', 11), state='disabled')
        self.results_text.pack(fill='both', expand=True)
        
    def create_standings_tab(self):
        """Standings tab - show current rankings"""
        # Title
        title = tk.Label(self.standings_frame, text="🏆 Tournament Standings", 
                        font=('Arial', 20, 'bold'), fg='#2c3e50')
        title.pack(pady=20)
        
        # Standings table
        table_frame = ttk.Frame(self.standings_frame)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create treeview
        columns = ('Rank', 'Name', 'Best Time', 'Avg Time', 'Races')
        self.standings_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Column headings
        self.standings_tree.heading('Rank', text='Rank')
        self.standings_tree.heading('Name', text='Competitor')
        self.standings_tree.heading('Best Time', text='Best Time')
        self.standings_tree.heading('Avg Time', text='Average Time')
        self.standings_tree.heading('Races', text='Races')
        
        # Column widths
        self.standings_tree.column('Rank', width=80, anchor='center')
        self.standings_tree.column('Name', width=250)
        self.standings_tree.column('Best Time', width=150, anchor='center')
        self.standings_tree.column('Avg Time', width=150, anchor='center')
        self.standings_tree.column('Races', width=100, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', 
                                 command=self.standings_tree.yview)
        self.standings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.standings_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Refresh button
        refresh_btn = tk.Button(self.standings_frame, text="🔄 Refresh Standings", 
                               command=self.update_standings_display,
                               bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                               padx=30, pady=10)
        refresh_btn.pack(pady=20)
        
    # Setup Tab Methods
    def add_competitor(self):
        """Add a competitor to the list"""
        name = self.competitor_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Empty Name", "Please enter a competitor name.")
            return
        
        if name in self.competitors:
            messagebox.showwarning("Duplicate", f"{name} is already in the list.")
            return
        
        self.competitors[name] = {
            'heats': [],
            'best_time': None,
            'total_time': 0.0,
            'races_count': 0
        }
        
        self.competitor_listbox.insert(tk.END, name)
        self.competitor_entry.delete(0, tk.END)
        self.competitor_entry.focus()
        
    def remove_competitor(self):
        """Remove selected competitor"""
        selection = self.competitor_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a competitor to remove.")
            return
        
        idx = selection[0]
        name = self.competitor_listbox.get(idx)
        
        if messagebox.askyesno("Confirm", f"Remove {name} from the tournament?"):
            del self.competitors[name]
            self.competitor_listbox.delete(idx)
    
    def finish_setup(self):
        """Complete setup and move to connection"""
        if not self.competitors:
            messagebox.showwarning("No Competitors", 
                                 "Please add at least one competitor before continuing.")
            return
        
        count = len(self.competitors)
        if messagebox.askyesno("Confirm Setup", 
                              f"Ready to race with {count} competitors?"):
            self.notebook.tab(1, state='normal')
            self.show_connection_tab()
            
            # Initialize CSV
            with open(self.heats_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Heat #', 'Timestamp', 'Lane 1 Name', 'Lane 1 Time', 
                               'Lane 2 Name', 'Lane 2 Time', 'Lane 3 Name', 'Lane 3 Time',
                               'Lane 4 Name', 'Lane 4 Time', 'Heat Winner'])
    
    # Connection Tab Methods
    def refresh_ports(self):
        """Refresh available serial ports"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        
        if not port_list:
            port_list = ["No serial ports found"]
        
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
    
    def connect_timer(self):
        """Connect to the timer"""
        if self.is_connected:
            # Disconnect
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.is_connected = False
            self.connection_status.config(text="Not Connected", fg='red')
            self.connect_btn.config(text="Connect to Timer", bg='#3498db')
            self.next_to_race_btn.config(state='disabled')
            return
        
        port_selection = self.port_combo.get()
        if not port_selection or "No serial ports" in port_selection:
            messagebox.showerror("No Port", "Please select a valid serial port.")
            return
        
        port_name = port_selection.split(' - ')[0]
        baudrate = int(self.baudrate_combo.get())
        
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            self.is_connected = True
            self.connection_status.config(text=f"✓ Connected to {port_name}", fg='green')
            self.connect_btn.config(text="Disconnect", bg='#e74c3c')
            self.next_to_race_btn.config(state='normal')
            
            messagebox.showinfo("Connected", f"Successfully connected to {port_name}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect:\n{str(e)}")
    
    def go_to_racing(self):
        """Move to racing tab"""
        self.notebook.tab(2, state='normal')
        self.notebook.tab(3, state='normal')
        self.show_racing_tab()
        self.update_lane_options()
    
    # Racing Tab Methods
    def update_lane_options(self):
        """Update lane assignment dropdowns"""
        options = ['(empty)'] + sorted(self.competitors.keys())
        
        for combo in self.lane_combos.values():
            combo['values'] = options
            combo.set('(empty)')
    
    def auto_assign_lanes(self):
        """Automatically assign racers who have raced the least"""
        # Sort competitors by race count
        sorted_competitors = sorted(
            self.competitors.items(),
            key=lambda x: x[1]['races_count']
        )
        
        # Assign first 4
        for lane, (name, _) in zip(range(1, 5), sorted_competitors[:4]):
            self.lane_combos[lane].set(name)
    
    def start_listening(self):
        """Start listening for race data"""
        # Get assignments
        self.current_heat_assignments = {}
        for lane, combo in self.lane_combos.items():
            selection = combo.get()
            if selection and selection != '(empty)':
                self.current_heat_assignments[lane] = selection
        
        if not self.current_heat_assignments:
            messagebox.showwarning("No Assignments", 
                                 "Please assign at least one competitor to a lane.")
            return
        
        # Confirm
        assignment_text = "\n".join([f"Lane {lane}: {name}" 
                                    for lane, name in self.current_heat_assignments.items()])
        
        if not messagebox.askyesno("Ready to Race?", 
                                   f"Current assignments:\n\n{assignment_text}\n\nReady to race?"):
            return
        
        # Disable button and start listening
        self.race_btn.config(state='disabled', text="⏳ Waiting for race data...")
        self.is_listening = True
        
        # Start listening thread
        thread = threading.Thread(target=self.listen_for_race, daemon=True)
        thread.start()
    
    def listen_for_race(self):
        """Listen for race data in background thread"""
        buffer = ""
        
        try:
            while self.is_listening and self.is_connected:
                if self.serial_port.in_waiting > 0:
                    chunk = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk
                    
                    while '\n' in buffer or '\r' in buffer:
                        if '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                        else:
                            line, buffer = buffer.split('\r', 1)
                        
                        line = line.strip()
                        
                        if line:
                            times = self.parse_timer_data(line)
                            
                            if any(t is not None for t in times):
                                # Process race results
                                self.root.after(0, self.process_race_results, times)
                                self.is_listening = False
                                return
                
                time.sleep(0.01)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Listening Error", str(e)))
            self.is_listening = False
            self.root.after(0, lambda: self.race_btn.config(state='normal', text="🏁 READY TO RACE!"))
    
    def parse_timer_data(self, data_line):
        """Parse timer data"""
        times = [None, None, None, None]
        
        try:
            import re
            time_pattern = r'(\d+\.?\d{4})'
            matches = re.findall(time_pattern, data_line)
            
            for i, match in enumerate(matches[:4]):
                times[i] = float(match)
            
        except Exception:
            pass
        
        return times
    
    def process_race_results(self, times):
        """Process and display race results"""
        # Find winner
        winner_lane = None
        winner_time = None
        valid_times = [(i+1, t) for i, t in enumerate(times) if t is not None]
        
        if valid_times:
            winner_lane, winner_time = min(valid_times, key=lambda x: x[1])
        
        # Display results
        results = f"\n{'='*60}\n"
        results += f"HEAT #{self.heat_number} RESULTS - {datetime.datetime.now().strftime('%H:%M:%S')}\n"
        results += f"{'='*60}\n\n"
        
        for lane in range(1, 5):
            competitor = self.current_heat_assignments.get(lane, "---")
            time_val = times[lane-1]
            
            if time_val is not None:
                winner_mark = " 🏆 HEAT WINNER!" if lane == winner_lane else ""
                results += f"Lane {lane} - {competitor:20s}: {time_val:.4f}s{winner_mark}\n"
            else:
                results += f"Lane {lane} - {competitor:20s}: ---\n"
        
        results += f"\n{'='*60}\n"
        
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', results)
        self.results_text.config(state='disabled')
        
        # Update stats
        for lane in range(1, 5):
            if lane in self.current_heat_assignments and times[lane-1] is not None:
                competitor = self.current_heat_assignments[lane]
                time_val = times[lane-1]
                
                self.competitors[competitor]['heats'].append({
                    'heat': self.heat_number,
                    'lane': lane,
                    'time': time_val
                })
                self.competitors[competitor]['races_count'] += 1
                self.competitors[competitor]['total_time'] += time_val
                
                if (self.competitors[competitor]['best_time'] is None or 
                    time_val < self.competitors[competitor]['best_time']):
                    self.competitors[competitor]['best_time'] = time_val
        
        # Save to CSV
        self.save_heat_results(times, winner_lane)
        
        # Update standings
        self.update_standings_display()
        self.save_standings()
        
        # Increment heat
        self.heat_number += 1
        self.heat_label.config(text=f"HEAT #{self.heat_number}")
        
        # Re-enable button
        self.race_btn.config(state='normal', text="🏁 READY TO RACE!")
        
        # Clear assignments
        self.update_lane_options()
        
        # Show success
        messagebox.showinfo("Race Complete", "Heat results recorded!\n\nReady for next heat.")
    
    def save_heat_results(self, times, winner_lane):
        """Save heat results to CSV"""
        try:
            with open(self.heats_file, 'a', newline='') as f:
                writer = csv.writer(f)
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                row = [self.heat_number - 1, timestamp]
                
                for lane in range(1, 5):
                    competitor = self.current_heat_assignments.get(lane, "")
                    time_val = times[lane-1] if times[lane-1] is not None else ""
                    row.extend([competitor, time_val])
                
                if winner_lane:
                    winner_name = self.current_heat_assignments.get(winner_lane, "")
                    row.append(winner_name)
                else:
                    row.append("")
                
                writer.writerow(row)
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving heat results:\n{str(e)}")
    
    # Standings Tab Methods
    def update_standings_display(self):
        """Update standings display"""
        # Clear existing
        for item in self.standings_tree.get_children():
            self.standings_tree.delete(item)
        
        # Sort by best time
        sorted_competitors = sorted(
            self.competitors.items(),
            key=lambda x: x[1]['best_time'] if x[1]['best_time'] is not None else 999.0
        )
        
        # Add rows
        for rank, (name, stats) in enumerate(sorted_competitors, 1):
            best = f"{stats['best_time']:.4f}s" if stats['best_time'] else "---"
            
            if stats['races_count'] > 0:
                avg = stats['total_time'] / stats['races_count']
                avg_str = f"{avg:.4f}s"
            else:
                avg_str = "---"
            
            medal = ""
            if rank == 1 and stats['best_time']:
                medal = "🥇 "
            elif rank == 2 and stats['best_time']:
                medal = "🥈 "
            elif rank == 3 and stats['best_time']:
                medal = "🥉 "
            
            self.standings_tree.insert('', tk.END, 
                                      values=(f"{medal}{rank}", name, best, avg_str, 
                                             stats['races_count']))
    
    def save_standings(self):
        """Save standings to CSV"""
        try:
            sorted_competitors = sorted(
                self.competitors.items(),
                key=lambda x: x[1]['best_time'] if x[1]['best_time'] is not None else 999.0
            )
            
            with open(self.standings_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Rank', 'Name', 'Best Time', 'Average Time', 'Total Races'])
                
                for rank, (name, stats) in enumerate(sorted_competitors, 1):
                    best = stats['best_time'] if stats['best_time'] else ''
                    
                    if stats['races_count'] > 0:
                        avg = stats['total_time'] / stats['races_count']
                    else:
                        avg = ''
                    
                    writer.writerow([rank, name, best, avg, stats['races_count']])
                    
        except Exception as e:
            pass  # Silent fail for background saves
    
    # Navigation
    def show_setup_tab(self):
        self.notebook.select(0)
    
    def show_connection_tab(self):
        self.notebook.select(1)
    
    def show_racing_tab(self):
        self.notebook.select(2)

def main():
    root = tk.Tk()
    app = TournamentGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
