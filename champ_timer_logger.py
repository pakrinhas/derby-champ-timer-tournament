#!/usr/bin/env python3
"""
The Champ Timer - Tournament Edition
Tracks multiple competitors racing in heats of 4 cars
Maintains overall standings and saves detailed results

Works on Mac and Windows
"""

import serial
import serial.tools.list_ports
import csv
import datetime
import os
import time
from pathlib import Path

class TournamentLogger:
    def __init__(self):
        self.serial_port = None
        self.is_running = False
        self.heat_number = 1
        self.results_dir = Path("race_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Competitor tracking
        self.competitors = {}  # {name: {heats: [], best_time: float, total_time: float}}
        self.current_heat_assignments = {}  # {lane: competitor_name}
        
        # CSV files
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.heats_file = self.results_dir / f"heats_{timestamp}.csv"
        self.standings_file = self.results_dir / f"standings_{timestamp}.csv"
        
        # Initialize heats CSV
        with open(self.heats_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Heat #', 'Timestamp', 'Lane 1 Name', 'Lane 1 Time', 
                           'Lane 2 Name', 'Lane 2 Time', 'Lane 3 Name', 'Lane 3 Time',
                           'Lane 4 Name', 'Lane 4 Time', 'Heat Winner'])
    
    def setup_competitors(self):
        """Setup competitor list at the start"""
        print("\n" + "="*60)
        print("COMPETITOR SETUP")
        print("="*60)
        print("\nHow many competitors are racing today?")
        
        while True:
            try:
                num = int(input("Number of competitors: "))
                if num > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")
        
        print(f"\nEnter names for {num} competitors:")
        for i in range(num):
            while True:
                name = input(f"  Competitor {i+1}: ").strip()
                if name:
                    self.competitors[name] = {
                        'heats': [],
                        'best_time': None,
                        'total_time': 0.0,
                        'races_count': 0
                    }
                    break
                print("  Name cannot be empty!")
        
        print(f"\n✓ {len(self.competitors)} competitors registered!")
        print("\nCompetitors:")
        for i, name in enumerate(self.competitors.keys(), 1):
            print(f"  {i}. {name}")
    
    def assign_heat(self):
        """Assign competitors to lanes for the current heat"""
        print("\n" + "="*60)
        print(f"HEAT #{self.heat_number} - LANE ASSIGNMENTS")
        print("="*60)
        
        available_competitors = list(self.competitors.keys())
        
        if not available_competitors:
            print("No competitors available!")
            return False
        
        print("\nAvailable competitors:")
        for i, name in enumerate(available_competitors, 1):
            races = self.competitors[name]['races_count']
            print(f"  {i}. {name} (raced {races} times)")
        
        print("\nAssign competitors to lanes (enter number or name):")
        print("(Press Enter to skip a lane if racing fewer than 4 cars)")
        
        self.current_heat_assignments = {}
        
        for lane in range(1, 5):
            while True:
                assignment = input(f"  Lane {lane}: ").strip()
                
                # Allow empty lane
                if not assignment:
                    print(f"    Lane {lane} will be empty")
                    break
                
                # Try as number first
                try:
                    idx = int(assignment) - 1
                    if 0 <= idx < len(available_competitors):
                        competitor_name = available_competitors[idx]
                        self.current_heat_assignments[lane] = competitor_name
                        print(f"    ✓ {competitor_name} assigned to Lane {lane}")
                        break
                except ValueError:
                    pass
                
                # Try as name
                if assignment in self.competitors:
                    self.current_heat_assignments[lane] = assignment
                    print(f"    ✓ {assignment} assigned to Lane {lane}")
                    break
                
                print("    Invalid selection. Try again.")
        
        # Confirm assignments
        print("\nHeat assignments:")
        for lane in range(1, 5):
            if lane in self.current_heat_assignments:
                print(f"  Lane {lane}: {self.current_heat_assignments[lane]}")
            else:
                print(f"  Lane {lane}: (empty)")
        
        confirm = input("\nReady to race? (y/n): ").lower()
        return confirm == 'y'
    
    def list_ports(self):
        """List all available serial ports"""
        print("\n=== Available Serial Ports ===")
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            print("No serial ports found!")
            return []
        
        for i, port in enumerate(ports):
            print(f"{i+1}. {port.device} - {port.description}")
        
        return [port.device for port in ports]
    
    def connect(self, port_name=None, baudrate=9600):
        """Connect to The Champ timer"""
        try:
            if port_name is None:
                ports = self.list_ports()
                if not ports:
                    return False
                
                choice = input("\nEnter port number (or 'q' to quit): ")
                if choice.lower() == 'q':
                    return False
                
                try:
                    port_idx = int(choice) - 1
                    port_name = ports[port_idx]
                except (ValueError, IndexError):
                    print("Invalid selection!")
                    return False
            
            print(f"\nConnecting to {port_name} at {baudrate} baud...")
            
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            print(f"✓ Connected to {port_name}")
            print(f"✓ Heat results: {self.heats_file}")
            print(f"✓ Standings: {self.standings_file}")
            
            return True
            
        except serial.SerialException as e:
            print(f"Error connecting: {e}")
            return False
    
    def parse_timer_data(self, data_line):
        """Parse data from The Champ timer"""
        times = [None, None, None, None]
        
        try:
            import re
            time_pattern = r'(\d+\.?\d{4})'
            matches = re.findall(time_pattern, data_line)
            
            for i, match in enumerate(matches[:4]):
                times[i] = float(match)
            
            return times
            
        except Exception as e:
            print(f"Parse error: {e}")
            return times
    
    def find_winner(self, times):
        """Determine the winning lane"""
        valid_times = [(i+1, t) for i, t in enumerate(times) if t is not None]
        
        if not valid_times:
            return None, None
        
        winner_lane, winner_time = min(valid_times, key=lambda x: x[1])
        return winner_lane, winner_time
    
    def display_heat_results(self, times):
        """Display heat results"""
        print("\n" + "="*60)
        print(f"🏁 HEAT #{self.heat_number} RESULTS - {datetime.datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        winner_lane, winner_time = self.find_winner(times)
        
        for lane in range(1, 5):
            competitor = self.current_heat_assignments.get(lane, "---")
            time_val = times[lane-1]
            
            if time_val is not None:
                winner_mark = " 🏆 HEAT WINNER!" if lane == winner_lane else ""
                print(f"  Lane {lane} - {competitor:20s}: {time_val:.4f}s{winner_mark}")
            else:
                print(f"  Lane {lane} - {competitor:20s}: ---")
        
        print("="*60)
        
        return winner_lane
    
    def update_competitor_stats(self, times):
        """Update competitor statistics"""
        for lane in range(1, 5):
            if lane in self.current_heat_assignments and times[lane-1] is not None:
                competitor = self.current_heat_assignments[lane]
                time_val = times[lane-1]
                
                # Update stats
                self.competitors[competitor]['heats'].append({
                    'heat': self.heat_number,
                    'lane': lane,
                    'time': time_val
                })
                self.competitors[competitor]['races_count'] += 1
                self.competitors[competitor]['total_time'] += time_val
                
                # Update best time
                if (self.competitors[competitor]['best_time'] is None or 
                    time_val < self.competitors[competitor]['best_time']):
                    self.competitors[competitor]['best_time'] = time_val
    
    def log_heat_results(self, times, winner_lane):
        """Save heat results to CSV"""
        try:
            with open(self.heats_file, 'a', newline='') as f:
                writer = csv.writer(f)
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                row = [self.heat_number, timestamp]
                
                for lane in range(1, 5):
                    competitor = self.current_heat_assignments.get(lane, "")
                    time_val = times[lane-1] if times[lane-1] is not None else ""
                    row.extend([competitor, time_val])
                
                # Add winner
                if winner_lane:
                    winner_name = self.current_heat_assignments.get(winner_lane, "")
                    row.append(winner_name)
                else:
                    row.append("")
                
                writer.writerow(row)
                
        except Exception as e:
            print(f"Error saving heat results: {e}")
    
    def display_standings(self):
        """Display current tournament standings"""
        print("\n" + "="*60)
        print("📊 CURRENT STANDINGS")
        print("="*60)
        
        # Sort by best time
        sorted_competitors = sorted(
            self.competitors.items(),
            key=lambda x: x[1]['best_time'] if x[1]['best_time'] is not None else 999.0
        )
        
        print(f"\n{'Rank':<6} {'Name':<20} {'Best Time':<12} {'Avg Time':<12} {'Races':<8}")
        print("-" * 60)
        
        for rank, (name, stats) in enumerate(sorted_competitors, 1):
            best = f"{stats['best_time']:.4f}s" if stats['best_time'] else "---"
            
            if stats['races_count'] > 0:
                avg = stats['total_time'] / stats['races_count']
                avg_str = f"{avg:.4f}s"
            else:
                avg_str = "---"
            
            races = stats['races_count']
            
            medal = ""
            if rank == 1 and stats['best_time']:
                medal = "🥇"
            elif rank == 2 and stats['best_time']:
                medal = "🥈"
            elif rank == 3 and stats['best_time']:
                medal = "🥉"
            
            print(f"{rank:<6} {name:<20} {best:<12} {avg_str:<12} {races:<8} {medal}")
        
        print("="*60)
    
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
            
            print(f"\n✓ Standings saved to {self.standings_file}")
            
        except Exception as e:
            print(f"Error saving standings: {e}")
    
    def run_tournament(self):
        """Main tournament loop"""
        if not self.serial_port:
            print("Not connected to timer!")
            return
        
        self.is_running = True
        print("\n🏁 Tournament Mode Active!")
        print("After each heat, you'll assign competitors for the next heat.")
        print("Press Ctrl+C when tournament is complete.\n")
        
        buffer = ""
        
        try:
            while self.is_running:
                # Assign heat
                if not self.assign_heat():
                    print("\nSkipping heat...")
                    continue
                
                print("\n👂 Waiting for race data from timer...")
                print("Run the race on The Champ timer...\n")
                
                race_complete = False
                
                while not race_complete and self.is_running:
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
                                print(f"📡 Raw data: {line}")
                                
                                times = self.parse_timer_data(line)
                                
                                if any(t is not None for t in times):
                                    winner_lane = self.display_heat_results(times)
                                    self.update_competitor_stats(times)
                                    self.log_heat_results(times, winner_lane)
                                    self.display_standings()
                                    self.save_standings()
                                    
                                    self.heat_number += 1
                                    race_complete = True
                                    
                                    time.sleep(2)
                                    break
                    
                    time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n⏹ Tournament Complete!")
            self.is_running = False
            self.display_standings()
            self.save_standings()
            print("\n🏆 Final results saved!")
        except Exception as e:
            print(f"\nError: {e}")
            self.is_running = False
    
    def close(self):
        """Close serial connection"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("✓ Serial port closed")

def main():
    print("""
╔═══════════════════════════════════════════╗
║   THE CHAMP TIMER - TOURNAMENT EDITION    ║
║   Multi-Competitor Heat Tracking          ║
╚═══════════════════════════════════════════╝
    """)
    
    logger = TournamentLogger()
    
    # Setup competitors first
    logger.setup_competitors()
    
    # Ask for baudrate
    print("\nCommon baudrates: 9600 (default), 19200, 38400, 115200")
    baud = input("Enter baudrate (press Enter for 9600): ").strip()
    baudrate = int(baud) if baud else 9600
    
    # Connect to timer
    if logger.connect(baudrate=baudrate):
        try:
            logger.run_tournament()
        finally:
            logger.close()
    else:
        print("\n❌ Failed to connect to timer")

if __name__ == "__main__":
    main()