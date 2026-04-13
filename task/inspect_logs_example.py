from inspect_ai.log import list_eval_logs, read_eval_log

"""
This script provides a template of how to extract the messages from log files.
"""

# search for all logs
logs = list_eval_logs()

# read the first log in the list
log = read_eval_log(logs[0].name)

# get the first sample from the log
assert log.samples is not None
first_sample = log.samples[0]
messages_first_sample = first_sample.messages
print("Messages from the first sample:")
print(messages_first_sample)
