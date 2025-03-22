import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import tkinter.ttk as ttk
import subprocess
import json
import os
import threading
import sys
import time
from tkinter import filedialog, messagebox

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class ScriptLauncherUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Launcher")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        
        # Configure the grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)  # Progress bar row
        self.root.grid_rowconfigure(2, weight=1)  # Log window row
        
        # Create buttons
        self.btn_site_a = tk.Button(root, text="Run siteA.bat", command=self.run_site_a, 
                                  bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), 
                                  padx=20, pady=10)
        self.btn_site_a.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.btn_site_b = tk.Button(root, text="Run siteB.bat", command=self.run_site_b, 
                                  bg="#2196F3", fg="white", font=("Arial", 12, "bold"), 
                                  padx=20, pady=10)
        self.btn_site_b.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.btn_config = tk.Button(root, text="Change config.json", command=self.edit_config, 
                                  bg="#FF9800", fg="white", font=("Arial", 12, "bold"), 
                                  padx=20, pady=10)
        self.btn_config.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        
        # Create progress bar frame
        self.progress_frame = tk.LabelFrame(root, text="Progress", font=("Arial", 10))
        self.progress_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew")
        
        # Progress bar and time remaining label
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                         length=100, mode="determinate", 
                                         variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.time_label = tk.Label(self.progress_frame, text="Estimated time remaining: --:--", 
                                 font=("Arial", 9))
        self.time_label.pack(pady=(0, 5))
        
        # Create log window
        self.log_frame = tk.LabelFrame(root, text="Log Output", font=("Arial", 10))
        self.log_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="nsew")
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, 
                                               bg="#F0F0F0", font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")
        
        # Set up output redirection
        self.redirect = RedirectText(self.log_text)
        
        # Store the current working directory
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize process variable
        self.process = None
        
        # Initialize progress tracking variables
        self.start_time = 0
        self.estimated_duration = 0  # in seconds
        self.progress_update_id = None
    
    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")
    
    def reset_progress_bar(self):
        """Reset the progress bar to initial state"""
        self.progress_var.set(0)
        self.time_label.config(text="Estimated time remaining: --:--")
        if self.progress_update_id:
            self.root.after_cancel(self.progress_update_id)
            self.progress_update_id = None
    
    def update_progress(self):
        """Update the progress bar and time remaining"""
        if not self.process or self.process.poll() is not None:  # Process completed
            self.progress_var.set(100)
            self.time_label.config(text="Completed")
            return
        
        elapsed_time = time.time() - self.start_time
        
        # For the first 10 seconds, we'll use a predetermined estimate
        if elapsed_time < 10:
            # Set progress to show activity but not much progress yet
            progress = min(5, (elapsed_time / 10) * 5)
            self.progress_var.set(progress)
            
            # For siteA.bat, estimate 3 minutes, for siteB.bat estimate 2 minutes
            script_name = os.path.basename(self.current_script)
            if script_name == "siteA.bat":
                self.estimated_duration = 180  # 3 minutes in seconds
            else:  # siteB.bat or any other script
                self.estimated_duration = 120  # 2 minutes in seconds
                
            remaining = self.estimated_duration - elapsed_time
        else:
            # After 10 seconds, we'll use a more dynamic approach
            # Assuming linear progress, calculate percentage complete based on elapsed time
            progress = min(95, (elapsed_time / self.estimated_duration) * 100)
            self.progress_var.set(progress)
            
            # Calculate remaining time
            if progress > 0:
                remaining = (self.estimated_duration * (100 - progress)) / 100
            else:
                remaining = self.estimated_duration
        
        # Format remaining time
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        self.time_label.config(text=f"Estimated time remaining: {minutes:02d}:{seconds:02d}")
        
        # Schedule the next update
        self.progress_update_id = self.root.after(1000, self.update_progress)
    
    def run_script(self, script_path):
        self.clear_log()
        self.reset_progress_bar()
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, f"Running {os.path.basename(script_path)}...\n")
        self.log_text.configure(state="disabled")
        
        # Store the current script path for reference
        self.current_script = script_path
        
        def execute():
            try:
                # Set start time for progress tracking
                self.start_time = time.time()
                
                # Start progress updates
                self.root.after(100, self.update_progress)
                
                # Run the batch file and capture output
                self.process = subprocess.Popen(
                    script_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=self.cwd,
                    shell=True
                )
                
                # Read and display output in real-time
                for line in self.process.stdout:
                    self.redirect.write(line)
                
                self.process.wait()
                self.redirect.write(f"\nProcess completed with exit code: {self.process.returncode}\n")
                
                # Ensure progress bar shows completion
                self.progress_var.set(100)
                self.time_label.config(text="Completed")
            except Exception as e:
                self.redirect.write(f"Error: {str(e)}\n")
                self.reset_progress_bar()
        
        # Run in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=execute)
        thread.daemon = True
        thread.start()
    
    def run_site_a(self):
        script_path = os.path.join(self.cwd, "siteA.bat")
        self.run_script(script_path)
    
    def run_site_b(self):
        script_path = os.path.join(self.cwd, "siteB.bat")
        self.run_script(script_path)
    
    def edit_config(self):
        config_path = os.path.join(self.cwd, "config.json")
        
        try:
            # Read the current config
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Create a new window for editing
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit config.json")
            edit_window.geometry("600x500")
            
            # Create a frame for the form
            form_frame = tk.Frame(edit_window)
            form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Create entry fields for each config item
            row = 0
            entries = {}
            
            for key, value in config_data.items():
                # Create label
                label = tk.Label(form_frame, text=key, font=("Arial", 10, "bold"))
                label.grid(row=row, column=0, sticky="w", pady=5)
                
                # Create entry field
                if isinstance(value, list):
                    entry = tk.Entry(form_frame, width=50)
                    entry.insert(0, ", ".join(value))
                else:
                    entry = tk.Entry(form_frame, width=50)
                    entry.insert(0, str(value))
                
                entry.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
                entries[key] = entry
                row += 1
            
            # Configure grid
            form_frame.columnconfigure(1, weight=1)
            
            # Function to save changes
            def save_config():
                try:
                    updated_config = {}
                    for key, entry in entries.items():
                        value = entry.get()
                        
                        # Convert back to original type
                        if isinstance(config_data[key], list):
                            value = [item.strip() for item in value.split(",")]
                        elif isinstance(config_data[key], int):
                            value = int(value)
                        elif isinstance(config_data[key], float):
                            value = float(value)
                        elif isinstance(config_data[key], bool):
                            value = value.lower() == "true"
                        
                        updated_config[key] = value
                    
                    # Write back to file with proper formatting
                    with open(config_path, 'w') as f:
                        json.dump(updated_config, f, indent=4)
                    
                    self.redirect.write(f"Config file updated successfully.\n")
                    edit_window.destroy()
                except Exception as e:
                    tk.messagebox.showerror("Error", f"Failed to save config: {str(e)}")
            
            # Add save button
            save_btn = tk.Button(form_frame, text="Save Changes", command=save_config,
                               bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                               padx=10, pady=5)
            save_btn.grid(row=row, column=0, columnspan=2, pady=20)
            
        except Exception as e:
            self.redirect.write(f"Error opening config file: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptLauncherUI(root)
    root.mainloop()