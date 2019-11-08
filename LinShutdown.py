__author__ = 'WutDuk? https://github.com/jcemerson'
__date__ = '20191104'
__version__ = '1.1'
__description__ = """
    The Linux version of WinShutdown.
"""


# import sys
import os
import json
import ast
import kivy
from kivy import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty
from kivy.properties import ListProperty
from kivy.clock import Clock
# import tray as systray


# Supported Kivy version required for operation. Older version may work too,
# but they're not supported. You can remove or modify this setting at your own
# risk.
kivy.require('1.10.1')

# Set config.ini setting for this instance of the app only
# (as opposed to writing to the file which would impact ALL Kivy apps)
Config.set(
    'graphics',
    'fullscreen',
    0,
)
Config.set(
    'graphics',
    'resizable',
    0,
)
Config.set(
    'kivy',
    'exit_on_escape',
    0,
)
Config.set(
    'kivy',
    'window_icon',
    './Images/power-on-white.png'
)


# Import Window for Keybindings functionality -- When placed before config,
# Kivy would flicker during loading. Relocated lower in the process to ensure
# Window is loaded AFTER initial config is defined
from kivy.core.window import Window
Window.size = (800, 600)
Window.fullscreen = False


# Set the path to the user settings file:
file_path = os.path.dirname(os.path.realpath(__file__))
filename = 'user_settings.json'
user_settings_file = file_path + '/' + filename


# Class defining popup presented when User forces countdown to 0
class ImminentPopup(Popup):

    label_text = StringProperty('')

    def __init__(self, cmd):
        super(ImminentPopup, self).__init__()
        self.title = f'Imminent {cmd}!'
        self.label_text = f"""By forcing an active countdown to 00:00:00 you are about to initiate an [i][b]imminent {cmd}[/b][/i].\n\nDo you wish to continue?"""


# Class defining popup presented when final command is sent prior to the
# App auto-closing
class FinalPopup(Popup):

    countdown = NumericProperty(5.9)

    def __init__(self):
        super(FinalPopup, self).__init__()

    # Function to start the countdown to App auto-closing
    def start_final_timer(self):
        Animation.cancel_all(self)
        self.anim = Animation(countdown=0, duration=self.countdown)
        self.anim.bind(on_complete=App.get_running_app().stop)
        # self.anim.bind(on_complete = App.get_running_app().root.close_systray)
        self.anim.start(self)


