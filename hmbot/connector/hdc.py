from .connector import Connector
from ..exception import DeviceError, HDCError
from ..proto import ResourceType
from loguru import logger
import subprocess, re

try:
    from shlex import quote  # Python 3
except ImportError:
    from pipes import quote  # Python 2


class HDC(Connector):
    def __init__(self, device=None):
        if device is None and len(HDC.devices()) > 0:
            self.serial = HDC.devices()[0]
        from ..device import Device
        if isinstance(device, Device):
            self.serial = device.serial
        else:
            raise DeviceError
        self.cmd_prefix = ['hdc', "-t", device.serial]

    def run_cmd(self, extra_args):
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if not isinstance(extra_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise HDCError(msg)

        args = [] + self.cmd_prefix
        args += extra_args

        logger.debug('command: %s' % args)
        r = subprocess.check_output(args).strip()
        if not isinstance(r, str):
            r = r.decode()
        logger.debug('return: %s' % r)
        return r

    def shell(self, extra_args):
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if not isinstance(extra_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise HDCError(msg)
        extra_args = ['shell'] + extra_args
        return self.run_cmd(extra_args)

    def _hidumper(self, ability, extra_args):
        if isinstance(extra_args, str):
            extra_args = [extra_args]
        else:
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise HDCError(msg)
        extra_args = ['hidumper', '-s', ability, '-a'] + extra_args
        return self.shell(extra_args)

    def shell_grep(self, extra_args, grep_args):
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        if isinstance(grep_args, str):
            grep_args = grep_args.split()
        if not isinstance(extra_args, list) or not isinstance(grep_args, list):
            msg = "invalid arguments: %s\nshould be str, %s given" % (extra_args, type(extra_args))
            logger.warning(msg)
            raise HDCError(msg)

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
        missions = self._hidumper(ability='AbilityManagerService', extra_args='-l')
        missions = missions.split('}')
        infos_re = re.compile('.*app name \[(.*)\].*main name \[(.*)\].*bundle name \[(.*)\].*ability type.*',
                              flags=re.DOTALL)
        for mission in missions:
            if 'state #FOREGROUND  start time' in mission and 'app state #FOREGROUND' in mission:
                match = infos_re.match(mission)
                if match:
                    return {'app': match.groups()[0],
                            'ability': match.groups()[1],
                            'bundle': match.groups()[2]}

    def devices(cls):
        args = ['hdc', 'list', 'targets']
        logger.debug('command: %s' % args)
        r = subprocess.check_output(args).strip()
        if not isinstance(r, str):
            r = r.decode()
        logger.debug('return: %s' % r)
        return r.splitlines()

    def get_uid(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')
        ps_info = self.shell_grep("ps -ef", bundle).split()
        if len(ps_info) > 2:
            return ps_info[0]

    def get_pid(self, bundle=None):
        if not bundle:
            bundle = self.current_ability().get('bundle')
        ps_info = self.shell_grep("ps -ef", bundle).split()
        if len(ps_info) > 2:
            return ps_info[1]

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
        uid = self.get_uid(bundle)
        pid = self.get_pid(bundle)

        session_id_infos = self.shell_grep("hidumper -s AudioDistributed", "sessionId").splitlines()
        session_id = 0
        for session_id_info in session_id_infos:
            session_id_info = session_id_info.strip()
            session_id_re = re.compile(f'.*sessionId: (\d+).*appUid: {uid}.*appPid: {pid}.*')
            match = session_id_re.match(session_id_info)
            if match:
                session_id = match.group(1)

        stream_id_infos = self.shell_grep("hidumper -s AudioDistributed", "Stream").splitlines()
        stream_id_list = []
        for stream_id_info in stream_id_infos:
            stream_id_re = re.compile('.*Stream Id: (\d+).*')
            match = stream_id_re.match(stream_id_info)
            if match:
                stream_id = match.groups()[0]
                stream_id_list.append(stream_id)

        status_infos = self.shell_grep("hidumper -s AudioDistributed", "Status").splitlines()
        status_list = []
        for status_info in status_infos:
            status_info = status_info.strip()
            status_re = re.compile('.*Status:(.*)')
            match = status_re.match(status_info)
            if match:
                status = match.groups()[0]
                status_list.append(status)
        status = ''
        for index, stream_id in enumerate(stream_id_list):
            if stream_id == session_id:
                status = status_list[index]
        if status in ['RUNNING']:
            return 'START'
        if 'STOPPED' in status:
            return 'STOP'
        return

    def get_camera_status(self):
        pass

    def get_micro_status(self, bundle):
        pass

    def get_keyboard_status(self):
        pass
