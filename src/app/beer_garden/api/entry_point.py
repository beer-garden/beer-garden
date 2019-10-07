# -*- coding: utf-8 -*-
import beer_garden.config


class EntryPoint(object):
    def __init__(self):
        self.enabled = False

    def start(self, **kwargs):
        pass

    def stop(self, timeout=None):
        pass


class ProcessEntryPoint(EntryPoint):
    def __init__(self, name, target):
        super().__init__()

        self._name = name
        self._target = target
        self._process = None

    def start(self, **kwargs):
        context = kwargs.get("context")
        log_queue = kwargs.get("log_queue")
        process_name = f"BGEntryPoint-{self._name}"

        self._process = context.Process(
            target=self._target,
            args=(beer_garden.config.get(), log_queue),
            name=process_name,
            daemon=True,
        )
        self._process.start()

    def stop(self, timeout=None):
        # TODO - Should we start with INT?
        self._process.terminate()

        self._process.join(timeout=timeout)
        if self._process.exitcode is None:
            self.logger.warning(
                f"Process {self._process.name} is STILL running - sending SIGKILL"
            )
            self._process.kill()