# Main Class defining overall functions of the App
class LinShutdownTimer(GridLayout, ToggleButtonBehavior):
    # Define default layout attributes
    font_size = 20
    widget_padding = (25, 10, 25, 10)
    spacer_width = 10
    abort_disabled = BooleanProperty(True)
    abort_background_color = ListProperty([1, 1, 1, 1])
    popup_active = BooleanProperty(False)
    # Define default cmd button attributes
    shutdown_btn_disabled = BooleanProperty(False)
    shutdown_btn_state = StringProperty('normal')
    restart_btn_disabled = BooleanProperty(False)
    restart_btn_state = StringProperty('normal')
    suspend_btn_disabled = BooleanProperty(False)
    suspend_btn_state = StringProperty('normal')
    logoff_btn_disabled = BooleanProperty(False)
    logoff_btn_state = StringProperty('normal')
    # Define default time button attributes
    set20_disabled = BooleanProperty(False)
    set20_state = StringProperty('normal')
    set40_disabled = BooleanProperty(False)
    set40_state = StringProperty('normal')
    set60_disabled = BooleanProperty(False)
    set60_state = StringProperty('normal')
    set90_disabled = BooleanProperty(False)
    set90_state = StringProperty('normal')
    set120_disabled = BooleanProperty(False)
    set120_state = StringProperty('normal')
    preset_status = BooleanProperty(True)
    preset_keybinding_enabled = BooleanProperty(True)

    sub_time_disabled = BooleanProperty(True)
    add_time_disabled = BooleanProperty(False)

    countdown = NumericProperty(0)

    start_pause = StringProperty('Start')
    start_pause_disabled = BooleanProperty(True)

    # Retrieve default settings if the file exists, else create the file and
    # set defaults
    try:
        with open(user_settings_file, 'r') as f:
            user_settings = ast.literal_eval(f.read())
    except FileNotFoundError:
        user_settings = {
            'default_cmd': 'shutdown',
            'default_time': 'set20',
        }
        with open(user_settings_file, 'w+') as f:
            json.dump(user_settings, f, indent=4)


    def __init__(self):
        super(LinShutdownTimer, self).__init__()
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


    def apply_defaults(self):
        default_cmd = self.user_settings['default_cmd']
        default_time = self.user_settings['default_time']

        if default_cmd == 'shutdown':
            self.shutdown_btn_state = 'down'
        elif default_cmd == 'restart':
            self.restart_btn_state = 'down'
        elif default_cmd == 'suspend':
            self.suspend_btn_state = 'down'
        elif default_cmd == 'log off':
            self.logoff_btn_state = 'down'

        if default_time == 'set20':
            self.set20_state = 'down'
            self.countdown = 20*60
        elif default_time == 'set40':
            self.set40_state = 'down'
            self.countdown = 40*60
        elif default_time == 'set60':
            self.set60_state = 'down'
            self.countdown = 60*60
        elif default_time == 'set90':
            self.set90_state = 'down'
            self.countdown = 90*60
        elif default_time == 'set120':
            self.set120_state = 'down'
            self.countdown = 120*60

        self.start_pause_disabled = False
        self.sub_time_disabled = False


    # Function to get the current cmd value
    def get_cmd(self):
        if self.ids.shutdown.state == 'down':
            self.cmd = 'Shutdown'
        elif self.ids.restart.state == 'down':
            self.cmd = 'Restart'
        elif self.ids.suspend.state == 'down':
            self.cmd = 'Suspend'
        elif self.ids.logoff.state == 'down':
            self.cmd = 'Log Off'
        return self.cmd


    # Function to get the current time value
    def get_time(self):
        if self.ids.set20.state == 'down':
            self.time = 'set20'
        elif self.ids.set40.state == 'down':
            self.time = 'set40'
        elif self.ids.set60.state == 'down':
            self.time = 'set60'
        elif self.ids.set90.state == 'down':
            self.time = 'set90'
        elif self.ids.set120.state == 'down':
            self.time = 'set120'
        return self.time


    def set_app_settings(self):
        with open(user_settings_file, 'w') as f:
            json.dump(self.user_settings, f, indent=4)


    def get_curr_settings(self):
        self.user_settings['default_cmd'] = self.get_cmd().lower()
        self.user_settings['default_time'] = self.get_time()


    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.preset_keybinding_enabled == True:
            # cmd buttons
            if keycode[0] == 115:
                self.ids.shutdown.trigger_action(0)
            elif keycode[0] == 114:
                self.ids.restart.trigger_action(0)
            elif keycode[0] == 112:
                self.ids.suspend.trigger_action(0)
            elif keycode[0] == 108:
                self.ids.logoff.trigger_action(0)
            # preset duration buttons
            elif keycode[0] in (50, 258):
                self.ids.set20.trigger_action(0)
            elif keycode[0] in (52, 260):
                self.ids.set40.trigger_action(0)
            elif keycode[0] in (54, 262):
                self.ids.set60.trigger_action(0)
            elif keycode[0] in (57, 265):
                self.ids.set90.trigger_action(0)
            elif keycode[0] in (49, 257):
                self.ids.set120.trigger_action(0)

        # subtract time / add time buttons
        if self.sub_time_disabled == False:
            if keycode[0] in (45, 269, 274, 276):
                self.ids.minus15.trigger_action(0)

        if self.add_time_disabled == False:
            if keycode[0] in (61, 270, 273, 275):
                self.ids.plus15.trigger_action(0)

        # If there's no active popup, then
        if self.popup_active == False:
            # Start/Stop buttons
            if self.countdown > 0 and self.start_pause_disabled == False:
                if keycode[0] in (13, 16, 32, 271):
                    self.ids.start_pause.trigger_action(0)

            # Abort button
            if  self.abort_disabled == False:
                if keycode[0] == 97:
                    self.ids.abort.trigger_action(0)

        # If there is an active popop, then
        if self.popup_active == True:
            # ImminentPopup Yes/No buttons
            if keycode[0] == 121:
                self.imminent_popup.ids.yes.trigger_action(0)
            elif keycode[0] == 110:
                self.imminent_popup.ids.no.trigger_action(0)


    def toggle_keybinding_allowed(self):
        if self.ids.start_pause.state == 'down':
            self.preset_keybinding_enabled = False
        else:
            self.preset_keybinding_enabled = True


    # Function called when countdown reaches 0 to execute the selected
    # cmd from the cmd_group togglebuttons
    def initiate_shutdown(self, *args):
        # Custom message to display on screen.
        # wall_cmd = '/c "Automated User-initiated {cmd} via LinShutdown"'
        # build final cmd
        final_cmd = ''
        # If the Start/Pause button is down (should say 'Pause') and the countdown is at 0, then
        if self.countdown == 0:
            # If the Shutdown button is down, then
            if self.cmd == 'Shutdown':
                # Compile the cmd string for a shutdown
                final_cmd = 'systemctl poweroff'
            # Else, if the Restart button is down, then
            elif self.cmd == 'Restart':
                # Compile the cmd string for a restart
                final_cmd = 'systemctl reboot'
            # Else, if the Suspend button is down, then
            elif self.cmd == 'Suspend':
                # Compile the cmd string for suspend
                final_cmd = 'systemctl suspend'
            # Else, if the Log Off button is down, then
            elif self.cmd == 'logoff':
                # Compile the cmd string for log off
                final_cmd = 'gnome-session-quit --force'
            # Instantiate and open the final popup then start final timer
            self.final_popup = FinalPopup()
            self.final_popup.open()
            self.popup_active = True
            self.final_popup.start_final_timer()
            # send final cmd to command shell
            os.system(final_cmd)


    # Function to set the countdown timer. This doesn't add time.
    # Instead it replaces time.
    def set_timer(self, button_time):
        # If the countdown is at 0, then
        if self.countdown == 0:
            # Then set the countdown to the time of the button that
            # initiated the call
            self.countdown = button_time


    # Function to clear the timer to 0
    def clear_timer(self):
        self.countdown = 0


    # Function to toggle the '-15 min' button's state
    def toggle_sub_time_status(self):
        # If the countdown is less than 15 minutes, then
        if self.countdown < 15 * 60:
            # The '-15 min' button is disabled because there's
            # no time to subtract
            self.sub_time_disabled = True
        # Otherwise, the button is active
        else:
            self.sub_time_disabled = False


    # Fucntion to toggle the '+ 15 min' button status
    def toggle_add_time_status(self):
        # If '+ 15 min' button is not disabled, set to disabled
        if self.add_time_disabled == False:
            self.add_time_disabled = True
        # Else, if countdown is 0 and '+ 15 min' button is disabled,
        # make it active
        elif self.countdown == 0 or self.add_time_disabled == True:
            self.add_time_disabled = False


    # Function to toggle the Start/Pause button status
    def toggle_start_pause_status(self):
        # If the countdown is greater than 0
        if self.countdown > 0:
            # The Start/Pause button is active and can be clicked
            self.start_pause_disabled = False
        else:
            # Otherwise the timer is at 0 and there's no function for
            # this button, so it's disabled
            self.start_pause_disabled = True


    # Function to toggle the Abort button state
    def toggle_abort_status(self):
        # If countdown is greater than 0 and the Start/Pause button
        # is down, then
        if self.countdown > 0 and self.ids.start_pause.state == 'down':
            # The Abort button is active, and colored red
            self.abort_disabled = False
            self.abort_background_color = [1, 0, 0, 1]
        # Else the button is disabled and returns to default gray
        else:
            self.abort_disabled = True
            self.abort_background_color = [1, 1, 1, 1]


    # Function to toggle the status of preset cmd buttons
    # (20, 40, 60, 90, 120)
    def toggle_cmd_status(self):
        # If the Start/Pause button is down (countdown is active), then
        if self.ids.start_pause.state == 'down':
            # Then preset cmd buttons are down. To apply a preset, Pause or
            # Abort the countdown.
            self.preset_status = True
        # Otherwise they are available and can be selected at any time
        else:
            self.preset_status = False
        self.shutdown_btn_disabled = self.preset_status
        self.restart_btn_disabled = self.preset_status
        self.suspend_btn_disabled = self.preset_status
        self.logoff_btn_disabled = self.preset_status


    # Function to toggle the status of preset time buttons
    # (20, 40, 60, 90, 120)
    def toggle_preset_status(self):
        # If the Start/Pause button is down (countdown is active), then
        if self.ids.start_pause.state == 'down':
            # Then preset time buttons are down. To apply a preset, Pause or
            # Abort the countdown.
            self.preset_status = True
        # Otherwise they are available and can be selected at any time
        else:
            self.preset_status = False
        self.set20_disabled = self.preset_status
        self.set40_disabled = self.preset_status
        self.set60_disabled = self.preset_status
        self.set90_disabled = self.preset_status
        self.set120_disabled = self.preset_status


    # Function to toggle the Start/Pause button state (up or down)
    def toggle_start_pause_state(self):
        # If Start/Pause says 'Start', then
        if self.start_pause == 'Start':
            # Set the button to 'up'
            self.ids.start_pause.state = 'normal'
        # Else the button is down
        else:
            self.ids.start_pause.state = 'down'


    # Function to toggle the state of presets (up or down)
    def toggle_preset_state(self):
        # If countdown is at 0, the presets are in the 'up' state
        if self.countdown == 0:
            self.ids.set20.state = 'normal'
            self.ids.set40.state = 'normal'
            self.ids.set60.state = 'normal'
            self.ids.set90.state = 'normal'
            self.ids.set120.state = 'normal'


    # Function to toggle the state cmd buttons (up or down)
    def toggle_cmd_state(self):
        self.ids.shutdown.state = 'normal'
        self.ids.restart.state = 'normal'
        self.ids.suspend.state = 'normal'
        self.ids.logoff.state = 'normal'


    # Function to toggle the Start/Pause text label of the button
    def toggle_start_pause_text(self):
        # If the Start/Pause button is down and the countdown is above 0, then
        if self.ids.start_pause.state == 'down' and self.countdown > 0:
            # The countdown is active, so set the button text to 'Pause'
            self.start_pause = 'Pause'
        # Else, set the text to 'Start'
        else:
            self.start_pause = 'Start'


    def start_stop_timer(self):
        # Get current cmd value
        self.get_cmd()
        # Cancel any current animation in progress
        Animation.cancel_all(self)
        # Define the rules for Animation; i.e., (where we are going, where
        # we're coming from)
        self.anim = Animation(
            countdown=0,
            duration=self.countdown,
        )
        # on_release of Start/Pause button, if the down and there is still
        # time on the clock, then
        if self.ids.start_pause.state == 'down' and self.countdown > 0:
            # On completion of the countdown, call function to initiate the
            # shutdown process
            self.anim.bind(on_complete=self.initiate_shutdown)
            # Start the animation
            self.anim.start(self)


    # Function to add time to the current countdown (as opposed to resetting)
    # v1.1 introduced the ability to edit a live countdown, so Start/Pause
    # state is no longer checked
    def add_time(self, button_time):
        # The timer must be stopped in order to add time
        self.start_stop_timer()
        # Add to the current countdown time the time of the button that
        # initiated the call
        self.countdown += button_time
        # The timer is then restarted again
        self.start_stop_timer()


    # Function to subtract time from the current countdown (as opposed to
    # resetting)
    def sub_time(self, button_time):
        # If subtracting time would set the countdown to 0 or less, then
        if button_time >= self.countdown:
            # If the Start/Pause button is 'down', then
            if self.ids.start_pause.state == 'down':
                # Instantiate ImminentPopup
                self.imminent_popup = ImminentPopup(self.cmd)
                # Toggle '+ 15 min' button status
                self.toggle_add_time_status()
                # Disable '- 15 min button'
                self.sub_time_disabled = True
                # Stop the countdown, then
                Animation.cancel_all(self)
                # Call the pop-up to notify User of imminent shutdown,
                # restart, etc.
                self.imminent_popup.open()
                self.popup_active = True
            # Else, Start/Pause is 'normal' and the countdown isn't active, so
            else:
                # Set the countdown to 0
                self.countdown = 0
                # Disable '- 15 min' button
                self.sub_time_disabled = True
        # Else, the timer will remain above 0, so
        else:
            # The timer must be stopped in order to add time, then
            self.start_stop_timer()
            # Subtract from the current countdown time the time of the button
            # that initiated the call
            self.countdown -= button_time
            # The timer is then restarted again
            self.start_stop_timer()


    # Function to initiate shutdown on 'Yes' response to pop-up
    def popup_yes(self):
        self.countdown = 0
        self.initiate_shutdown()
        self.popup_active = False


    # Function to dismiss the pop-up and restart the countdown
    def popup_no(self):
        self.anim.start(self)
        self.toggle_add_time_status()
        self.sub_time_disabled = False
        self.popup_active = False


    # Function to reset the entire app
    def reset(self):
        Animation.cancel_all(self),
        self.clear_timer(),
        self.toggle_start_pause_status(),
        self.toggle_start_pause_text(),
        self.toggle_start_pause_state(),
        self.toggle_preset_status(),
        self.toggle_cmd_status(),
        self.toggle_sub_time_status(),
        self.toggle_abort_status(),
        self.toggle_keybinding_allowed(),
        self.apply_defaults()
        #, self.toggle_preset_state()


# App class that, when called, instatiates the root class
class LinShutdownApp(App):

    def build(self):
        shutdown_timer = LinShutdownTimer()
        # shutdown_timer.systray.main()
        shutdown_timer.apply_defaults()
        return shutdown_timer


#Instantiate top-level/root widget and run it
if __name__ == "__main__":
    LinShutdownApp().run()
