import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

ok, argv = Gtk.init_check()
if not ok:
    print("GTK not available (no display/session).")
    sys.exit(2)

import sys
import os

class ReminderWindow(Gtk.Window):
    def __init__(self, content):
        super().__init__(title="Reminder")
        self.set_border_width(10)
        self.set_default_size(400, 300)

        # Main layout container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Text view for content
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        
        # Set text content
        text_buffer = self.text_view.get_buffer()
        text_buffer.set_text(content)
        
        # Styling (mimicking the previous colors roughly if possible, but keeping it standard GTK for now
        # or using CSS providers if strictly needed. For now, standard GTK is safer and cleaner)
        # To strictly match the previous bg="#E64A19", we'd need a CssProvider. 
        # I will stick to standard GTK for simplicity unless requested otherwise, 
        # but I will add the text view to a scrolled window just in case.
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.text_view)
        
        vbox.pack_start(scrolled_window, True, True, 0)

        # Acknowledge button
        self.button = Gtk.Button(label="Acknowledge")
        self.button.connect("clicked", self.on_acknowledge_clicked)
        vbox.pack_start(self.button, False, False, 0)

    def on_acknowledge_clicked(self, widget):
        Gtk.main_quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python display_reminder.py <file_content>")
        sys.exit(1)

    file_content = sys.argv[1]

    win = ReminderWindow(file_content)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
