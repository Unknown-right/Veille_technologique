import customtkinter as ctk
import threading
import webbrowser
import queue
from datetime import datetime
from src.utils.scheduler import WatchdogScheduler
from src.storage.json_handler import JSONHandler

class AppWindow:
    def __init__(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("IoT Security Watchdog")
        self.root.geometry("1100x700")

        self.setup_ui()
        
        self.msg_queue = queue.Queue()
        self.root.after(100, self.process_queue)

        self.scheduler = WatchdogScheduler(self.on_new_item_found, self.on_report_generated)
        self.json_handler = JSONHandler()

    def setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self.root, height=60)
        self.header_frame.pack(fill="x", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="IoT Security Watchdog", 
            font=("Roboto", 24, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        self.export_btn = ctk.CTkButton(
            self.header_frame, 
            text="Export to JSON", 
            command=self.export_data,
            fg_color="#2ecc71", 
            hover_color="#27ae60"
        )
        self.export_btn.pack(side="right", padx=20)

        # Main Content - Tabview for Categories
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs = {
            "operational_alerts": self.tabview.add("Alerts (CERT/Ops)"),
            "institutional_standards": self.tabview.add("Standards (ANSSI/NIST)"),
            "research_academic": self.tabview.add("Research (IEEE)"),
            "sensors_devices": self.tabview.add("Sensors & Devices"),
            "network_transit": self.tabview.add("Network & Transit"),
            "destination_storage": self.tabview.add("Destination & Storage"),
            "all": self.tabview.add("All Feed"),
            "filtered": self.tabview.add("Filtered (Noise)"),
            "report": self.tabview.add("Daily Analysis (Gemini)")
        }

        # Create scrollable frames for each tab
        self.scroll_frames = {}
        for key, tab in self.tabs.items():
            if key == "report":
                continue
            scroll_frame = ctk.CTkScrollableFrame(tab, label_text=f"Latest News - {key.replace('_', ' ').title()}")
            scroll_frame.pack(fill="both", expand=True)
            self.scroll_frames[key] = scroll_frame

        # Setup Report Tab
        self.report_textbox = ctk.CTkTextbox(self.tabs["report"], font=("Consolas", 14))
        self.report_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.report_textbox.insert("0.0", "Waiting for data collection cycle to generate report...\n(Ensure GEMINI_API_KEY is set in .env)")
        self.report_textbox.configure(state="disabled")

        # Status Bar
        self.status_bar = ctk.CTkLabel(self.root, text="System Ready", font=("Arial", 12))
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
    def on_new_item_found(self, item):
        """Callback when a new item is found by the collector thread"""
        self.msg_queue.put(('ITEM', item))

    def on_report_generated(self, report_text):
        """Callback when a report is generated"""
        self.msg_queue.put(('REPORT', report_text))

    def process_queue(self):
        """Check queue for new items and update UI in the main thread"""
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == 'ITEM':
                    self._update_ui_with_item(data)
                elif msg_type == 'REPORT':
                    self._update_report_tab(data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def _update_report_tab(self, report_text):
        self.report_textbox.configure(state="normal")
        self.report_textbox.delete("0.0", "end")
        self.report_textbox.insert("0.0", f"--- REPORT GENERATED AT {datetime.now().strftime('%H:%M:%S')} ---\n\n")
        self.report_textbox.insert("end", report_text)
        self.report_textbox.configure(state="disabled")
        
        # Switch to report tab to notify user
        self.tabview.set("Daily Analysis (Gemini)")

    def _update_ui_with_item(self, item):
        category = item.get('category', 'all')
        status = item.get('status', 'accepted')

        if status == 'rejected':
            # Only add to Filtered tab
            self.create_news_card(self.scroll_frames['filtered'], item, is_rejected=True)
        else:
            # Accepted items go to standard tabs
            # Add to 'All' tab
            self.create_news_card(self.scroll_frames['all'], item)
            
            # Add to specific category tab
            if category in self.scroll_frames:
                self.create_news_card(self.scroll_frames[category], item)

        # Update Status
        self.status_bar.configure(text=f"Last update: {datetime.now().strftime('%H:%M:%S')} - Found: {item['title'][:30]}...")

        # Auto-save to JSON (Append mode)
        # We might want to save rejected items too for debugging, or filter them out of storage
        self.json_handler.append_item(item)

    def create_news_card(self, parent_frame, item, is_rejected=False):
        # Different styling for rejected items
        card_color = "#333333" if is_rejected else None # Darker gray for noise
        title_color = "#999999" if is_rejected else None # Dimmed title

        card = ctk.CTkFrame(parent_frame, fg_color=card_color)
        card.pack(fill="x", padx=5, pady=5)

        # Title
        title_lbl = ctk.CTkLabel(
            card, 
            text=item['title'], 
            font=("Arial", 16, "bold"), 
            anchor="w",
            wraplength=800,
            text_color=title_color
        )
        title_lbl.pack(fill="x", padx=10, pady=(10, 2))

        # Meta info
        meta_text = f"Source: {item['source']} | Date: {item['date']}"
        if is_rejected:
            meta_text = "[FILTERED NOISE] " + meta_text
            
        meta_lbl = ctk.CTkLabel(card, text=meta_text, font=("Arial", 12), text_color="gray", anchor="w")
        meta_lbl.pack(fill="x", padx=10, pady=0)

        # Link Button
        link_btn = ctk.CTkButton(
            card, 
            text="Open Link", 
            font=("Arial", 12),
            height=25,
            width=80,
            fg_color="#555555" if is_rejected else None, # Dimmed button
            hover_color="#777777" if is_rejected else None,
            command=lambda url=item['link']: webbrowser.open(url)
        )
        link_btn.pack(side="right", padx=10, pady=10)

        # Content Button (New)
        if item.get('content') and not is_rejected:
            content_btn = ctk.CTkButton(
                card, 
                text="View Content", 
                font=("Arial", 12),
                height=25,
                width=100,
                command=lambda i=item: self.show_content_popup(i)
            )
            content_btn.pack(side="right", padx=5, pady=10)

    def show_content_popup(self, item):
        popup = ctk.CTkToplevel(self.root)
        popup.title(f"Content: {item.get('title', 'Unknown')}")
        popup.geometry("800x600")
        
        textbox = ctk.CTkTextbox(popup, font=("Consolas", 14))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", item.get('content', 'No content available.'))
        textbox.configure(state="disabled")

    def export_data(self):

        saved_path = self.json_handler.get_file_path()
        self.status_bar.configure(text=f"Data exported successfully to {saved_path}")

    def start(self):
        # Start the scheduler in a background thread
        threading.Thread(target=self.scheduler.run_continuously, daemon=True).start()
        self.root.mainloop()
