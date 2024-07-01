import json
import os
from time import localtime, strftime
from typing import Any

from langchain.schema.messages import BaseMessage

from kai.models.kai_config import KaiConfig


def enabled_check(func):
    def wrapper(obj, *args, **kwargs):
        if obj.enabled:
            return func(obj, *args, **kwargs)
        else:
            # Perform as a noop (do nothing)
            pass

    return wrapper


class Trace:
    """Captures information to aid debugging and prompt tweaking

    This class is instantiated for a given request, so all of the data/actions
    are considered local to that single request

    Data will be stored to disk in the format of:
        {top_trace_dir}/{model_id}/{application_name}/
            {src_file_name}/{batch_mode}/{batch_id}/{retry_attempt_counter}/

    """

    def __init__(
        self,
        config: KaiConfig,
        model_id: str,
        batch_mode: str,
        application_name: str,
        file_name: str,
    ):
        super()
        self.config = config
        self.enabled = config.trace_enabled
        self.model_id = model_id
        self.batch_mode = batch_mode
        self.application_name = application_name
        self.file_name = file_name
        self.time_start = -1
        self.time_end = -1

        # TODO:  Specify trace directory in config
        self.top_trace_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../logs/trace"
        )

        self.trace_dir = os.path.join(
            self.top_trace_dir, model_id, application_name, file_name, batch_mode
        )

    @enabled_check
    def start(self, start: float):
        self.time_start = start
        self.trace_dir = os.path.join(self.trace_dir, f"{self.time_start}")

    # Capture timing info of the request completing
    @enabled_check
    def end(self, end: float):
        self.time_end = end
        end_file_path = os.path.join(self.trace_dir, "timing")
        os.makedirs(os.path.dirname(end_file_path), exist_ok=True)
        with open(end_file_path, "w") as f:
            local_start = strftime("%Y-%m-%d %H:%M:%S", localtime(self.time_start))
            local_end = strftime("%Y-%m-%d %H:%M:%S", localtime(self.time_end))
            entry = f"start: {local_start}\nend: {local_end}\nduration: {self.time_end - self.time_start} seconds"
            f.write(entry)

    @enabled_check
    def params(self, params: Any):
        params_file_path = os.path.join(self.trace_dir, "params.json")
        os.makedirs(os.path.dirname(params_file_path), exist_ok=True)
        with open(params_file_path, "w") as f:
            # f.write(json.dumps(params, indent=4))
            f.write(params.json())

    ##############
    # Assumptions:
    #   - We will be grouping incidents in various 'batching' strategies, this may lead to
    #     multiple LLM calls for a single file as we chunk the work into smaller pieces based on the incidents
    #     We use 'current_batch_count' to distinguish these potential different batching calls
    #
    #   - We will retry a failed LLM call multiple times, these failures may be due to LLM server side issues
    #     or parsing related issues if we received incompleted/unexpected data
    #     We use 'retry_count' to distinguish these potential different retry attempts
    ##############

    @enabled_check
    def prompt(self, current_batch_count: int, prompt: str, pb_vars: dict):
        prompt_file_path = os.path.join(
            self.trace_dir, f"{current_batch_count}", "prompt"
        )
        os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)
        with open(prompt_file_path, "w") as f:
            f.write(prompt)

        pb_vars_file_path = os.path.join(
            self.trace_dir, f"{current_batch_count}", "prompt_vars.json"
        )
        os.makedirs(os.path.dirname(pb_vars_file_path), exist_ok=True)
        with open(pb_vars_file_path, "w") as f:
            # Filter 'model_provider' from being written to disk.
            # This is a crude approach to make the pb_vars json serializable without
            # implementing anything custom for ModelProvider.  We will make a shallow
            # copy and remove the key for 'model_provider'
            #
            # TODO:  Capture the args associated with the model_provider, things like temperature
            #
            data = pb_vars.copy()
            del data["model_provider"]
            f.write(json.dumps(data, indent=4))

    @enabled_check
    def llm_result(
        self, current_batch_count: int, retry_count: int, result: BaseMessage
    ):
        result_file_path = os.path.join(
            self.trace_dir, f"{current_batch_count}", f"{retry_count}", "llm_result"
        )
        os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
        with open(result_file_path, "w") as f:
            f.write(result.pretty_repr())

    @enabled_check
    def exception(
        self,
        current_batch_count: int,
        retry_count: int,
        exception: Exception,
        traceback: str,
    ):
        # We may call this trace of exception data prior to entering the batched incident / llm_retry loop
        # therefore we will adjust the dir/file path as needed
        exception_file_path_dir = self.trace_dir
        if current_batch_count >= 0:
            exception_file_path_dir = os.path.join(
                exception_file_path_dir, f"{current_batch_count}"
            )
        if retry_count >= 0:
            exception_file_path_dir = os.path.join(
                exception_file_path_dir, f"{retry_count}"
            )

        exception_file_path = os.path.join(exception_file_path_dir, "exception")
        os.makedirs(os.path.dirname(exception_file_path), exist_ok=True)
        with open(exception_file_path, "w") as f:
            f.write(f"{exception}")

        traceback_file_path = os.path.join(exception_file_path_dir, "traceback")
        os.makedirs(os.path.dirname(traceback_file_path), exist_ok=True)
        with open(traceback_file_path, "w") as f:
            f.write(traceback)
