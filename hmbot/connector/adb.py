from .connector import Connector
from ..exception import DeviceError, ADBError
from ..proto import ResourceType, AudioStatus, MicroStatus
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

    def get_uid(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')
        process_lines = self.shell_grep("ps", bundle).splitlines()
        if len(process_lines) > 0:
            usr_name = process_lines[0].split()[0]
            uid = str(int(usr_name.split('_a')[1]) + 10000)
            return uid
        else:
            return

    def get_resource_status(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')
        return {
            ResourceType.AUDIO: self.get_audio_status(bundle),
            ResourceType.CAMERA: self.get_camera_status(),
            ResourceType.MICRO: self.get_micro_status(bundle),
            ResourceType.KEYBOARD: self.get_keyboard_status()
        }

    def get_audio_status(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')

        audio_lines = self.shell_grep("dumpsys audio", "AudioPlaybackConfiguration").splitlines()
        audio_line_re = re.compile(".*u/pid:(.*)/(.*) .*state:(.*) attr.*")
        audio_status_dict = {}
        for audio_line in audio_lines:
            m = audio_line_re.match(audio_line)
            if m:
                uid = m.group(1)
                pid = m.group(2)
                status = m.group(3)
                if (uid, pid) not in audio_status_dict:
                    audio_status_dict[(uid, pid)] = status
                elif status == 'started':
                    audio_status_dict[(uid, pid)] = status

        ps_lines = self.shell_grep("ps", bundle).splitlines()
        ps_line_re = re.compile(r'^\S+\s+(\d+)')
        pid_list = []
        for ps_line in ps_lines:
            m = ps_line_re.match(ps_line)
            if m:
                pid = m.group(1)
                pid_list.append(pid)

        uid_ = self.get_uid(bundle)
        for (uid, pid), status in audio_status_dict.items():
            if uid != uid_:
                continue
            if pid in pid_list and status == 'started':
                return AudioStatus.START
        return AudioStatus.STOP

    def get_camera_status(self):
        pass

    def get_micro_status(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')

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
            return MicroStatus.STOP
        return MicroStatus.START


    def get_keyboard_status(self):
        pass
