from .connector import Connector
from ..exception import DeviceError, ADBError
from ..proto import ResourceType
from loguru import logger
import subprocess
import re

try:
    from shlex import quote  # Python 3
except ImportError:
    from pipes import quote  # Python 2


class ADB(Connector):
    def __init__(self, device=None):
        from ..device import Device
        if isinstance(device, Device):
            self.serial = device.serial
        else:
            raise DeviceError
        self.cmd_prefix = ['adb', "-s", device.serial]

    def run_cmd(self, extra_args):
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if not isinstance(extra_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise ADBError(msg)

        args = [] + self.cmd_prefix
        args += extra_args

        logger.debug('command:')
        logger.debug(args)
        r = subprocess.check_output(args).strip()
        if not isinstance(r, str):
            r = r.decode()
        logger.debug('return:')
        logger.debug(r)
        return r

    def shell(self, extra_args):
        pass

    def shell_grep(self, extra_args, grep_args):
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if isinstance(grep_args, str):
            grep_args = grep_args.split()
        if not isinstance(extra_args, list) or not isinstance(grep_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise ADBError(msg)

        args = self.cmd_prefix + ['shell'] + [quote(arg) for arg in extra_args]
        grep_args = ['grep'] + [quote(arg) for arg in grep_args]

        proc1 = subprocess.Popen(args, stdout=subprocess.PIPE)
        proc2 = subprocess.Popen(grep_args, stdin=proc1.stdout,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        proc1.stdout.close()  # Allow proc1 to receive a SIGPIPE if proc2 exits.
        out, err = proc2.communicate()
        if not isinstance(out, str):
            out = out.decode()
        return out

    def current_ability(self):
        focus_lines = self.shell_grep("dumpsys window", "mCurrentFocus").splitlines()
        infos_re = re.compile(".*u0 (.*)/(.*)}")
        if len(focus_lines) > 0:
            for focus_line in focus_lines:
                m = infos_re.match(focus_line)
                if m:
                    return {
                        'app': m.groups()[0],
                        'ability': m.groups()[1],
                        'bundle': m.groups()[0],
                    }
        return {}

    def get_uid(self):
        bundle = self.current_ability().get('bundle')
        process_lines = self.shell_grep("ps", bundle).splitlines()
        if len(process_lines) > 0:
            usr_name = process_lines[0].split()[0]
            uid = str(int(usr_name.split('_a')[1]) + 10000)
            return uid
        else:
            return

    def get_resource_status(self):
        return {
            ResourceType.AUDIO: self.get_audio_status(),
            ResourceType.CAMERA: self.get_camera_status(),
            ResourceType.MICRO: self.get_micro_status(),
            ResourceType.KEYBOARD: self.get_keyboard_status()
        }

    def get_audio_status(self):
        audio_lines = self.shell_grep("dumpsys audio", "AudioPlaybackConfiguration").splitlines()
        audio_line_re = re.compile(".*u/pid:(.*)/(.*) .*state:(.*) attr.*")
        audio_status_dict = {}
        started_count = 0
        for audio_line in audio_lines:
            m = audio_line_re.match(audio_line)
            if m:
                uid = m.group(1)
                pid = m.group(2)
                status = m.group(3)
                audio_status_dict[(uid, pid)] = status
                if status == 'started':
                    started_count += 1
        req_focus_lines = self.shell_grep("dumpsys audio", "requestAudioFocus").splitlines()
        req_focus_line_re = re.compile(".*uid/pid (\d*)/(\d*) .*clientId=(.*) callingPack=.*")
        client_dict = {}
        started_count = 0
        for req_focus_line in req_focus_lines:
            m = req_focus_line_re.match(req_focus_line)
            if m:
                uid = str(m.group(1))
                pid = str(m.group(2))
                client_id = m.group(3)
                client_dict[client_id] = (uid, pid)
        focus_lines = self.shell_grep("dumpsys audio", "source:").splitlines()
        focus_line_re = re.compile(".* pack: (.*) -- client: (.*) -- gain: (.*) -- flags.* loss: (.*) -- notified.*")
        focus_dict = {}
        for focus_line in focus_lines:
            m = focus_line_re.match(focus_line)
            if m:
                (uid, pid) = client_dict[m.group(2)]
                focus_dict[(uid, pid)] = (m.group(3), m.group(4))
        uid_ = self.get_uid()
        audio_status = ''
        for (uid, pid), status in audio_status_dict.items():
            if uid != uid_:
                continue
            if status == 'paused':
                if (uid, pid) not in focus_dict:
                    audio_status = 'PAUSE'
                    continue
                if focus_dict[(uid, pid)][1] == 'LOSS_TRANSIENT':
                    audio_status = 'PAUSE*'
                else:
                    audio_status = 'PAUSE'
            if status == 'stopped' or status == 'idle':
                audio_status = 'STOP'
            if status == 'started':
                if (uid, pid) not in focus_dict:
                    if started_count > 1:
                        audio_status = 'START*'
                    else:
                        audio_status = 'START'
                    continue
                if focus_dict[(uid, pid)][1] == 'LOSS_TRANSIENT_CAN_DUCK':
                    audio_status = 'DUCK'
                else:
                    audio_status = 'START'
        return audio_status

    def get_camera_status(self):
        pass

    def get_micro_status(self, bundle):
        mic_infos = self.shell_grep("dumpsys audio", "src:").splitlines()
        status = ''
        silenced = ''
        for mic_info in mic_infos:
            mic_re = re.compile(f".*rec (.*) riid.*src:(.*) pack:{bundle}.*")
            match = mic_re.match(mic_info)
            if match:
                status = match.group(1)
                silenced = match.group(2)
        if status in ['stop', 'release'] or 'not' not in silenced:
            return 'stop'
        return 'start'


    def get_keyboard_status(self):
        pass
