import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk
from gi.repository import AppIndicator3 as AppIndicator

def main():
    appindicator_id = 'LinShutdownTray'
    icon = "Images/power-on-white.png"
    icon_path = os.path.join(os.path.dirname(__file__), icon)
    indicator = AppIndicator.Indicator.new(
        appindicator_id,
        icon,
        AppIndicator.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
    # indicator.set_menu(menu())

    Gtk.main()

# def menu():
#     menu = Gtk.Menu()
#
#     # command_one = gtk.MenuItem('My Notes')
#     # command_one.connect('activate', note)
#     # menu.append(command_one)
#
#     AppClose = Gtk.MenuItem('Close')
#     AppClose.connect('activate', quit)
#     menu.append(AppClose)
#
#     menu.show_all()
#     return menu

if __name__ == "__main__":
    main()
