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

        self.scheduler = WatchdogScheduler(self.on_new_item_found)
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
            "sensors_devices": self.tabview.add("Sensors & Devices"),
            "network_transit": self.tabview.add("Network & Transit"),
            "destination_storage": self.tabview.add("Destination & Storage"),
            "all": self.tabview.add("All Feed"),
            "filtered": self.tabview.add("Filtered (Noise)")
        }

        # Create scrollable frames for each tab
        self.scroll_frames = {}
        for key, tab in self.tabs.items():
            scroll_frame = ctk.CTkScrollableFrame(tab, label_text=f"Latest News - {key.replace('_', ' ').title()}")
            scroll_frame.pack(fill="both", expand=True)
            self.scroll_frames[key] = scroll_frame

        # Status Bar
        self.status_bar = ctk.CTkLabel(self.root, text="System Ready", font=("Arial", 12))
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
    def on_new_item_found(self, item):
        """Callback when a new item is found by the collector thread"""
        self.msg_queue.put(item)

    def process_queue(self):
        """Check queue for new items and update UI in the main thread"""
        try:
            while True:
                item = self.msg_queue.get_nowait()
                self._update_ui_with_item(item)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

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
            text="Read Article", 
            font=("Arial", 12),
            height=25,
            width=100,
            fg_color="#555555" if is_rejected else None, # Dimmed button
            hover_color="#777777" if is_rejected else None,
            command=lambda url=item['link']: webbrowser.open(url)
        )
        link_btn.pack(side="right", padx=10, pady=10)

    def export_data(self):
        saved_path = self.json_handler.get_file_path()
        self.status_bar.configure(text=f"Data exported successfully to {saved_path}")

    def start(self):
        # Start the scheduler in a background thread
        threading.Thread(target=self.scheduler.run_continuously, daemon=True).start()
        self.root.mainloop()
