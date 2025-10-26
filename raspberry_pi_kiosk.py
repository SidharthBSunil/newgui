#!/usr/bin/env python3
"""
Revive Print Kiosk - Raspberry Pi UI
A fun, modern kiosk interface for printing with easter eggs!

Requirements:
    pip install pillow qrcode cups-python pdf2image flask requests

System Requirements:
    - CUPS installed and configured
    - HP LaserJet M208dw configured in CUPS
"""

import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time
import cups
import os
import tempfile
from pdf2image import convert_from_path
import requests
from flask import Flask, request, jsonify
import json
from datetime import datetime

# Configuration
UPLOAD_URL = "http://localhost:5001"  # Your Flask backend URL
PRINTER_NAME = "HP_LaserJet_M208dw"  # Your printer name in CUPS
QR_URL = "https://printervendingmachine.onrender.com/"  # Your web app URL
KONAMI_CODE = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']

class PrintKiosk:
    def __init__(self, root):
        self.root = root
        self.root.title("Revive Print Kiosk")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#1a1a2e')
        
        # State management
        self.current_screen = "welcome"
        self.current_file = None
        self.preview_images = []
        self.current_page = 0
        self.print_settings = {
            'page_range': 'all',
            'orientation': 'portrait',
            'duplex': 'none'
        }
        
        # Easter egg tracking
        self.konami_progress = []
        self.secret_clicks = 0
        
        # CUPS connection
        try:
            self.cups_conn = cups.Connection()
            self.printers = self.cups_conn.getPrinters()
            if PRINTER_NAME not in self.printers:
                print(f"Warning: Printer '{PRINTER_NAME}' not found in CUPS")
        except Exception as e:
            print(f"Error connecting to CUPS: {e}")
            self.cups_conn = None
        
        # Bind keyboard for easter eggs
        self.root.bind('<Key>', self.check_konami)
        
        # Create main container
        self.container = tk.Frame(self.root, bg='#1a1a2e')
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Start with welcome screen
        self.show_welcome()
        
        # Start background server to receive files
        self.start_file_receiver()
    
    def clear_screen(self):
        """Clear all widgets from container"""
        for widget in self.container.winfo_children():
            widget.destroy()
    
    def show_welcome(self):
        """Display welcome screen with QR code"""
        self.clear_screen()
        self.current_screen = "welcome"
        
        # Title with fun animation effect
        title = tk.Label(
            self.container,
            text="🎨 Revive Print Kiosk",
            font=('Arial', 48, 'bold'),
            bg='#1a1a2e',
            fg='#a855f7'
        )
        title.pack(pady=50)
        title.bind('<Button-1>', self.secret_click)
        
        # Subtitle
        subtitle = tk.Label(
            self.container,
            text="Scan QR code to upload your document",
            font=('Arial', 24),
            bg='#1a1a2e',
            fg='#22d3ee'
        )
        subtitle.pack(pady=20)
        
        # Generate and display QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(QR_URL)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="#a855f7", back_color="#1a1a2e")
        qr_img = qr_img.resize((400, 400))
        qr_photo = ImageTk.PhotoImage(qr_img)
        
        qr_label = tk.Label(self.container, image=qr_photo, bg='#1a1a2e')
        qr_label.image = qr_photo
        qr_label.pack(pady=30)
        
        # Instructions
        instructions = tk.Label(
            self.container,
            text="upload the file you want to print",
            font=('Arial', 18),
            bg='#1a1a2e',
            fg='#94a3b8'
        )
        instructions.pack(pady=20)
        
        # Status indicator
        status = tk.Label(
            self.container,
            text="● Ready",
            font=('Arial', 16),
            bg='#1a1a2e',
            fg='#22c55e'
        )
        status.pack(pady=10)
        
        # Pulse animation
        self.animate_pulse(status)
    
    def show_file_confirmation(self, filename, filesize):
        """Show file received confirmation"""
        self.clear_screen()
        self.current_screen = "confirmation"
        
        # Success icon
        canvas = tk.Canvas(self.container, width=120, height=120, bg='#1a1a2e', highlightthickness=0)
        canvas.pack(pady=40)
        canvas.create_oval(10, 10, 110, 110, fill='#22c55e', outline='')
        canvas.create_text(60, 60, text='✓', font=('Arial', 60, 'bold'), fill='white')
        
        # Title
        title = tk.Label(
            self.container,
            text="File Received!",
            font=('Arial', 36, 'bold'),
            bg='#1a1a2e',
            fg='#22c55e'
        )
        title.pack(pady=20)
        
        # File info
        info_frame = tk.Frame(self.container, bg='#16213e', relief=tk.RAISED, bd=2)
        info_frame.pack(pady=20, padx=100, fill=tk.X)
        
        tk.Label(
            info_frame,
            text=f"📄 {filename}",
            font=('Arial', 20),
            bg='#16213e',
            fg='#ffffff'
        ).pack(pady=10, padx=20)
        
        tk.Label(
            info_frame,
            text=f"Size: {filesize / 1024:.1f} KB",
            font=('Arial', 16),
            bg='#16213e',
            fg='#94a3b8'
        ).pack(pady=5, padx=20)
        
        # Buttons
        btn_frame = tk.Frame(self.container, bg='#1a1a2e')
        btn_frame.pack(pady=40)
        
        proceed_btn = tk.Button(
            btn_frame,
            text="Proceed to Print",
            font=('Arial', 20, 'bold'),
            bg='#a855f7',
            fg='white',
            activebackground='#9333ea',
            activeforeground='white',
            relief=tk.FLAT,
            padx=40,
            pady=20,
            command=self.show_preview
        )
        proceed_btn.pack(side=tk.LEFT, padx=20)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=('Arial', 20),
            bg='#ef4444',
            fg='white',
            activebackground='#dc2626',
            activeforeground='white',
            relief=tk.FLAT,
            padx=40,
            pady=20,
            command=self.show_welcome
        )
        cancel_btn.pack(side=tk.LEFT, padx=20)
    
    def show_preview(self):
        """Display PDF preview and print options"""
        self.clear_screen()
        self.current_screen = "preview"
        
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "File not found")
            self.show_welcome()
            return
        
        # Generate preview images
        try:
            self.preview_images = convert_from_path(self.current_file, dpi=150)
            self.current_page = 0
        except Exception as e:
            messagebox.showerror("Error", f"Could not preview file: {e}")
            self.show_welcome()
            return
        
        # Left panel - Preview
        left_panel = tk.Frame(self.container, bg='#1a1a2e')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            left_panel,
            text="Preview",
            font=('Arial', 24, 'bold'),
            bg='#1a1a2e',
            fg='#a855f7'
        ).pack(pady=10)
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(left_panel, width=500, height=600, bg='white', relief=tk.SUNKEN, bd=2)
        self.preview_canvas.pack(pady=10)
        
        # Navigation
        nav_frame = tk.Frame(left_panel, bg='#1a1a2e')
        nav_frame.pack(pady=10)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Previous",
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            command=self.prev_page
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.page_label = tk.Label(
            nav_frame,
            text=f"Page 1 of {len(self.preview_images)}",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#94a3b8'
        )
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            command=self.next_page
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Options
        right_panel = tk.Frame(self.container, bg='#16213e', relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(
            right_panel,
            text="Print Options",
            font=('Arial', 24, 'bold'),
            bg='#16213e',
            fg='#a855f7'
        ).pack(pady=20, padx=20)
        
        # Page Range
        tk.Label(
            right_panel,
            text="Page Range:",
            font=('Arial', 16),
            bg='#16213e',
            fg='white'
        ).pack(pady=10, padx=20, anchor='w')
        
        self.page_range_var = tk.StringVar(value='all')
        
        tk.Radiobutton(
            right_panel,
            text="All Pages",
            variable=self.page_range_var,
            value='all',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        range_frame = tk.Frame(right_panel, bg='#16213e')
        range_frame.pack(padx=40, anchor='w', pady=5)
        
        tk.Radiobutton(
            range_frame,
            text="Custom:",
            variable=self.page_range_var,
            value='custom',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(side=tk.LEFT)
        
        self.custom_range = tk.Entry(range_frame, font=('Arial', 14), width=15)
        self.custom_range.pack(side=tk.LEFT, padx=10)
        self.custom_range.insert(0, "e.g. 1-3,5")
        
        # Orientation
        tk.Label(
            right_panel,
            text="Orientation:",
            font=('Arial', 16),
            bg='#16213e',
            fg='white'
        ).pack(pady=10, padx=20, anchor='w')
        
        self.orientation_var = tk.StringVar(value='portrait')
        
        tk.Radiobutton(
            right_panel,
            text="Portrait",
            variable=self.orientation_var,
            value='portrait',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        tk.Radiobutton(
            right_panel,
            text="Landscape",
            variable=self.orientation_var,
            value='landscape',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        # Duplex
        tk.Label(
            right_panel,
            text="Duplex Printing:",
            font=('Arial', 16),
            bg='#16213e',
            fg='white'
        ).pack(pady=10, padx=20, anchor='w')
        
        self.duplex_var = tk.StringVar(value='none')
        
        tk.Radiobutton(
            right_panel,
            text="Single-sided",
            variable=self.duplex_var,
            value='none',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        tk.Radiobutton(
            right_panel,
            text="Long Edge (Book)",
            variable=self.duplex_var,
            value='long',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        tk.Radiobutton(
            right_panel,
            text="Short Edge (Flip)",
            variable=self.duplex_var,
            value='short',
            font=('Arial', 14),
            bg='#16213e',
            fg='white',
            selectcolor='#1a1a2e',
            activebackground='#16213e'
        ).pack(padx=40, anchor='w')
        
        # Action buttons
        btn_frame = tk.Frame(right_panel, bg='#16213e')
        btn_frame.pack(pady=30, padx=20)
        
        tk.Button(
            btn_frame,
            text="🖨️ Print",
            font=('Arial', 18, 'bold'),
            bg='#22c55e',
            fg='white',
            activebackground='#16a34a',
            relief=tk.FLAT,
            padx=30,
            pady=15,
            command=self.start_printing
        ).pack(pady=10, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            font=('Arial', 16),
            bg='#ef4444',
            fg='white',
            activebackground='#dc2626',
            relief=tk.FLAT,
            padx=30,
            pady=10,
            command=self.show_welcome
        ).pack(pady=5, fill=tk.X)
        
        # Show first page
        self.update_preview()
    
    def update_preview(self):
        """Update preview canvas with current page"""
        if not self.preview_images:
            return
        
        img = self.preview_images[self.current_page].copy()
        img.thumbnail((480, 580))
        photo = ImageTk.PhotoImage(img)
        
        self.preview_canvas.delete('all')
        self.preview_canvas.create_image(250, 300, image=photo)
        self.preview_canvas.image = photo
        
        self.page_label.config(text=f"Page {self.current_page + 1} of {len(self.preview_images)}")
        
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < len(self.preview_images) - 1 else tk.DISABLED)
    
    def prev_page(self):
        """Show previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_preview()
    
    def next_page(self):
        """Show next page"""
        if self.current_page < len(self.preview_images) - 1:
            self.current_page += 1
            self.update_preview()
    
    def start_printing(self):
        """Begin print job"""
        # Collect settings
        if self.page_range_var.get() == 'custom':
            page_range = self.custom_range.get()
            if page_range == "e.g. 1-3,5":
                page_range = 'all'
        else:
            page_range = 'all'
        
        self.print_settings = {
            'page_range': page_range,
            'orientation': self.orientation_var.get(),
            'duplex': self.duplex_var.get()
        }
        
        self.show_printing()
        
        # Start printing in background thread
        threading.Thread(target=self.do_print, daemon=True).start()
    
    def show_printing(self):
        """Show printing status screen"""
        self.clear_screen()
        self.current_screen = "printing"
        
        # Status indicator
        self.status_canvas = tk.Canvas(self.container, width=200, height=200, bg='#1a1a2e', highlightthickness=0)
        self.status_canvas.pack(pady=50)
        
        # Spinner
        self.spinner_angle = 0
        self.draw_spinner()
        
        # Status text
        self.status_label = tk.Label(
            self.container,
            text="Preparing document...",
            font=('Arial', 28, 'bold'),
            bg='#1a1a2e',
            fg='#a855f7'
        )
        self.status_label.pack(pady=20)
        
        self.status_detail = tk.Label(
            self.container,
            text="Please wait while we process your print job",
            font=('Arial', 18),
            bg='#1a1a2e',
            fg='#94a3b8'
        )
        self.status_detail.pack(pady=10)
        
        # Progress info
        self.progress_label = tk.Label(
            self.container,
            text="",
            font=('Arial', 16),
            bg='#1a1a2e',
            fg='#22d3ee'
        )
        self.progress_label.pack(pady=20)
    
    def draw_spinner(self):
        """Draw animated spinner"""
        if self.current_screen != "printing":
            return
        
        self.status_canvas.delete('all')
        
        # Draw arc
        self.status_canvas.create_arc(
            50, 50, 150, 150,
            start=self.spinner_angle,
            extent=90,
            outline='#a855f7',
            width=10,
            style=tk.ARC
        )
        
        self.spinner_angle = (self.spinner_angle + 10) % 360
        self.root.after(50, self.draw_spinner)
    
    def do_print(self):
        """Execute print job using CUPS"""
        try:
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Sending to printer..."))
            self.root.after(0, lambda: self.progress_label.config(text="⏳ Communicating with HP LaserJet"))
            
            time.sleep(1)
            
            if not self.cups_conn:
                raise Exception("CUPS connection not available")
            
            # Prepare CUPS options
            options = {}
            
            # Page range
            if self.print_settings['page_range'] != 'all':
                options['page-ranges'] = self.print_settings['page_range']
            
            # Orientation
            if self.print_settings['orientation'] == 'landscape':
                options['orientation-requested'] = '4'
            else:
                options['orientation-requested'] = '3'
            
            # Duplex
            if self.print_settings['duplex'] == 'long':
                options['sides'] = 'two-sided-long-edge'
            elif self.print_settings['duplex'] == 'short':
                options['sides'] = 'two-sided-short-edge'
            else:
                options['sides'] = 'one-sided'
            
            # Submit print job
            job_id = self.cups_conn.printFile(
                PRINTER_NAME,
                self.current_file,
                "Print Job",
                options
            )
            
            self.root.after(0, lambda: self.status_label.config(text="Printing..."))
            self.root.after(0, lambda: self.progress_label.config(text=f"📄 Job ID: {job_id}"))
            
            # Monitor job status
            while True:
                time.sleep(1)
                jobs = self.cups_conn.getJobs()
                if job_id not in jobs:
                    break
                
                job_state = jobs[job_id]['job-state']
                if job_state == 9:  # Completed
                    break
                elif job_state == 8:  # Cancelled
                    raise Exception("Print job cancelled")
            
            # Success!
            self.root.after(0, self.show_success)
            
        except Exception as e:
            print(f"Print error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Print Error", str(e)))
            self.root.after(0, self.show_welcome)
    
    def show_success(self):
        """Show success screen"""
        self.clear_screen()
        self.current_screen = "success"
        
        # Success icon with animation
        canvas = tk.Canvas(self.container, width=200, height=200, bg='#1a1a2e', highlightthickness=0)
        canvas.pack(pady=60)
        canvas.create_oval(20, 20, 180, 180, fill='#22c55e', outline='')
        canvas.create_text(100, 100, text='✓', font=('Arial', 100, 'bold'), fill='white')
        
        # Title
        title = tk.Label(
            self.container,
            text="Print Successful!",
            font=('Arial', 42, 'bold'),
            bg='#1a1a2e',
            fg='#22c55e'
        )
        title.pack(pady=20)
        
        # Message
        msg = tk.Label(
            self.container,
            text="Your document is printing",
            font=('Arial', 24),
            bg='#1a1a2e',
            fg='#94a3b8'
        )
        msg.pack(pady=10)
        
        # Auto-return countdown
        self.countdown = 5
        self.countdown_label = tk.Label(
            self.container,
            text=f"Returning to home in {self.countdown} seconds...",
            font=('Arial', 18),
            bg='#1a1a2e',
            fg='#22d3ee'
        )
        self.countdown_label.pack(pady=30)
        
        self.do_countdown()
    
    def do_countdown(self):
        """Countdown to return home"""
        if self.current_screen != "success":
            return
        
        if self.countdown > 0:
            self.countdown -= 1
            self.countdown_label.config(text=f"Returning to home in {self.countdown} seconds...")
            self.root.after(1000, self.do_countdown)
        else:
            self.show_welcome()
    
    def animate_pulse(self, widget):
        """Create pulse animation for widget"""
        if self.current_screen != "welcome":
            return
        
        colors = ['#22c55e', '#16a34a', '#15803d', '#16a34a']
        current = getattr(widget, 'pulse_index', 0)
        widget.pulse_index = (current + 1) % len(colors)
        widget.config(fg=colors[widget.pulse_index])
        self.root.after(500, lambda: self.animate_pulse(widget))
    
    def check_konami(self, event):
        """Check for Konami code easter egg"""
        key = event.keysym
        if key in ['b', 'a']:
            key = event.char
        
        self.konami_progress.append(key)
        if len(self.konami_progress) > len(KONAMI_CODE):
            self.konami_progress.pop(0)
        
        if self.konami_progress == KONAMI_CODE:
            self.trigger_party_mode()
            self.konami_progress = []
    
    def secret_click(self, event):
        """Secret click counter easter egg"""
        self.secret_clicks += 1
        if self.secret_clicks >= 10:
            self.trigger_party_mode()
            self.secret_clicks = 0
    
    def trigger_party_mode(self):
        """Activate party mode!"""
        party_window = tk.Toplevel(self.root)
        party_window.title("🎉 PARTY MODE! 🎉")
        party_window.geometry("600x400")
        party_window.configure(bg='#1a1a2e')
        
        colors = ['#a855f7', '#22d3ee', '#22c55e', '#f59e0b', '#ef4444']
        
        label = tk.Label(
            party_window,
            text="🎊 YOU FOUND THE SECRET! 🎊",
            font=('Arial', 24, 'bold'),
            bg='#1a1a2e',
            fg='#a855f7'
        )
        label.pack(expand=True)
        
        def flash():
            color = colors[int(time.time() * 5) % len(colors)]
            label.config(fg=color)
            party_window.configure(bg='#1a1a2e' if int(time.time() * 10) % 2 else '#16213e')
            if party_window.winfo_exists():
                party_window.after(100, flash)
        
        flash()
        party_window.after(3000, party_window.destroy)
    
    def start_file_receiver(self):
        """Start Flask server to receive files from web app"""
        app = Flask(__name__)
        
        @app.route('/receive_file', methods=['POST'])
        def receive_file():
            try:
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'Empty filename'}), 400
                
                # Save file
                temp_dir = tempfile.gettempdir()
                filepath = os.path.join(temp_dir, f"print_{int(time.time())}_{file.filename}")
                file.save(filepath)
                
                # Get file info
                filesize = os.path.getsize(filepath)
                
                # Update UI on main thread
                self.current_file = filepath
                self.root.after(0, lambda: self.show_file_confirmation(file.filename, filesize))
                
                return jsonify({
                    'success': True,
                    'message': 'File received',
                    'filename': file.filename
                })
                
            except Exception as e:
                print(f"Error receiving file: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # Run Flask in background thread
        def run_server():
            app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print("File receiver started on port 5001")
    
    def cleanup(self):
        """Cleanup on exit"""
        if self.current_file and os.path.exists(self.current_file):
            try:
                os.remove(self.current_file)
            except:
                pass


def main():
    root = tk.Tk()
    app = PrintKiosk(root)
    
    # Handle window close
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Exit fullscreen with Escape
    root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))
    
    root.mainloop()


if __name__ == "__main__":
    main()
