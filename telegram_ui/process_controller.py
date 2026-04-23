
import os
import signal
import subprocess
import sys
import time

class BotProcessController:
    def __init__(self):
        self.process = None
        self.pid = None
        self.pid_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.bot_process.pid')
        self._load_pid_from_file()

    def _pid_is_alive(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _save_pid_to_file(self, pid):
        with open(self.pid_file, 'w', encoding='utf-8') as pid_handle:
            pid_handle.write(str(pid))

    def _clear_pid_file(self):
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)

    def _load_pid_from_file(self):
        if not os.path.exists(self.pid_file):
            return

        try:
            with open(self.pid_file, 'r', encoding='utf-8') as pid_handle:
                pid_value = int(pid_handle.read().strip())
            if self._pid_is_alive(pid_value):
                self.pid = pid_value
                return
        except (OSError, ValueError):
            pass

        self.pid = None
        self._clear_pid_file()

    def _cleanup_dead_state(self):
        self.process = None
        self.pid = None
        self._clear_pid_file()

    def _running_pid(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.pid = self.process.pid
                return self.pid
            self._cleanup_dead_state()
            return None

        if self.pid is None:
            return None

        if self._pid_is_alive(self.pid):
            return self.pid

        self._cleanup_dead_state()
        return None

    def is_running(self):
        return self._running_pid() is not None

    def _terminate_by_pid(self, pid):
        if os.name == 'nt':
            os.kill(pid, signal.SIGTERM)
        else:
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                os.kill(pid, signal.SIGTERM)

        deadline = time.time() + 8
        while time.time() < deadline:
            if not self._pid_is_alive(pid):
                return
            time.sleep(0.2)

        hard_signal = getattr(signal, 'SIGKILL', signal.SIGTERM)
        if os.name == 'nt':
            os.kill(pid, hard_signal)
        else:
            try:
                os.killpg(pid, hard_signal)
            except OSError:
                os.kill(pid, hard_signal)

    def start(self, mode='normal'):
        running_pid = self._running_pid()
        if running_pid is not None:
            return False, f'Скрипт уже запущен (PID {running_pid}).'

        bot_script_path = os.path.abspath(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot.py')
        )
        command = [sys.executable, bot_script_path]

        popen_kwargs = {'cwd': os.path.dirname(bot_script_path)}
        if os.name != 'nt':
            popen_kwargs['start_new_session'] = True

        self.process = subprocess.Popen(command, **popen_kwargs)
        self.pid = self.process.pid
        self._save_pid_to_file(self.pid)
        return True, f'Скрипт запущен (PID {self.pid}).'

    def stop(self):
        running_pid = self._running_pid()
        if running_pid is None:
            return False, 'Скрипт уже остановлен.'

        try:
            if self.process is not None and self.process.poll() is None:
                if os.name == 'nt':
                    self.process.terminate()
                else:
                    os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=8)
            else:
                self._terminate_by_pid(running_pid)
        except (subprocess.TimeoutExpired, OSError):
            pass

        self._cleanup_dead_state()
        return True, 'Скрипт остановлен.'

    def status(self):
        running_pid = self._running_pid()
        if running_pid is not None:
            return f'Статус: работает (PID {running_pid}).'
        return 'Статус: остановлен.'

    def consume_exit_event(self):
        if self.process is not None:
            return_code = self.process.poll()
            if return_code is None:
                return None

            pid = self.process.pid
            self._cleanup_dead_state()
            return f'Скрипт завершился (PID {pid}, код {return_code}).'

        if self.pid is None:
            return None

        if self._pid_is_alive(self.pid):
            return None

        pid = self.pid
        self._cleanup_dead_state()
        return f'Скрипт завершился (PID {pid}).'
