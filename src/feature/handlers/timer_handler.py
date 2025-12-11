class TimerFeatureHandler:
    def __init__(self, timer_manager):
        self.timer_manager = timer_manager

    def toggle_timer(self, **kwargs):
        if self.timer_manager is None:
            print(f"DEBUG: TimerManager is None in toggle_timer. self.timer_manager={self.timer_manager}")
            raise Exception("TimerManager not configured")
        
        print(f"DEBUG: Toggling timer. Manager: {self.timer_manager}")
        running = self.timer_manager.toggle()
        state = "START" if running else "STOP"
        print(f"Timer state: {state}")

    def pause_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.pause()
            print("Timer paused")

    def resume_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.resume()
            print("Timer resumed")

    def stop_timer(self, **kwargs):
        if self.timer_manager:
            self.timer_manager.stop_and_persist()
            print("Timer stopped and saved")
