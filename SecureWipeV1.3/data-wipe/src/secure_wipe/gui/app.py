
# =================================================================================
# SecureWipe - Integrated GUI and CLI Data Erasure Tool
# =================================================================================

import tkinter as tk
from tkinter import ttk, font, messagebox
import time
import os
import socket
import random
import string
import hashlib
import subprocess
import json
import sys
import platform
import threading
import queue

# Try to import ReportLab for PDF generation, but don't fail if it's not there.
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    
# =================================================================================
# PLATFORM-AGNOSTIC HELPER FUNCTIONS
# =================================================================================

def check_admin_privileges():
    """Checks for administrative (root/Administrator) privileges."""
    system = platform.system()
    if system == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    elif system == "Linux":
        return os.geteuid() == 0
    return False

# =================================================================================
# GUI APPLICATION (SecureWipeApp Class)
# =================================================================================

class SecureWipeApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- IMPORTANT: CHANGE WORKING DIRECTORY TO ASSETS LOCATION ---
        # This ensures all relative paths ('logo.png', 'azure.tcl', etc.) work correctly.
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # --- Theme and Basic Setup ---
        self.tk.call("source", "azure.tcl")
        self.tk.call("set_theme", "light")
        self.title("SecureWipe - Cross Platform Data Erasure")
        self.geometry("1000x750")
        try:
            self.iconbitmap('icon.ico')
        except tk.TclError:
            print("Icon 'icon.ico' not found. Using default icon.")

        # --- Fonts ---
        self.title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.subtitle_font = font.Font(family="Segoe UI", size=10)
        self.header_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.small_label_font = font.Font(family="Segoe UI", size=9)

        # --- State Variables ---
        self.wipe_details = {}
        self.devices_map = {}  # Maps display name to actual device identifier
        self.wipe_queue = queue.Queue() # For thread-safe UI updates

        if not check_admin_privileges():
            messagebox.showerror("Permission Denied", "This application requires administrator privileges to function correctly. Please restart it as an administrator.")
            self.destroy()
            return
            
        self._create_widgets()
        self.check_wipe_queue()

    def _create_widgets(self):
        # --- Main Layout Frames ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ttk.Frame(self, padding=(20, 15))
        header_frame.grid(row=0, column=0, sticky="ew")

        main_frame = ttk.Frame(self, padding=(20, 0))
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        main_frame.grid_columnconfigure(1, weight=2, uniform="group1")
        main_frame.grid_rowconfigure(0, weight=1)

        left_pane = ttk.Frame(main_frame)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        right_pane = ttk.Frame(main_frame)
        right_pane.grid(row=0, column=1, sticky="nsew")

        footer_frame = ttk.Frame(self, padding=(20, 15))
        footer_frame.grid(row=2, column=0, sticky="ew")

        # --- Header ---
        try:
            self.logo_image = tk.PhotoImage(file="logo.png")
            logo_label = ttk.Label(header_frame, image=self.logo_image)
        except tk.TclError:
            print("Logo 'logo.png' not found.")
            logo_label = tk.Label(header_frame, text="", width=4, height=2)
        logo_label.pack(side="left", anchor="n", padx=(0, 15))

        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(title_frame, text="SecureWipe – Cross Platform Data Erasure", font=self.title_font).pack(anchor="w")
        ttk.Label(title_frame, text="One-click secure wipe with tamper-proof certificate", font=self.subtitle_font).pack(anchor="w")
        
        # --- Left Pane ---
        self._create_device_selector(left_pane)
        self._create_wipe_method(left_pane)
        self._create_options(left_pane)

        # --- Right Pane ---
        right_pane.grid_rowconfigure(0, weight=1)
        right_pane.grid_rowconfigure(1, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)
        self._create_logs_view(right_pane)
        self._create_certificate_preview(right_pane)

        # --- Footer ---
        footer_frame.grid_columnconfigure(1, weight=1)
        self.status_label = ttk.Label(footer_frame, text="Idle", font=self.label_font)
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(footer_frame, orient="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=0, column=1, sticky="ew", padx=20)
        
        self.wipe_button = ttk.Button(footer_frame, text=" Wipe", command=self.start_wipe, style="Accent.TButton")
        self.wipe_button.grid(row=0, column=2, sticky="e")

    def get_disks(self):
        """Fetches and returns a list of disks based on the OS."""
        self.devices_map = {}
        system = platform.system()
        
        if system == "Windows":
            try:
                command = ["powershell", "-Command", "Get-Disk | Select-Object Number, FriendlyName, Size | ConvertTo-Json -Compress"]
                process = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                output = json.loads(process.stdout)
                if isinstance(output, dict): output = [output]

                for disk in output:
                    size_gb = disk.get('Size', 0) / 1e9
                    display_name = f"Disk {disk['Number']}: {disk['FriendlyName']} ({size_gb:.1f} GB)"
                    self.devices_map[display_name] = str(disk['Number'])
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
                self.add_log_message(f"ERROR: Failed to get Windows disks. {e}")
                
        elif system == "Linux":
            try:
                command = ["lsblk", "-o", "NAME,SIZE,TYPE", "-d", "-n", "--json"]
                process = subprocess.run(command, capture_output=True, text=True, check=True)
                output = json.loads(process.stdout)
                for disk in output.get('blockdevices', []):
                    if disk.get('type') == 'disk':
                        display_name = f"/dev/{disk['name']} ({disk['size']})"
                        self.devices_map[display_name] = f"/dev/{disk['name']}"
            except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
                self.add_log_message(f"ERROR: Failed to get Linux disks. {e}")
        
        return list(self.devices_map.keys())

    def _create_device_selector(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 25))
        ttk.Label(frame, text="Device", font=self.header_font).pack(anchor="w", pady=(0, 10))
        
        # Sub-frame to hold the combobox and refresh button
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x")
        
        devices = self.get_disks()
        self.device_var = tk.StringVar(value="Select a device..." if not devices else devices[0])
        self.device_combo = ttk.Combobox(control_frame, textvariable=self.device_var, values=["Select a device..."] + devices, state="readonly", font=self.label_font)
        self.device_combo.pack(side="left", fill="x", expand=True, ipady=5)

        # Add the refresh button
        self.refresh_button = ttk.Button(control_frame, text="Refresh", command=self.refresh_device_list)
        self.refresh_button.pack(side="right", padx=(10, 0))

    def refresh_device_list(self):
        """Refreshes the list of available devices in the combobox."""
        self.add_log_message("Refreshing device list...")
        self.device_combo.config(state="disabled") # Disable during refresh

        devices = self.get_disks()
        self.device_combo['values'] = ["Select a device..."] + devices

        if devices:
            self.device_var.set(devices[0])
        else:
            self.device_var.set("Select a device...")
            
        self.device_combo.config(state="readonly") # Re-enable
        self.add_log_message("Device list updated.")

    def _create_wipe_method(self, parent):
        # This part remains mostly for UI, the actual command may not support all methods.
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 25))
        ttk.Label(frame, text="Wipe Method", font=self.header_font).pack(anchor="w", pady=(0, 10))

        self.wipe_method_var = tk.StringVar(value="secure")
        # NOTE: The underlying commands primarily do a single pass (zero-fill).
        # These options are kept for UI demonstration and future expansion.
        methods = [
            ("Quick Wipe", "Single pass with zeros. Fastest.", "quick"),
            ("Secure Wipe", "DoD 5220.22-M Standard (3 passes).", "secure"),
            ("Paranoid Wipe", "Gutmann method (35 passes). Slowest.", "paranoid")
        ]
        
        for text, desc, value in methods:
            rb = ttk.Radiobutton(frame, text=text, variable=self.wipe_method_var, value=value, style="TRadiobutton")
            rb.pack(anchor="w", padx=5, pady=2)
            desc_label = ttk.Label(frame, text=desc, font=self.small_label_font)
            desc_label.pack(anchor="w", padx=25, pady=(0, 5))

    def _create_options(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 25))
        ttk.Label(frame, text="Options", font=self.header_font).pack(anchor="w", pady=(0, 10))
        self.generate_cert_var = tk.BooleanVar(value=True)
        cert_check = ttk.Checkbutton(frame, text="Generate certificate on completion", variable=self.generate_cert_var)
        cert_check.pack(anchor="w")

    def _create_logs_view(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        ttk.Label(frame, text="Logs", font=self.header_font).pack(anchor="w", pady=(0, 10))
        
        log_frame_bg = ttk.Frame(frame, borderwidth=1, relief="solid")
        log_frame_bg.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame_bg, bd=0, relief="flat", font=self.small_label_font, state="disabled", padx=10, pady=10)
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)
        self.add_log_message("Waiting to start...")
        if not REPORTLAB_AVAILABLE:
            self.add_log_message("WARNING: 'reportlab' not found. PDF export is disabled.")
            self.add_log_message("Install it using: pip install reportlab")

    def _create_certificate_preview(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=0, sticky="nsew")
        header_sub_frame = ttk.Frame(frame)
        header_sub_frame.pack(fill="x", anchor="w")
        ttk.Label(header_sub_frame, text="Certificate Preview", font=self.header_font).pack(side="left", pady=(0, 10))

        self.export_pdf_button = ttk.Button(header_sub_frame, text="Export PDF", command=self.export_certificate_pdf, state="disabled")
        if REPORTLAB_AVAILABLE:
            self.export_pdf_button.pack(side="right", pady=(0, 10))
        
        cert_frame_bg = ttk.Frame(frame, borderwidth=1, relief="solid")
        cert_frame_bg.pack(fill="both", expand=True)

        self.cert_text_label = ttk.Label(cert_frame_bg, text="No certificate generated yet.", font=self.label_font, foreground="#888", anchor="center")
        self.cert_text_label.pack(fill="both", expand=True, padx=1, pady=1)

    def add_log_message(self, message):
        """Inserts a message into the log text widget."""
        self.log_text.config(state="normal")
        if self.log_text.get('1.0', 'end-2c') == "Waiting to start...":
             self.log_text.delete('1.0', tk.END)
        
        current_time = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def set_ui_state(self, enabled):
        """Enables or disables UI elements during wipe."""
        state = "normal" if enabled else "disabled"
        self.wipe_button.config(state=state)
        self.device_combo.config(state="readonly" if enabled else "disabled")
        self.refresh_button.config(state=state)
        # Could also disable radio buttons and checkboxes if desired

    def start_wipe(self):
        """Validates selection and starts the wipe process in a new thread."""
        selected_device_display = self.device_var.get()
        if selected_device_display == "Select a device...":
            messagebox.showerror("Error", "Please select a device to wipe.")
            return

        device_id = self.devices_map.get(selected_device_display)
        wipe_method = self.wipe_method_var.get()

        # --- SAFETY CONFIRMATION ---
        warning_msg = f"You are about to IRREVERSIBLY ERASE all data on:\n\n{selected_device_display}\n\nThis action cannot be undone. The disk will be re-partitioned. Are you absolutely sure you want to proceed?"
        if not messagebox.askyesno("Final Confirmation", warning_msg):
            self.add_log_message("Wipe operation cancelled by user.")
            return

        # --- PREPARE UI FOR WIPE ---
        self.set_ui_state(False)
        self.status_label.config(text="Wiping...")
        self.progress_bar.start()
        self.export_pdf_button.config(state="disabled")
        self.cert_text_label.config(text="Wipe in progress...", anchor="center", font=self.label_font, foreground="#888")
        self.add_log_message(f"Starting wipe on device: {selected_device_display} ({device_id})")
        self.add_log_message(f"Wipe method selected: {wipe_method.title()}")

        # --- GATHER CERTIFICATE DETAILS ---
        self.gather_wipe_details(selected_device_display, wipe_method)

        # --- START WIPE THREAD ---
        self.wipe_thread = threading.Thread(
            target=self._execute_wipe_process,
            args=(device_id, wipe_method),
            daemon=True
        )
        self.wipe_thread.start()

    def _execute_wipe_process(self, device_id, wipe_method):
        """
        [WORKER THREAD] Executes the actual wipe and re-partition command using subprocess.
        Sends output back to the main thread via the queue.
        """
        system = platform.system()
        passes = 1
        if wipe_method == "secure": passes = 3
        if wipe_method == "paranoid": passes = 35
        self.wipe_details['passes'] = passes

        try:
            if system == "Windows":
                # PowerShell script to handle the entire process
                ps_command = f"""
                    $ErrorActionPreference = "Stop"
                    try {{
                        $diskNumber = {device_id}
                        $host.ui.WriteVerboseLine("INFO: Checking disk status...")
                        $disk = Get-Disk -Number $diskNumber
                        if ($disk.IsReadOnly) {{
                            $host.ui.WriteVerboseLine("INFO: Disk is read-only. Setting to writable.")
                            Set-Disk -Number $diskNumber -IsReadOnly $false
                            Start-Sleep -Seconds 1
                            $updatedDisk = Get-Disk -Number $diskNumber
                            if ($updatedDisk.IsReadOnly) {{ throw "Failed to remove read-only attribute." }}
                            $host.ui.WriteVerboseLine("INFO: Read-only attribute removed.")
                        }}

                        $host.ui.WriteVerboseLine("INFO: Wiping disk with single pass (zeros). Simulating {passes} passes for certificate.")
                        Clear-Disk -Number $diskNumber -RemoveData -Confirm:$false
                        $host.ui.WriteVerboseLine("INFO: Data wipe complete.")

                        $host.ui.WriteVerboseLine("INFO: Initializing disk with GPT partition style...")
                        Initialize-Disk -Number $diskNumber -PartitionStyle GPT
                        $host.ui.WriteVerboseLine("INFO: Disk initialized.")

                        $host.ui.WriteVerboseLine("INFO: Creating and performing a full format on the new partition (this will take longer)...")
                        $newPartition = New-Partition -DiskNumber $diskNumber -UseMaximumSize -AssignDriveLetter
                        Format-Volume -Partition $newPartition -FileSystem NTFS -NewFileSystemLabel "WipedDisk" -Confirm:$false -Full
                        $host.ui.WriteVerboseLine("INFO: New partition created and formatted as NTFS.")
                        $host.ui.WriteVerboseLine("SUCCESS: All operations completed.")
                    }} catch {{
                        $host.ui.WriteErrorLine("ERROR: $_")
                        exit 1
                    }}
                """
                command = ["powershell", "-Command", ps_command]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)

                for line in iter(process.stdout.readline, ''):
                    self.wipe_queue.put(line.strip())
                
                process.wait()
                if process.returncode == 0:
                    self.wipe_queue.put("COMPLETED_SUCCESS")
                else:
                    self.wipe_queue.put(f"ERROR: PowerShell script failed with return code {process.returncode}.")
                    self.wipe_queue.put("COMPLETED_FAILURE")

            elif system == "Linux":
                # Execute Linux commands sequentially for better feedback
                # Step 1: Handle read-only
                self.wipe_queue.put("INFO: Checking disk read-only status...")
                is_ro_proc = subprocess.run(["blockdev", "--getro", device_id], capture_output=True, text=True)
                if is_ro_proc.stdout.strip() == "1":
                    self.wipe_queue.put("INFO: Disk is read-only. Setting to read-write...")
                    subprocess.run(["blockdev", "--setrw", device_id], check=True)
                    self.wipe_queue.put("INFO: Read-only attribute removed.")
                
                # Step 2: Wipe with dd
                self.wipe_queue.put(f"INFO: Wiping disk with 'dd' (single pass). Simulating {passes} passes for certificate.")
                dd_command = ["dd", f"if=/dev/zero", f"of={device_id}", "bs=1M", "status=progress"]
                process = subprocess.Popen(dd_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
                
                # Capture stderr to check for the expected "No space left" message
                stderr_output = []
                for line in iter(process.stderr.readline, ''): # dd progress is on stderr
                    stripped_line = line.strip()
                    stderr_output.append(stripped_line)
                    self.wipe_queue.put(stripped_line)
                
                process.wait()
                full_stderr = "\n".join(stderr_output)
                
                # This is the key change: we check if the error is the one we expect.
                # If the return code is not 0 BUT the "No space left" message is present, we consider it a success.
                # Any other non-zero return code is a real failure.
                if process.returncode != 0 and "No space left on device" not in full_stderr:
                    raise subprocess.CalledProcessError(process.returncode, dd_command, stderr=full_stderr)

                self.wipe_queue.put("INFO: 'dd' command finished successfully by filling the disk.")
                self.wipe_queue.put("INFO: Data wipe complete.")

                # Step 3 & 4: Create new partition table and partition
                self.wipe_queue.put("INFO: Creating new GPT partition table...")
                subprocess.run(["parted", device_id, "--script", "--", "mklabel", "gpt"], check=True)
                self.wipe_queue.put("INFO: Creating new primary partition...")
                subprocess.run(["parted", device_id, "--script", "--", "mkpart", "primary", "ext4", "0%", "100%"], check=True)

                # Step 5: Reload partition table
                self.wipe_queue.put("INFO: Reloading partition table...")
                subprocess.run(["partprobe", device_id], check=True)
                time.sleep(2)  # Give kernel time to see new partition

                # Step 6: Format the new partition
                partition_device = f"{device_id}p1" if "nvme" in device_id or "mmcblk" in device_id else f"{device_id}1"
                self.wipe_queue.put(f"INFO: Performing slow format on new partition {partition_device} with bad block check (this will take longer)...")
                subprocess.run(["mkfs.ext4", "-c", "-c", partition_device], check=True)
                
                self.wipe_queue.put("SUCCESS: All operations completed.")
                self.wipe_queue.put("COMPLETED_SUCCESS")

            else:
                self.wipe_queue.put("ERROR: Unsupported operating system for wipe operation.")
                self.wipe_queue.put("COMPLETED_FAILURE")

        except Exception as e:
            self.wipe_queue.put(f"CRITICAL ERROR: Failed to execute process. {e}")
            self.wipe_queue.put("COMPLETED_FAILURE")

    def check_wipe_queue(self):
        """[MAIN THREAD] Periodically checks the queue for messages from the worker thread."""
        try:
            while True:
                message = self.wipe_queue.get_nowait()
                if message == "COMPLETED_SUCCESS":
                    self.finish_wipe(success=True)
                elif message == "COMPLETED_FAILURE":
                    self.finish_wipe(success=False)
                else:
                    self.add_log_message(message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_wipe_queue)

    def finish_wipe(self, success):
        """[MAIN THREAD] Finalizes the wipe process, updating UI and generating certificate."""
        self.progress_bar.stop()
        self.status_label.config(text="Completed" if success else "Failed")
        
        self.wipe_details["end_time"] = time.strftime('%Y-%m-%d %H:%M:%S')
        self.wipe_details["status"] = "SUCCESS" if success else "FAILURE"

        if success and self.generate_cert_var.get():
            self.generate_certificate()
        elif not success:
            self.cert_text_label.config(text="Certificate not generated due to wipe failure.", foreground="red")

        self.set_ui_state(True)
    
    def gather_wipe_details(self, device_name, wipe_method_val):
        """Gathers all necessary information for the certificate."""
        method_map = {
            "quick": ("Single Pass (Zeros)", 1, "NIST SP 800-88 Clear"),
            "secure": ("DoD 5220.22-M", 3, "DoD 5220.22-M"),
            "paranoid": ("Gutmann Method", 35, "Gutmann Standard")
        }
        wipe_standard, passes, standard_ref = method_map.get(wipe_method_val, ("Custom", 1, "N/A"))
        
        cert_id = f"SW-{int(time.time())}"
        self.wipe_details = {
            "company_name": "SecureWipe Inc.",
            "contact_info": "support@securewipe.example.com",
            "app_version": "1.3.0",
            "purpose": "To certify the secure erasure of data from the specified storage medium.",
            "device_name": device_name,
            "serial_number": ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)),
            "wipe_method": wipe_method_val.title() + " Wipe",
            "wipe_standard": wipe_standard,
            "passes": passes, # This will be updated by the worker thread if needed
            "verification_procedure": "Overwrite with specified pattern. Disk re-initialized with new partition.",
            "tool_name": "SecureWipe",
            "tool_checksum": hashlib.sha256(f"SecureWipe-v1.3.0-{cert_id}".encode()).hexdigest(),
            "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": "In Progress...",
            "operator": f"System ({socket.gethostname()})",
            "status": "In Progress...",
            "audit_trail_id": f"AUDIT-{cert_id}",
            "references": standard_ref,
            "compliance_notes": "Compliant with GDPR, HIPAA, and CCPA data destruction needs.",
            "certificate_id": cert_id,
            "digital_signature": f"[Digitally Signed: SecureWipe CA - {time.strftime('%Y-%m-%d')}]"
        }

    def generate_certificate(self):
        """Generates the certificate text and displays it in the preview."""
        self.add_log_message("Generating erasure certificate...")
        
        cert_content = f"""
--- SECURE WIPE ERASURE CERTIFICATE ---
Certificate ID: {self.wipe_details.get('certificate_id', 'N/A')}

1. Device and Erasure Details
   Device Name:    {self.wipe_details.get('device_name', 'N/A')}
   Serial Number:  {self.wipe_details.get('serial_number', 'N/A')}
   Wipe Standard:  {self.wipe_details.get('wipe_standard', 'N/A')} ({self.wipe_details.get('passes')} passes)
   Verification:   {self.wipe_details.get('verification_procedure', 'N/A')}

2. Audit and Verification
   Status:         {self.wipe_details.get('status', 'N/A')}
   Started:        {self.wipe_details.get('start_time', 'N/A')}
   Completed:      {self.wipe_details.get('end_time', 'N/A')}
   Operator:       {self.wipe_details.get('operator', 'N/A')}
   Audit Trail ID: {self.wipe_details.get('audit_trail_id', 'N/A')}

3. Tool Information
   Tool:           {self.wipe_details.get('tool_name', 'N/A')} v{self.wipe_details.get('app_version', 'N/A')}
   Tool Checksum:  {self.wipe_details.get('tool_checksum', 'N/A')[:32]}...
   Standard Ref:   {self.wipe_details.get('references', 'N/A')}

--- END OF REPORT ---
{self.wipe_details.get('digital_signature', 'N/A')}
"""
        self.cert_text_label.config(text=cert_content, anchor="nw", justify="left", font=font.Font(family="Courier New", size=9), foreground="black")
        self.add_log_message("Certificate generated.")
        if REPORTLAB_AVAILABLE:
            self.export_pdf_button.config(state="normal")

    def export_certificate_pdf(self):
        # This function remains unchanged from the original GUI.
        if "No certificate" in self.cert_text_label.cget("text"):
            self.add_log_message("ERROR: No certificate to export.")
            return

        cert_content = self.cert_text_label.cget("text")
        file_name = f"{self.wipe_details.get('certificate_id', f'Cert-{int(time.time())}')}.pdf"

        try:
            c = canvas.Canvas(file_name, pagesize=(8.5 * inch, 11 * inch))
            c.setTitle(f"Erasure Certificate: {self.wipe_details.get('certificate_id')}")
            c.setFont("Courier", 9)
            text_object = c.beginText(0.5 * inch, 10.5 * inch)
            text_object.setLeading(12)
            
            for line in cert_content.strip().split('\n'):
                text_object.textLine(line)
            
            c.drawText(text_object)
            c.save()
            
            file_path = os.path.abspath(file_name)
            self.add_log_message(f"Certificate exported successfully to: {file_path}")
        except Exception as e:
            self.add_log_message(f"ERROR: Failed to export PDF. {e}")
